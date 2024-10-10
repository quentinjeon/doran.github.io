from flask import Flask, render_template, request, jsonify
import os
import sqlite3
from datetime import datetime, timedelta
from youtubesearchpython import VideosSearch
import pafy
import speech_recognition as sr
import threading
import time

# Flask 애플리케이션 초기화
app = Flask(__name__)

# Pafy 백엔드를 yt-dlp로 설정
os.environ["PAFY_BACKEND"] = "yt-dlp"

# 데이터베이스 초기화 함수
def init_db():
    conn = sqlite3.connect('songs.db')  # songs.db 파일에 연결
    cursor = conn.cursor()
    # search_history 테이블이 없으면 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_title TEXT NOT NULL,
            search_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# 데이터베이스에 검색 기록 저장 함수
def save_to_db(song_title):
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO search_history (song_title) VALUES (?)', (song_title,))
    conn.commit()
    conn.close()
    print(f"'{song_title}'이(가) 데이터베이스에 저장되었습니다.")

# 유튜브에서 노래를 검색하고 관련 동영상 목록을 가져오는 함수
def search_related_videos(query, limit=5):
    print(f"'{query}'와 관련된 유튜브 동영상을 검색 중...")
    videos_search = VideosSearch(query, limit=limit)
    result = videos_search.result()["result"]

    if result:
        video_urls = [video["link"] for video in result]
        return video_urls
    else:
        print("관련된 유튜브 동영상을 찾을 수 없습니다.")
        return []

# 음성 인식을 통해 텍스트로 변환하는 함수
def recognize_speech():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        print("노래 제목과 가수명을 말하세요...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        print("인식 중...")
        text = recognizer.recognize_google(audio, language="ko-KR")
        print(f"인식된 텍스트: {text}")
        return text
    except sr.UnknownValueError:
        return "음성을 인식하지 못했습니다."
    except sr.RequestError as e:
        return f"API 요청 오류: {e}"

# 노래를 20분 동안 연속 재생하는 함수
def play_for_20_minutes(video_urls):
    start_time = datetime.now()
    current_index = 0

    while (datetime.now() - start_time) < timedelta(minutes=20):
        if current_index >= len(video_urls):
            current_index = 0  # 플레이리스트가 끝나면 처음으로 돌아가기

        video_url = video_urls[current_index]
        print(f"재생 중: {video_url}")

        # 유튜브 동영상 URL을 자동 재생하는 IFrame src URL로 변환
        video_embed_url = video_url.replace("watch?v=", "embed/") + "?autoplay=1"

        # 동영상 재생을 위해 iframe src 설정
        current_index += 1

        # 대기 시간 설정 (노래가 평균적으로 4분이라고 가정)
        time.sleep(240)  # 240초 = 4분

    print("20분 재생이 완료되었습니다.")

# 홈 페이지 라우트
@app.route('/')
def index():
    return render_template('index.html')

# 음성 인식 API 라우트
@app.route('/recognize', methods=['POST'])
def recognize():
    song_info = recognize_speech()
    if song_info:
        # 데이터베이스에 검색 기록 저장
        save_to_db(song_info)
        return jsonify({'song_info': song_info})
    else:
        return jsonify({'error': '음성 인식 실패'})

# 유튜브 검색 및 20분 연속 재생을 위한 라우트
@app.route('/play', methods=['POST'])
def play():
    data = request.get_json()
    song_info = data['song_info']

    # 유튜브에서 노래 검색 및 관련 동영상 가져오기
    video_urls = search_related_videos(song_info, limit=10)  # 관련 동영상 10개 가져오기

    if video_urls:
        # 20분 동안 연속 재생 (별도의 스레드에서 실행)
        threading.Thread(target=play_for_20_minutes, args=(video_urls,)).start()
        return jsonify({'video_urls': video_urls})
    else:
        return jsonify({'error': '유튜브에서 노래를 찾을 수 없습니다.'})

# 데이터베이스 검색 기록 조회 라우트
@app.route('/history', methods=['GET'])
def history():
    conn = sqlite3.connect('songs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM search_history ORDER BY search_time DESC')
    rows = cursor.fetchall()
    conn.close()
    return render_template('history.html', rows=rows)

if __name__ == '__main__':
    init_db()  # 서버 시작 시 데이터베이스 초기화
    app.run(debug=True)
