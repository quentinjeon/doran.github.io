import os
import speech_recognition as sr
from youtubesearchpython import VideosSearch
import pafy
import vlc

# Pafy 백엔드를 yt-dlp로 설정
os.environ["PAFY_BACKEND"] = "yt-dlp"

# 음성 인식을 통해 텍스트로 변환하는 함수
def recognize_speech_from_mic():
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
        print("음성을 인식하지 못했습니다.")
        return None
    except sr.RequestError as e:
        print(f"API 요청 오류: {e}")
        return None

# 유튜브에서 노래를 검색하는 함수
def search_youtube(query):
    print(f"'{query}'로 유튜브에서 검색 중...")
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()["result"]

    if result:
        video_url = result[0]["link"]
        print(f"유튜브 URL: {video_url}")
        return video_url
    else:
        print("해당 노래를 찾을 수 없습니다.")
        return None

# 유튜브 동영상을 재생하는 함수
def play_youtube(url):
    try:
        video = pafy.new(url)  # pafy를 사용하여 유튜브 오디오 스트림 가져오기
        best = video.getbestaudio()
        playurl = best.url

        player = vlc.MediaPlayer(playurl)  # vlc를 사용하여 오디오 스트림 재생
        player.play()

        print("노래를 재생합니다...")
        input("노래를 멈추려면 엔터를 누르세요.")
        player.stop()
    except Exception as e:
        print(f"동영상을 재생할 수 없습니다: {e}")

# 메인 프로그램
if __name__ == "__main__":
    # 음성 인식을 통해 노래 제목과 가수명을 받아옴
    song_info = recognize_speech_from_mic()

    if song_info:
        # 유튜브에서 노래를 검색
        video_url = search_youtube(song_info)

        if video_url:
            # 검색된 노래를 재생
            play_youtube(video_url)
