from flask import Flask, render_template, request
import os
import requests
import uuid
import time
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

API_URL = os.getenv("CLOVA_API_URL")     
SECRET_KEY = os.getenv("CLOVA_API_KEY") 
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

    # 사진에서 텍스트 추출
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
            full_text = ' '.join(extracted_texts)

            system_prompt = (
                "한 끼 섭취 칼로리 상한선을 넘는 경우 경고.\n"
                "식품 첨가물 3가지 이상 포함되어 있는 경우 경고. \n"
                "한 끼 섭취 칼로리 상한선을 넘지 않습니다.\n"
                "식품 첨가물이 3가지 이상 포함되어 있습니다.\" 처럼 간략하게 메세지를 출력해야 함. \n"
                "비만, 고혈압, 당뇨의 한 끼 섭취량이 넘는 영양소가 있다면 경고\n"
                "경고를 1개 이상 받은 경우, 건강한 식단 3개 추천해주기. '\n\n건강한 식단 3가지 추천:'으로 시작해서 1, 2, 3번으로 각 식단에 번호 매기기\n"
                "이외의 다른 말은 출력하지 않기."
            )

            gpt_response = client.chat.completions.create(
                model="gpt-4",
                temperature=1,
                top_p=1,
                max_tokens=2048,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_text}
                ]
            )

            gpt_text = gpt_response.choices[0].message.content
            
            return render_template('results.html', gpt_result=gpt_text)

        except Exception as e:
            return f"처리 중 오류 발생: {str(e)}", 500


if __name__ == '__main__':
    app.run(debug=True)
