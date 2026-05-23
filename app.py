import os
from flask import Flask, request, jsonify, send_file
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
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify({
                "status": "success",
                "title": info.get('title', 'Tiktok Video'),
                "description": info.get('description', ''),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration', 0),
                "view_count": info.get('view_count', 0),
                "like_count": info.get('like_count', 0),
                "uploader": info.get('uploader', '')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ২. রেন্ডার সার্ভার নিজেই ফাইল ডাউনলোড করে সরাসরি ইউজারের ব্রাউজারে পুশ করবে
@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL parameter is missing", 400

    # /tmp/ ফোল্ডারে ফাইলটি সাময়িকভাবে সেভ হবে (রেন্ডার ফ্রি টায়ারে এটি অনুমতি দেয়)
    output_template = '/tmp/%(id)s.%(ext)s'
    
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True) # রেন্ডার সার্ভারে ফাইল ডাউনলোড হবে
            filename = ydl.prepare_filename(info)
            title = info.get('title', 'video')
            safe_title = "".join([c if c.isalnum() else "_" for c in title]) + ".mp4"

        # রেন্ডার সার্ভার থেকে ফাইলটি সরাসরি ইউজারের পিসিতে ডাউনলোড হিসেবে পাঠিয়ে দেওয়া
        return send_file(filename, as_attachment=True, download_name=safe_title)

    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
