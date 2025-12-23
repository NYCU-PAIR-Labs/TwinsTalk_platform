import argparse
import os
import requests

def upload_video(file_path, mode='pose', host='localhost', port=5000):
    url = f'http://{host}:{port}/upload'

    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案: {file_path}")
        return

    with open(file_path, 'rb') as f:
        print(f"⬆️ 上傳影片: {file_path}")
        print(f"🎯 模式: {mode}")
        print(f"🌐 傳送至: {url}")

        try:
            response = requests.post(
                url,
                files={'video': f},
                data={'task': mode}
            )
        except requests.ConnectionError as e:
            print(f"⛔ 無法連線到伺服器: {e}")
            return

    print(f"\n🌐 HTTP 狀態碼: {response.status_code}")

    try:
        data = response.json()
        print("✅ 伺服器回傳結果:")
        for key, value in data.items():
            print(f"{key}: {value}")
    except ValueError:
        print("⚠️ 無法解析 JSON，伺服器回應如下：")
        print(response.text)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='上傳影片進行 AI 分析')
    parser.add_argument('--mode', '-m', choices=['pose', 'object'], default='pose', help='分析模式（pose 或 object）')
    parser.add_argument('--file', '-f', required=True, help='影片檔案路徑（e.g. uploads/sample.mp4）')
    parser.add_argument('--host', required=False, default='localhost', help='伺服器 IP 或主機名稱（預設：localhost）')
    parser.add_argument('--port', '-p', type=int, default=5000, help='伺服器通訊 port（預設：5000）')

    args = parser.parse_args()

    upload_video(
        file_path=args.file,
        mode=args.mode,
        host=args.host,
        port=args.port
    )