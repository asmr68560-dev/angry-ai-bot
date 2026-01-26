import os
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

BOT_TOKEN = "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE"

RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
]

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="О, новый жертва...")

def echo(bot, update):
    response = random.choice(RESPONSES)
    bot.send_message(chat_id=update.message.chat_id, text=response)

def main():
    print("🤖 Бот запускается...")
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text, echo))
    print("✅ Бот запущен!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
