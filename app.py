from flask import Flask, render_template, request
import os
import requests
import uuid
import time
import json
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

API_URL = os.getenv("CLOVA_API_URL")     
SECRET_KEY = os.getenv("CLOVA_API_KEY") 
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    photo = request.files.get('photo')

    if not photo:
        return '파일이 업로드되지 않았습니다.', 400

    filename = photo.filename
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    photo.save(save_path)

    request_json = {
        'images': [
            {
                'format': filename.split('.')[-1],
                'name': 'demo'
            }
        ],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }

    payload = {
        'message': json.dumps(request_json).encode('UTF-8')
    }

    files = [
        ('file', open(save_path, 'rb'))
    ]

    headers = {
        'X-OCR-SECRET': SECRET_KEY
    }

    response = requests.post(API_URL, headers=headers, data=payload, files=files)

    if response.status_code == 200:
        try:
            result = response.json()
            fields = result['images'][0].get('fields', [])
            extracted_texts = [f['inferText'] for f in fields]
            return f"추출된 텍스트: {' / '.join(extracted_texts)}"
        except Exception as e:
            return f"OCR 파싱 중 오류 발생: {str(e)}", 500
    else:
        return f"OCR 요청 실패 - 상태 코드: {response.status_code}<br>응답: {response.text}", 400

if __name__ == '__main__':
    app.run(debug=True)
