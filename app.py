import os
from flask import Flask, jsonify, request
import yt_dlp

app = Flask(__name__)

# প্রক্সি Render-এর Environment Variable থেকে আসবে (কোডে লিখো না)
PROXY_URL = os.environ.get("PROXY_URL", "ReEUR3ZzXcu0D9P:g7gjZGC56bO8dgr_country-CA_region-alberta_city-calgary_session-98968521_ttl-30@thehub.proxy-cheap.com:8080")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

FB_DOMAINS = ['facebook.com', 'fb.watch', 'fb.com']


@app.route('/')
def home():
    return jsonify({"status": "running", "message": "yt-dlp API is fully working!"})


@app.route('/get-video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "URL parameter is missing"}), 400

    url_lower = video_url.lower()
    is_fb = any(d in url_lower for d in FB_DOMAINS)

    headers = {'User-Agent': UA, 'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.9'}
    if 'tiktok.com' in url_lower:
        headers['Referer'] = 'https://www.tiktok.com/'

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'skip_download': True,
        'format': 'best',
        'socket_timeout': 30,
        'http_headers': headers,
    }

    if is_fb:
        # Facebook: শুধু এখানেই প্রক্সি
        if PROXY_URL:
            ydl_opts['proxy'] = PROXY_URL
    else:
        # অন্য সাইট: প্রক্সি ছাড়া, cookies থাকলে ব্যবহার
        if any(d in url_lower for d in ['instagram.com', 'youtube.com', 'youtu.be', 'x.com', 'tiktok.com']):
            if os.path.exists('cookies.txt'):
                ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify(ydl.sanitize_info(info))
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e) or repr(e)}), 500
