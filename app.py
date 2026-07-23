import os
from flask import Flask, request, jsonify, send_file, g
import yt_dlp

app = Flask(__name__)

# সাপোর্ট করা ওয়েবসাইট ডোমেইনের তালিকা
COOKIES_DOMAINS = ['instagram.com', 'youtube.com', 'youtu.be', 'x.com', 'twitter.com']

def should_use_cookies(url):
    """লিংকটিতে কুকিজ ব্যবহার করা লাগবে কিনা তা চেক করার ফাংশন"""
    url_lower = url.lower()
    return any(domain in url_lower for domain in COOKIES_DOMAINS)


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

    # কুকিজ প্রয়োজন হলে যোগ করবে এবং cookies.txt ফাইলটি সার্ভারে আছে কিনা চেক করবে
    if should_use_cookies(video_url) and os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return jsonify(info)
            
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

    # কুকিজ প্রয়োজন হলে যোগ করবে এবং cookies.txt ফাইলটি সার্ভারে আছে কিনা চেক করবে
    if should_use_cookies(video_url) and os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            # merge_output_format এর কারণে ফাইলটি mp4 হতে পারে, তাই তা হ্যান্ডেল করা
            if not os.path.exists(filename):
                filename = filename.rsplit('.', 1)[0] + '.mp4'

            title = info.get('title', 'video')
            safe_title = "".join([c if c.isalnum() else "_" for c in title]) + ".mp4"

            # ফ্ল্যাস্কের 'g' অবজেক্টে ফাইলের পাথ রাখা যেন ডাউনলোডের পর ফাইল ডিলিট করা যায়
            g.cleanup_file = filename

            return send_file(filename, as_attachment=True, download_name=safe_title)

    except Exception as e:
        return f"Download Error: {str(e)}", 500


# ডাউনলোড শেষ হওয়ার পর /tmp ফোল্ডার থেকে ফাইলটি মুছে ফেলার নিয়ম
@app.teardown_request
def teardown_request(exception=None):
    filename = g.get('cleanup_file', None)
    if filename and os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception:
            pass


if __name__ == '__main__':
    app.run(debug=True)
