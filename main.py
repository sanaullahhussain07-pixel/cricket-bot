import os
import threading
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run, daemon=True).start()

import time
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = "8988347697:AAE-GfG-S_2kfyjMMDd-535d5Yuurjbja1w"
CHAT_ID = "7340401618"
EXCHANGE_URL = "https://96ex.one/game_play2/Exchange"

last_volume = 0

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def fetch_market_load():
    global last_volume
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(EXCHANGE_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        volume_element = soup.find("span", class_="matched-amount") or soup.find("div", class_="total-matched")

        if volume_element:
            current_volume = float(volume_element.text.replace("Matched:", "").replace("₹", "").replace(",", "").strip())
            volume_change = current_volume - last_volume

            if last_volume > 0 and volume_change > 5000:
                alert_msg = f"🚨 *LIVE MARKET LOAD SPIKE*\n\n💰 *Total Matched:* ₹{current_volume:,.2f}\n⚡ *Spike:* +₹{volume_change:,.2f}"
                send_telegram_alert(alert_msg)

            last_volume = current_volume
            print(f"Volume: ₹{current_volume:,.2f}")
    except Exception as e:
        print(f"Scrape error: {e}")

if __name__ == "__main__":
    send_telegram_alert("🚀 *RENDER BOT ACTIVE*\nLive market monitoring started!")
    while True:
        fetch_market_load()
        time.sleep(15)
