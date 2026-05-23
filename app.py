import os
from flask import Flask, request, jsonify, Response
import yt_dlp
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "yt-dlp API is fully working!"})

@app.route('/get-video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "URL parameter is missing"}), 400

    # টিকটক ও ফেসবুকের সিকিউরিটি বাইপাস করার জন্য বিশেষ অপশন
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # অনেক সময় টিকটকের ডিরেক্ট লিঙ্ক 'url' কি-তে না থেকে 'formats'-এর ভেতরে থাকে
            download_url = info.get('url')
            if not download_url and info.get('formats'):
                # সবথেকে ভালো ফরম্যাটের ভিডিও লিঙ্কটি খুঁজে নেওয়া
                valid_formats = [f for f in info['formats'] if f.get('url')]
                if valid_formats:
                    download_url = valid_formats[-1]['url'] # একদম শেষেরটা সাধারণত বেস্ট কোয়ালিটি হয়

            return jsonify({
                "status": "success",
                "title": info.get('title', 'Tiktok Video'),
                "description": info.get('description', ''),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "view_count": info.get('view_count', 0),
                "like_count": info.get('like_count', 0),
                "comment_count": info.get('comment_count', 0),
                "uploader": info.get('uploader', ''),
                "download_url": download_url  # পিএইচপিকে ডিরেক্ট প্রক্সি করার জন্য লিঙ্কটি দেওয়া হলো
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# এই রুটটি পিএইচপি থেকে পাঠানো ডিরেক্ট টিকটক সোর্স ফাইলকে ব্রাউজারে স্ট্রিম করবে
@app.route('/stream-file', methods=['GET'])
def stream_file():
    real_url = request.args.get('real_url')
    title = request.args.get('title', 'video')
    
    if not real_url:
        return "Real video URL is missing", 400

    safe_title = "".join([c if c.isalnum() else "_" for c in title])

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.tiktok.com/'
    }

    try:
        req = requests.get(real_url, headers=headers, stream=True, timeout=15)
        
        def generate():
            for chunk in req.iter_content(chunk_size=1024*512): # 512KB chunks
                if chunk:
                    yield chunk

        response = Response(generate(), content_type=req.headers.get('Content-Type', 'video/mp4'))
        response.headers['Content-Disposition'] = f'attachment; filename={safe_title}.mp4'
        return response
    except Exception as e:
        return f"Streaming Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
