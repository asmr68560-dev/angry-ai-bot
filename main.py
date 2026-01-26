#!/usr/bin/env python3
"""
АГРЕССИВНЫЙ TELEGRAM БОТ
РАБОЧАЯ ВЕРСИЯ
"""

# ========== ФИКС ДЛЯ Python 3.13 ==========
import sys
try:
    import imghdr
except ImportError:
    class ImghdrStub:
        @staticmethod
        def what(file, h=None):
            return None
    imghdr = ImghdrStub()
    sys.modules['imghdr'] = imghdr

# ========== ОСНОВНЫЕ ИМПОРТЫ ==========
import random
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE"

# ========== БАЗА ОТВЕТОВ ==========
RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
    "Твой вопрос настолько тупой...",
    "Я бы ответил, но боюсь, ты не поймешь.",
    "Спроси у своей мамы, она в воспитании явно провалилась.",
    "У меня нет времени на твою чушь.",
]

# ========== ФУНКЦИИ БОТА ==========
def start(bot, update):
    """Обработчик /start"""
    bot.send_message(
        chat_id=update.message.chat_id,
        text="О, новый жертва... Чего надо?"
    )

def help_command(bot, update):
    """Обработчик /help"""
    bot.send_message(
        chat_id=update.message.chat_id,
        text="Помощь? Серьезно? Сам разбирайся!"
    )

def echo(bot, update):
    """Обработчик всех сообщений"""
    response = random.choice(RESPONSES)
    bot.send_message(
        chat_id=update.message.chat_id,
        text=response
    )

def error(bot, update, error):
    """Обработчик ошибок"""
    print(f"Ошибка: {error}")

# ========== ЗАПУСК БОТА ==========
def main():
    print("=" * 50)
    print("🤖 БОТ ЗАПУСКАЕТСЯ...")
    print(f"Токен: {BOT_TOKEN[:10]}...")
    print("=" * 50)
    
    try:
        # 1. Создаем Updater
        updater = Updater(BOT_TOKEN)
        
        # 2. Получаем диспетчер
        dp = updater.dispatcher
        
        # 3. Регистрируем команды
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", help_command))
        
        # 4. Регистрируем обработчик сообщений
        dp.add_handler(MessageHandler(Filters.text, echo))
        
        # 5. Регистрируем обработчик ошибок
        dp.add_error_handler(error)
        
        # 6. Запускаем бота
        print("✅ БОТ ЗАПУЩЕН!")
        print("📱 Открой Telegram")
        print("💬 Отправь /start боту")
        print("=" * 50)
        
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПУСКА: {e}")
        print("=" * 50)

# ========== ТОЧКА ВХОДА ==========
if __name__ == '__main__':
    main()
