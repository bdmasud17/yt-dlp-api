import os
from flask import Flask, jsonify, request

import yt_dlp

app = Flask(__name__)


@app.route('/')
def home():
  return jsonify(
      {"status": "running", "message": "yt-dlp API is fully working!"}
  )


# ১. ভিডিওর সমস্ত ডিটেইলস (Title, Desc, Thumbnail, Direct URL) পাওয়ার জন্য
@app.route('/get-video', methods=['GET'])
def get_video():
  video_url = request.args.get('url')
  if not video_url:
    return jsonify({"status": "error", "message": "URL parameter is missing"}), (
        400
    )

  # টিকটক সহ অন্যান্য সোশ্যাল মিডিয়ার জন্য অপটিমাইজড অপশন
  ydl_opts = {
      'format': 'bestvideo+bestaudio/best',
      'quiet': True,
      'no_warnings': True,
      # আসল Chrome ব্রাউজারের মতো আচরণ করানোর জন্য impersonate ব্যবহার:
      'impersonate': 'chrome',
      'extractor_args': {
          'tiktok': {
              'app_version': '34.0.0',
              'manifest_app_version': '34.0.0',
              'web_client_name': 'android',
          }
      },
      'http_headers': {
          'User-Agent': (
              'com.zhiliaoapp.musically/2023400000 (Linux; U; Android 13;'
              ' en_US; Pixel 7; Build/TQ3A.230901.001; Cronet/TTNetVersion:95e54eb8'
              ' 2023-08-16 QuicVersion:4d60e653 2023-08-14)'
          ),
          'Accept-Language': 'en-US,en;q=0.9',
      },
  }

  url_lower = video_url.lower()

  # নির্দিষ্ট সাইটগুলোর জন্য কুকি ফাইল যুক্ত করার চেক
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
      return jsonify(info)

  except Exception as e:
    return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
  app.run(debug=True)
