import requests
import sys

# 設定影片上傳路徑與任務類型（pose / object）
file_path = 'sample.mp4'
task_type = 'object'  # 預設為 pose；可改為 'object'

if len(sys.argv) > 1:
    task_type = sys.argv[1]  # 從命令列參數接收任務類型

with open(file_path, 'rb') as f:
    response = requests.post(
        'http://localhost:5000/upload',
        files={'video': f},
        data={'task': task_type}
    )

print('HTTP 狀態碼:', response.status_code)
print('伺服器回應:')
try:
    print(response.json())
except Exception as e:
    print('⚠️ 回應無法解析為 JSON：', e)
    print('Raw:', response.text)