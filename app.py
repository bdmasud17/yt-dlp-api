import os
import requests
from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)


@app.route('/')
def home():
  return jsonify(
      {"status": "running", "message": "yt-dlp API is fully working!"}
  )


def fetch_from_fb_api(video_url):
  """Facebook ভিডিওর জন্য fb-video-downloader.com API ব্যবহার করা হয়।"""
  api_url = 'https://fb-video-downloader.com/api/video/'
  headers = {
      'Content-Type': 'application/json',
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          ' (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
      ),
      'Accept': 'application/json, text/plain, */*',
      'Origin': 'https://fb-video-downloader.com',
      'Referer': 'https://fb-video-downloader.com/',
  }

  response = requests.post(
      api_url, json={'url': video_url}, headers=headers, timeout=25
  )
  response.raise_for_status()
  data = response.json()

  # রেসপন্স স্ট্রাকচার হ্যান্ডেল করা (data কী-এর ভিতরে থাকতে পারে)
  fb_data = data.get('data', data)

  # HD → SD → url → links[] ক্রমে ডাউনলোড লিংক খোঁজা
  raw_download_link = ''
  if isinstance(fb_data, dict):
    if fb_data.get('hd'):
      raw_download_link = fb_data['hd']
    elif fb_data.get('sd'):
      raw_download_link = fb_data['sd']
    elif fb_data.get('url'):
      raw_download_link = fb_data['url']
    elif isinstance(fb_data.get('links'), list) and fb_data['links']:
      hd_link = next(
          (l for l in fb_data['links'] if l.get('quality') == 'hd' or l.get('label') == 'HD'),
          None,
      )
      sd_link = next(
          (l for l in fb_data['links'] if l.get('quality') == 'sd' or l.get('label') == 'SD'),
          None,
      )
      raw_download_link = (
          (hd_link or {}).get('url')
          or (sd_link or {}).get('url')
          or fb_data['links'][0].get('url', '')
      )

  if not raw_download_link:
    raise ValueError('Facebook API থেকে কোনো ডাউনলোড লিংক পাওয়া যায়নি।')

  # yt-dlp এর আউটপুট ফরম্যাটের সাথে মিলিয়ে ডিকশনারি রিটার্ন
  return {
      'status': 'success',
      'title': fb_data.get('title') or fb_data.get('description') or 'facebook_video',
      'thumbnail': fb_data.get('thumbnail') or fb_data.get('thumb') or '',
      'duration': fb_data.get('duration'),
      'view_count': fb_data.get('view_count', 0),
      'like_count': fb_data.get('like_count', 0),
      'comment_count': fb_data.get('comment_count', 0),
      'uploader': fb_data.get('author') or fb_data.get('uploader') or 'Unknown',
      'url': raw_download_link,
  }


@app.route('/get-video', methods=['GET'])
def get_video():
  video_url = request.args.get('url')
  if not video_url:
    return jsonify({"status": "error", "message": "URL parameter is missing"}), (
        400
    )

  url_lower = video_url.lower()

  # 🎯 Facebook হলে fb-video-downloader.com API ব্যবহার
  is_facebook = any(
      domain in url_lower
      for domain in ['facebook.com', 'fb.watch', 'fb.com']
  )

  if is_facebook:
    try:
      info = fetch_from_fb_api(video_url)
      return jsonify(info)
    except Exception as e:
      error_msg = str(e) if str(e) else repr(e)
      # Facebook API ফেইল করলে yt-dlp-তে ফলব্যাক
      print(f'FB API failed, falling back to yt-dlp: {error_msg}')

  # TikTok বাইপাস করার জন্য অপটিমাইজড ydl_opts
  ydl_opts = {
      'quiet': True,
      'no_warnings': True,
      'format': 'best',
      'http_headers': {
          'User-Agent': (
              'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              ' (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
          ),
          'Accept': '*/*',
          'Accept-Language': 'en-US,en;q=0.9',
          'Referer': 'https://www.tiktok.com/',
      },
  }

  # কুকি ফাইল থাকলে তা ব্যবহারের অপশন
  if any(
      domain in url_lower
      for domain in [
          'instagram.com',
          'youtube.com',
          'youtu.be',
          'x.com',
          'facebook.com',
          'tiktok.com',
      ]
  ):
    if os.path.exists('cookies.txt'):
      ydl_opts['cookiefile'] = 'cookies.txt'

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      return jsonify(info)

  except Exception as e:
    error_msg = str(e) if str(e) else repr(e)
    return jsonify({'status': 'error', 'message': error_msg}), 500


if __name__ == '__main__':
  app.run(debug=True)
