import os
import time
import threading
import requests
from flask import Flask
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- KEEP-ALIVE FLASK SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and monitoring market load!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

threading.Thread(target=run_flask, daemon=True).start()

# --- BOT CONFIGURATION ---
BOT_TOKEN = "8988347697:AAE-GfG-S_2kfyjMMDd-535d5Yuurjbja1w"

# --- SCRAPER FUNCTION ---
def scrape_market_data(match_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(match_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return f"⚠️ Server returned status code {response.status_code}"
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        total_matched = soup.find(class_="matched-val")
        total_matched = total_matched.text.strip() if total_matched else "Data unavailable"
        
        back_liquidity = soup.find(class_="back-depth")
        back_liquidity = back_liquidity.text.strip() if back_liquidity else "Data unavailable"
        
        lay_liquidity = soup.find(class_="lay-depth")
        lay_liquidity = lay_liquidity.text.strip() if lay_liquidity else "Data unavailable"

        return (
            f"📊 **IN-DEPTH MARKET ANALYSIS**\n"
            f"🏟️ **Target:** {match_url}\n"
            f"💰 **Total Matched Money:** {total_matched}\n"
            f"🟢 **Money Waiting to Back:** {back_liquidity}\n"
            f"🔴 **Money Waiting to Lay:** {lay_liquidity}\n"
            f"⏱️ **Updated:** {time.strftime('%H:%M:%S IST')}"
        )
    except Exception as e:
        return f"⚠️ Scraping error: {str(e)}"

# --- MONITORING LOOP ---
async def monitor_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    match_url = job.data
    
    analysis = scrape_market_data(match_url)
    await context.bot.send_message(chat_id=chat_id, text=analysis, parse_mode="Markdown")

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "To track any live match, simply send:\n"
        "`/track <MATCH_URL>`\n\n"
        "Example:\n"
        "`/track https://96ex.one/game_play`",
        parse_mode="Markdown"
    )

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a URL!\nExample: `/track https://96ex.one/game_play`", parse_mode="Markdown")
        return

    match_url = context.args[0]
    
    # Cancel previous monitoring if running
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    # Start tracking new URL
    context.job_queue.run_repeating(monitor_loop, interval=10, first=1, chat_id=chat_id, data=match_url, name=str(chat_id))
    await update.message.reply_text(f"✅ **Started live market monitoring for:**\n{match_url}\n\nUpdates will arrive every 10 seconds. Send /stop to pause.", parse_mode="Markdown")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()
        await update.message.reply_text("⏹️ Stopped live market updates.")
    else:
        await update.message.reply_text("No active monitoring session found.")

# --- MAIN ENGINE ---
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("track", track))
    application.add_handler(CommandHandler("stop", stop))
    
    application.run_polling()

if __name__ == '__main__':
    main()
