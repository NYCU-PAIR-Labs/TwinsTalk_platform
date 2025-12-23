from flask import Flask, request, jsonify, render_template, Response, send_file
from datetime import datetime
import os
import uuid
from analyze import analyze_pose, analyze_object_detection

# 路徑資料夾設定
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
RESULT_FOLDER = 'results'

# 確保資料夾存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# 建立 Flask app
app = Flask(__name__, template_folder='templates')

# 首頁（影片清單）
@app.route('/')
def index():
    videos = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.mp4')]
    videos.sort()  # 可選：按時間字串排序
    return render_template('index.html', videos=videos)

# 播放頁面
@app.route('/video/<filename>')
def play_video(filename):
    return render_template('player.html', filename=filename)

# 回傳影片檔案（支援 Range）
@app.route('/stream/<path:filename>')
def stream_video(filename):
    filepath = os.path.join(OUTPUT_FOLDER, filename)

    if not os.path.exists(filepath):
        return "影片不存在", 404

    file_size = os.path.getsize(filepath)
    range_header = request.headers.get('Range', None)

    if not range_header:
        return send_file(filepath, mimetype='video/mp4')

    byte1, byte2 = 0, None
    try:
        match = range_header.strip().split('=')[1].split('-')
        if match[0]:
            byte1 = int(match[0])
        if len(match) > 1 and match[1]:
            byte2 = int(match[1])
        else:
            byte2 = file_size - 1
    except:
        return send_file(filepath, mimetype='video/mp4')

    length = byte2 - byte1 + 1

    with open(filepath, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    resp = Response(data, status=206, mimetype='video/mp4')
    resp.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
    resp.headers.add('Accept-Ranges', 'bytes')
    resp.headers.add('Content-Length', str(length))
    return resp

# 上傳影片與分析
@app.route('/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': '請上傳影片檔案（video 欄位）'}), 400

    video_file = request.files['video']
    task = request.form.get('task', 'pose')  # 預設為 pose

    # 產生時間字串做為檔名，例如：20250703_1430
    now_str = datetime.now().strftime('%Y%m%d_%H%M')

    uploaded_video_filename    = f"{now_str}.mp4"
    json_filename              = f"{now_str}_{task}.json"
    annotated_video_filename   = f"{now_str}_{task}_annotated.mp4"

    uploaded_path      = os.path.join(UPLOAD_FOLDER, uploaded_video_filename)
    json_path          = os.path.join(RESULT_FOLDER, json_filename)
    output_video_path  = os.path.join(OUTPUT_FOLDER, annotated_video_filename)

    # 儲存上傳影片
    video_file.save(uploaded_path)

    try:
        if task == 'pose':
            analyze_pose(uploaded_path, json_path, output_video_path)
        elif task == 'object':
            analyze_object_detection(uploaded_path, json_path, output_video_path)
        else:
            return jsonify({'error': f'不支援的任務類型：{task}'}), 400
    except Exception as e:
        return jsonify({'error': f'分析失敗：{str(e)}'}), 500

    return jsonify({
        'message': '分析成功',
        'video': annotated_video_filename,
        'json': json_filename,
        'preview_url': f"/video/{annotated_video_filename}"
    })

# 啟動伺服器
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)