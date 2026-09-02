import os
from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)


@app.route('/')
def home():
  return jsonify(
      {"status": "running", "message": "yt-dlp API is fully working!"}
  )


@app.route('/get-video', methods=['GET'])
def get_video():
  video_url = request.args.get('url')
  if not video_url:
    return jsonify({"status": "error", "message": "URL parameter is missing"}), (
        400
    )

  # TikTok বাইপাস করার জন্য অপটিমাইজড ydl_opts
  ydl_opts = {
      'quiet': True,
      'no_warnings': True,
      'format': 'best',
      # টিকটকের জন্য রেগুলার ব্রাউজার হেডার
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

  url_lower = video_url.lower()

  # কুকি ফাইল থাকলে তা ব্যবহারের অপশন
  if any(
      domain in url_lower
      for domain in [
          'instagram.com',
          'youtube.com',
          'youtu.be',
          'x.com',
          'tiktok.com',
      ]
  ):
    if os.path.exists('cookies.txt'):
      ydl_opts['cookiefile'] = 'cookies.txt'

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(video_url, download=False)
      # সংক্ষেপে মূল দরকারি তথ্যগুলো পাঠানোর জন্য
      return jsonify(info)

  except Exception as e:
    # এরর মেসেজ যেন খালি না থাকে তার জন্য fallback মেসেজ
    error_msg = str(e) if str(e) else repr(e)
    return jsonify({'status': 'error', 'message': error_msg}), 500


if __name__ == '__main__':
  app.run(debug=True)
