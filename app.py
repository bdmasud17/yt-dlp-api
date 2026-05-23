import os
from flask import Flask, request, jsonify, send_file
import yt_dlp

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "running", "message": "yt-dlp API is fully working!"})

@app.route('/get-video', methods=['GET'])
def get_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "URL parameter is missing"}), 400

    # ফেসবুক ও টিকটকের বেস্ট ফরম্যাট ডিটেইলস চেনার জন্য
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
                "uploader": info.get('uploader', '')
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/download', methods=['GET'])
def download_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL parameter is missing", 400

    output_template = '/tmp/%(id)s.%(ext)s'
    
    # এখানে আমরা ভিডিও এবং অডিও মার্জ করার নির্দেশ দিচ্ছি
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # এটি ভিডিও ও অডিও দুটিই একসাথে নামাবে
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4', # অডিও-ভিডিও জোড়া লাগিয়ে ফাইনাল mp4 আউটপুট দেবে
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            
            # অনেক সময় মার্জ করার পর এক্সটেনশন mkv বা অন্য কিছু হতে পারে, তাই এক্সটেনশন নিশ্চিত করা
            if not os.path.exists(filename):
                filename = filename.rsplit('.', 1)[0] + '.mp4'

            title = info.get('title', 'video')
            safe_title = "".join([c if c.isalnum() else "_" for c in title]) + ".mp4"

        # ফাইলটি ব্রাউজারে পাঠানোর পর Render থেকে ক্লিন করার জন্য অটো-ডিলিট ট্রিক
        @app.after_request
        def delete_file(response):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                pass
            return response

        return send_file(filename, as_attachment=True, download_name=safe_title)

    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
