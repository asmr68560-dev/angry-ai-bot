#!/usr/bin/env python3
"""
АГРЕССИВНЫЙ TELEGRAM БОТ
ФИНАЛЬНАЯ ВЕРСИЯ
"""

import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE"

# ========== ОТВЕТЫ ==========
RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
    "Твой вопрос настолько тупой...",
    "Я бы ответил, но боюсь, ты не поймешь.",
    "Спроси у своей мамы.",
    "У меня нет времени на твою чушь.",
]

# ========== ФУНКЦИИ БОТА ==========
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, 
                    text="О, новый жертва... Чего надо?")

def help_cmd(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                    text="Помощь? Серьезно? Сам разбирайся!")

def echo(bot, update):
    response = random.choice(RESPONSES)
    bot.send_message(chat_id=update.message.chat_id, text=response)

def error_handler(bot, update, error):
    print(f"Бот ошибка: {error}")

# ========== ЗАПУСК БОТА ==========
def main():
    print("=" * 50)
    print("🤖 ЗАПУСК АГРЕССИВНОГО БОТА...")
    print("=" * 50)
    
    try:
        # 1. Создаем Updater с drop_pending_updates
        updater = Updater(BOT_TOKEN)
        
        # 2. Получаем диспетчер
        dp = updater.dispatcher
        
        # 3. Регистрируем обработчики
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_cmd))
        dp.add_handler(MessageHandler(Filters.text, echo))
        
        # 4. Регистрируем обработчик ошибок
        dp.add_error_handler(error_handler)
        
        print("✅ БОТ ЗАПУЩЕН!")
        print("📱 Telegram: отправь /start боту")
        print("=" * 50)
        
        # 5. Запускаем с очисткой старых обновлений
        updater.start_polling(clean=True)
        updater.idle()
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        print("Возможно бот уже запущен где-то еще!")
        print("=" * 50)

if __name__ == '__main__':
    main()
