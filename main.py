import os
import random
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE")

RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
    "Твой вопрос настолько тупой...",
    "Я бы ответил, но боюсь, ты не поймешь.",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("О, новый жертва... Чего надо?")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Помощь? Серьезно? Сам разбирайся!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = random.choice(RESPONSES)
    await update.message.reply_text(response)

def main():
    print("🤖 Бот запускается...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
