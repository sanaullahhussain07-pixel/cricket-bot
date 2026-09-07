import os
import time
import threading
import asyncio
from flask import Flask
from curl_cffi import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- KEEP-ALIVE FLASK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot status: Active"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# --- CONFIGURATION ---
BOT_TOKEN = "8988347697:AAE-GfG-S_2kfyjMMDd-535d5Yuurjbja1w"

# --- SCRAPER USING BROWSER TLS IMPERSONATION ---
def fetch_market_load(market_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://96ex.one/',
        'Origin': 'https://96ex.one'
    }
    try:
        # Impersonate Chrome to bypass Cloudflare 403 blocks
        response = requests.get(market_url, headers=headers, impersonate="chrome120", timeout=10)
        
        if response.status_code != 200:
            return f"⚠️ Endpoint error (Status Code: {response.status_code})"
            
        data = response.json()
        
        matched_val = data.get("totalMatched", "N/A") if isinstance(data, dict) else "N/A"
        back_val = data.get("backDepth", "N/A") if isinstance(data, dict) else "N/A"
        lay_val = data.get("layDepth", "N/A") if isinstance(data, dict) else "N/A"
        
        return (
            f"📊 **LIVE CRICKET MARKET LOAD**\n\n"
            f"💰 **Total Matched:** ₹{matched_val}\n"
            f"🟢 **Back Depth:** ₹{back_val}\n"
            f"🔴 **Lay Depth:** ₹{lay_val}\n\n"
            f"⏱️ **Timestamp:** {time.strftime('%H:%M:%S IST')}"
        )
    except Exception as e:
        return f"⚠️ Data parse error: {str(e)}"

# --- 10-SECOND REPEATING JOB ---
async def send_updates(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    market_url = job.data
    
    report = await asyncio.to_thread(fetch_market_load, market_url)
    await context.bot.send_message(chat_id=chat_id, text=report, parse_mode="Markdown")

# --- COMMAND HANDLERS ---
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if not context.args:
        await update.message.reply_text("⚠️ Send command as:\n`/track <MARKET_URL>`", parse_mode="Markdown")
        return

    market_url = context.args[0]
    
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    context.job_queue.run_repeating(send_updates, interval=10, first=1, chat_id=chat_id, data=market_url, name=str(chat_id))
    await update.message.reply_text("✅ **10-Second Market Tracking Activated!**\nSend /stop to pause updates.", parse_mode="Markdown")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("⏹️ Monitoring stopped.")
    else:
        await update.message.reply_text("No active monitoring session.")

# --- MAIN EXECUTION ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("track", track))
    application.add_handler(CommandHandler("stop", stop))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
