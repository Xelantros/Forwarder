#libraries that I've used in this project
#playwright, pyTelegramBotAPI, python-dotenv
#Have fun using this project!

from playwright.sync_api import sync_playwright
import time
import requests
import hashlib
import json
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN =os.getenv('TELEGRAM_TOKEN')
CHAT_ID =os.getenv('CHAT_ID')
GROUP_URL =os.getenv('GROUP_URL')
SESSION_FILE = "session.json"
KNOWN_HASHES_FILE = "known_hashes.json"

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

def send_photo(chat_id, photo_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    response = requests.get(photo_url)
    files = {'photo': response.content}
    requests.post(url, data={"chat_id": chat_id}, files=files)

def send_video(chat_id, video_url):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo"
    response = requests.get(video_url)
    files = {'video': response.content}
    requests.post(url, data={"chat_id": chat_id}, files=files)

def parse_messages(page):
    bubbles = page.query_selector_all("div.bubble")
    messages = []

    for bubble in bubbles:
        author_el = bubble.query_selector("button.header span.name span.text")
        author = author_el.inner_text().strip() if author_el else "Неизвестно"

        text_el = bubble.query_selector("span.text.svelte-1htnb3l")
        text = text_el.inner_text().strip() if text_el else ""

        time_el = bubble.query_selector("span.meta span.text.svelte-13lobfv")
        time_str = time_el.inner_text().strip() if time_el else ""

        # Фото и видео
        img_el = bubble.query_selector("img")
        img_url = img_el.get_attribute("src") if img_el else None

        video_el = bubble.query_selector("video")
        video_url = video_el.get_attribute("src") if video_el else None

        msg_hash = hashlib.md5(f"{author}-{text}-{img_url}-{video_url}-{time_str}".encode()).hexdigest()

        messages.append({
            "author": author,
            "text": text,
            "time": time_str,
            "img_url": img_url,
            "video_url": video_url,
            "hash": msg_hash
        })

    return messages

def main():
    known_hashes = set()
    if os.path.exists(KNOWN_HASHES_FILE):
        with open(KNOWN_HASHES_FILE, "r") as f:
            known_hashes = set(json.load(f))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # можно указать executable_path для Brave
        context = browser.new_context(storage_state=SESSION_FILE if os.path.exists(SESSION_FILE) else None)
        page = context.new_page()
        page.goto(GROUP_URL)

        if not os.path.exists(SESSION_FILE):
            input("Войдите в MAX вручную, затем нажмите Enter...")
            context.storage_state(path=SESSION_FILE)

        print("Начинаю мониторинг чата...")

        while True:
            messages = parse_messages(page)

            for msg in messages:
                if msg["hash"] not in known_hashes:
                    known_hashes.add(msg["hash"])
                    if msg["text"]:
                        send_to_telegram(f"[{msg['time']}] {msg['author']}: {msg['text'] + '    Паша Логинов лучший!!! Я его преданная фанатка :з'}")
                    if msg["img_url"]:
                        send_photo(CHAT_ID, msg["img_url"])
                    if msg["video_url"]:
                        send_video(CHAT_ID, msg["video_url"])

            with open(KNOWN_HASHES_FILE, "w") as f:
                json.dump(list(known_hashes), f)

            time.sleep(2)

if __name__ == "__main__":
    main()