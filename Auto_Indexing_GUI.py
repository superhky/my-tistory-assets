import requests
import feedparser
import time
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext
from google.oauth2 import service_account
from google.auth.transport.requests import AuthorizedSession

# === 사용자 설정 ===
API_KEY = "6f4dc8a521d2410c8104c8af5fe3504b"
BLOG_HOST = "superhky.tistory.com"
RSS_FEED_URL = f"https://{BLOG_HOST}/rss"
CHECK_INTERVAL = 600  # 초 단위 (10분)
GOOGLE_KEY_FILE = "C:\HwangCoding\Tistory_Auto_Indexing/goole-indexing-d5b29de59c71.json"  # 기본 Google 서비스 계정 키 파일 경로

# 제출 기록 방지용
submitted_urls = set()
running = False  # 실행 상태 플래그

# === Google Indexing API 인증 함수 ===
def load_google_session():
    try:
        SCOPES = ["https://www.googleapis.com/auth/indexing"]
        credentials = service_account.Credentials.from_service_account_file(
            GOOGLE_KEY_FILE, scopes=SCOPES
        )
        return AuthorizedSession(credentials)
    except Exception as e:
        log(f"❌ Google 키 로드 실패: {e}")
        return None

authed_session = load_google_session()

def submit_google(url):
    """Google Indexing API 제출"""
    if not authed_session:
        log("⚠️ Google 세션 없음. JSON 키 파일 확인 필요.")
        return
    endpoint = "https://indexing.googleapis.com/v3/urlNotifications:publish"
    data = {"url": url, "type": "URL_UPDATED"}
    try:
        response = authed_session.post(endpoint, json=data)
        if response.status_code == 200:
            log(f"✅ Google 제출 성공: {url}")
        else:
            log(f"⚠️ Google 제출 실패 {response.status_code}: {response.text}")
    except Exception as e:
        log(f"❌ Google 오류: {e}")

def submit_indexnow(urls):
    """IndexNow 제출 (Bing, Yandex, Seznam)"""
    endpoint = f"https://www.bing.com/indexnow?key={API_KEY}"
    data = {"host": BLOG_HOST, "key": API_KEY, "urlList": urls}
    try:
        r = requests.post(endpoint, json=data)
        log(f"IndexNow {r.status_code}: {urls}")
    except Exception as e:
        log(f"❌ IndexNow 오류: {e}")

def submit_naver(url):
    """네이버 Ping 제출"""
    try:
        ping_url = f"https://searchadvisor.naver.com/ping?site=https://{BLOG_HOST}&url={url}"
        r = requests.get(ping_url)
        log(f"Naver {r.status_code}: {url}")
    except Exception as e:
        log(f"❌ Naver 오류: {e}")

def check_rss():
    """RSS 피드 확인"""
    feed = feedparser.parse(RSS_FEED_URL)
    new_urls = []
    for entry in feed.entries:
        url = entry.link
        if url not in submitted_urls:
            new_urls.append(url)
            submitted_urls.add(url)
    return new_urls

# === 로그 출력 ===
def log(message):
    text_area.insert(tk.END, message + "\n")
    text_area.see(tk.END)

# === 실행 루프 ===
def worker():
    global running
    log("🚀 자동 제출 시작...")
    while running:
        new_posts = check_rss()
        if new_posts:
            submit_indexnow(new_posts)
            for u in new_posts:
                submit_google(u)
                submit_naver(u)
        else:
            log("⏳ 새 글 없음, 다음 확인까지 대기...")
        time.sleep(CHECK_INTERVAL)
    log("🛑 자동 제출 중지됨.")

def start():
    global running
    if not running:
        running = True
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()

def stop():
    global running
    running = False

# === Tkinter GUI ===
root = tk.Tk()
root.title("Tistory Auto Submitter (Bing+Google+Naver)")
root.geometry("700x400")

frame = tk.Frame(root)
frame.pack(pady=10)

start_btn = tk.Button(frame, text="▶ 실행", command=start, width=15, bg="green", fg="white")
start_btn.grid(row=0, column=0, padx=5)

stop_btn = tk.Button(frame, text="⏹ 중지", command=stop, width=15, bg="red", fg="white")
stop_btn.grid(row=0, column=1, padx=5)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=20)
text_area.pack(padx=10, pady=10)

root.mainloop()
