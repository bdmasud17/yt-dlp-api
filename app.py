import os
from flask import Flask, request, jsonify, send_file, g
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "yt-dlp API is fully working!"})


# ১. ভিডিওর সমস্ত ডিটেইলস (Title, Desc, Thumbnail) পাওয়ার জন্য
@app.route('/get-video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "URL parameter is missing"}), 400

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # ffmpeg থাকায় এখন সরাসরি বেস্ট কোয়ালিটি কাজ করবে
        'quiet': True,
        'no_warnings': True,
    }

    url_lower = video_url.lower()
    if 'instagram.com' in url_lower or 'youtube.com' in url_lower or 'youtu.be' in url_lower or 'x.com' in url_lower or 'twitter.com' in url_lower:
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify(info)
          
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
