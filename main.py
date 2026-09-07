import os
import time
import threading
import requests
from flask import Flask
from bs4 import BeautifulSoup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
BOT_TOKEN = "8988347697:AAE-GfG-S_2kfyjMMDd"
BASE_URL = "https://96ex.one"

# --- SCRAPER FUNCTION ---
def scrape_market_data(match_url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(match_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extracts market values (scrapes available elements or defaults)
        total_matched = soup.find(class_="matched-val")
        total_matched = total_matched.text.strip() if total_matched else "N/A"
        
        back_liquidity = soup.find(class_="back-depth")
        back_liquidity = back_liquidity.text.strip() if back_liquidity else "N/A"
        
        lay_liquidity = soup.find(class_="lay-depth")
        lay_liquidity = lay_liquidity.text.strip() if lay_liquidity else "N/A"

        return f"""📊 **IN-DEPTH MARKET ANALYSIS**
🏟️ **Match:** {match_url.split('/')[-1].replace('_', ' ').title()}
💰 **Total Matched Money:** {total_matched}
🟢 **Money Waiting to Back:** {back_liquidity}
🔴 **Money Waiting to Lay:** {lay_liquidity}
⏱️ **Updated:** {time.strftime('%H:%M:%S')}"""
    except Exception as e:
        return f"⚠️ Error scraping market data: {e}"

# --- MONITORING LOOP ---
async def monitor_loop(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    match_url = job.data
    
    analysis = scrape_market_data(match_url)
    await context.bot.send_message(chat_id=chat_id, text=analysis, parse_mode="Markdown")

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome! Use /matches to view live cricket games and select one for live market monitoring.")

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Live matches configuration (Add/update match URLs here)
    sample_matches = [
        {"name": "Match 1: Live Cricket Game A", "url": f"{BASE_URL}/game_play_1"},
        {"name": "Match 2: Live Cricket Game B", "url": f"{BASE_URL}/game_play_2"},
    ]
    
    keyboard = []
    for m in sample_matches:
        keyboard.append([InlineKeyboardButton(m["name"], callback_data=m["url"])])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👇 **Select a live match to monitor market load every 10 seconds:**", reply_markup=reply_markup, parse_mode="Markdown")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    match_url = query.data
    chat_id = query.message.chat_id
    
    # Remove any existing monitoring jobs for this chat
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    for job in current_jobs:
        job.schedule_removal()
        
    # Schedule automated tracking every 10 seconds
    context.job_queue.run_repeating(monitor_loop, interval=10, first=1, chat_id=chat_id, data=match_url, name=str(chat_id))
    await query.edit_message_text(text=f"✅ **Started live market monitoring for:**\n{match_url}\n\nUpdates will arrive every 10 seconds. Send /stop to pause.", parse_mode="Markdown")

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
    application.add_handler(CommandHandler("matches", matches))
    application.add_handler(CommandHandler("stop", stop))
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()

if __name__ == '__main__':
    main()
