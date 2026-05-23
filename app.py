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

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            return jsonify({
                "status": "success",
                "title": info.get('title', ''),
                "description": info.get('description', ''),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "view_count": info.get('view_count', 0),
                "like_count": info.get('like_count', 0),
                "comment_count": info.get('comment_count', 0),
                "uploader": info.get('uploader', '')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL parameter is missing", 400

    ydl_opts = {'format': 'best', 'quiet': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            real_url = info.get('url')
            title = info.get('title', 'video')
            safe_title = "".join([c if c.isalnum() else "_" for c in title])

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        req = requests.get(real_url, headers=headers, stream=True)
        
        def generate():
            for chunk in req.iter_content(chunk_size=1024*1024):
                if chunk:
                    yield chunk

        response = Response(generate(), content_type=req.headers.get('Content-Type'))
        response.headers['Content-Disposition'] = f'attachment; filename={safe_title}.mp4'
        return response

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
