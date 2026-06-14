import os
from flask import Flask, request, jsonify, send_file, g
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "yt-dlp API is fully working!"})

# ১. ভিডিওর সমস্ত ডিটেইলস (Title, Desc, Thumbnail) পাওয়ার জন্য
@app.route('/get-video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "URL parameter is missing"}), 400

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "status": "success",
                "title": info.get('title', 'Social Video'),
                "description": info.get('description', ''),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "view_count": info.get('view_count', 0),
                "like_count": info.get('like_count', 0),
                "uploader": info.get('uploader', ''),
                "info": info;
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ২. ভিডিও ডাউনলোড রুট (সাউন্ড ফিক্স সহ)
@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL parameter is missing", 400

    output_template = '/tmp/%(id)s.%(ext)s'
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            if not os.path.exists(filename):
                filename = filename.rsplit('.', 1)[0] + '.mp4'

            title = info.get('title', 'video')
            safe_title = "".join([c if c.isalnum() else "_" for c in title]) + ".mp4"

        # ফ্ল্যাস্কের 'g' অবজেক্টে ফাইলের পাথটি রেখে দিচ্ছি যেন পরে ডিলিট করা যায়
        g.cleanup_file = filename

        return send_file(filename, as_attachment=True, download_name=safe_title)

    except Exception as e:
        return f"Download Error: {str(e)}", 500

# ডাউনলোড শেষ হওয়ার পর ফাইলটি রেন্ডার থেকে ক্লিন করার সঠিক নিয়ম
@app.teardown_request
def teardown_request(exception=None):
    filename = g.get('cleanup_file', None)
    if filename and os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception:
            pass
