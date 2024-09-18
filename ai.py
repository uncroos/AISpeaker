import os
from gtts import gTTS
import pygame
import speech_recognition as sr
from google.cloud import aiplatform
from dotenv import load_dotenv

# .env 파일에 저장된 API 키를 불러오기 위해 dotenv 로드
load_dotenv()

# Google Cloud 프로젝트 ID 설정
os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT_ID")

# 음성 인식 함수
def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("말씀하세요...")
        recognizer.adjust_for_ambient_noise(source)  # 주변 소음 조정
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio, language='ko-KR')  # 한국어 음성 인식
        print(f"인식된 음성: {text}")
        return text
    except sr.UnknownValueError:
        print("음성을 이해할 수 없습니다. 다시 시도하세요.")
        return None
    except sr.RequestError:
        print("API 요청 오류가 발생했습니다.")
        return None

# Gemini 응답 생성 함수
def generate_response(prompt):
    # Gemini API 엔드포인트 및 매개변수 설정
    endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{os.getenv('GOOGLE_CLOUD_PROJECT_ID')}/locations/us-central1/publishers/google/models/text-bison-001:predict"
    headers = {"Content-Type": "application/json"}
    data = {
        "instances": [{"prompt": prompt}],
        "parameters": {"temperature": 0.7, "max_output_tokens": 100}
    }

    # API 호출 및 응답 처리
    response = aiplatform.gapic.PredictionServiceClient().predict(
        endpoint=endpoint,
        instances=data["instances"],
        parameters=data["parameters"],
        headers=headers,
    )
    return response.predictions[0]["content"]

# 음성 출력 함수
def speak_text(text):
    tts = gTTS(text=text, lang='ko')  # 한국어 음성 합성
    tts.save("response.mp3")
    
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        
        # 음성이 끝날 때까지 대기
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except pygame.error as e:
        print(f"Pygame 오류: {e}")
    finally:
        pygame.mixer.quit()

# 음성 인식을 반복해서 시도하는 함수
def get_valid_speech():
    while True:
        recognized_text = recognize_speech()
        if recognized_text:  # 유효한 음성이 인식될 때까지 반복
            return recognized_text

# 전체 실행 함수
def main():
    while True:
        # 음성 인식 후 Gemini 응답 받기
        recognized_text = get_valid_speech()
        response = generate_response(recognized_text)
        print(f"Gemini의 응답: {response}")
        
        # 응답을 음성으로 출력
        speak_text(response)

if __name__ == "__main__":
    main()