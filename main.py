import os
import random
import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== КОНФИГУРАЦИЯ ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8390892459:AAERG9pTHakirh9y-R0dl5P-v9TNmjTZmqE")

# ========== ЛОГИРОВАНИЕ ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== БАЗА АГРЕССИВНЫХ ОТВЕТОВ ==========
AGGRESSIVE_RESPONSES = [
    "Ты серьезно? Это все, что у тебя в голове?",
    "О, еще один гений решил потратить мое время...",
    "Даже мой код умнее тебя!",
    "Твой вопрос настолько тупой, что у меня синтаксическая ошибка возникла.",
    "Я бы ответил, но боюсь, ты не поймешь слова длиннее трех букв.",
    "Спроси у своей мамы, она в воспитании явно провалилась.",
    "У меня нет времени на твою чушь, я занят важными делами.",
    "Твоя глупость нарушает мой алгоритм, прекрати!",
    "Я видел идиотов, но ты... ты особенный.",
    "Закрой уже браузер и иди учиться, школота.",
]

# ========== ОБРАБОТЧИКИ КОМАНД ==========
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    greetings = [
        "О, новый жертва... значит, пользователь.",
        "Чего надо? Пиши быстрее, у меня нет времени.",
        "Ты тут? Ну ладно... задавай свой глупый вопрос.",
        "Добро пожаловать в ад. Шучу. Или нет.",
    ]
    await update.message.reply_text(random.choice(greetings))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text("Помощь? Серьезно? Сам разбирайся!")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /settings"""
    await update.message.reply_text("Настройки:\nАгрессивность: 8/10\nРежим зверя: ВКЛ")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    user_message = update.message.text
    logger.info(f"Получено сообщение: {user_message}")
    
    # Выбираем случайный агрессивный ответ
    response = random.choice(AGGRESSIVE_RESPONSES)
    
    # С шансом 40% добавляем дополнительное оскорбление
    if random.random() < 0.4:
        additions = [
            "\n\nИ это твой вопрос?",
            "\n\nНа это ты тратишь мое время?",
            "\n\nСерьезно? Это все?",
            "\n\nЧто, обиделся? Иди поплачь.",
        ]
        response += random.choice(additions)
    
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")
    if update and update.message:
        await update.message.reply_text("Ты что сделал? Я сломался из-за тебя!")

# ========== ЗАПУСК БОТА ==========
def main():
    """Основная функция запуска бота"""
    print("=" * 50)
    print("🤖 Агрессивный AI Бот запускается...")
    print(f"Токен: {BOT_TOKEN[:10]}...")
    print("=" * 50)
    
    # Проверка токена
    if not BOT_TOKEN or BOT_TOKEN == "ВАШ_ТОКЕН_БОТА":
        print("❌ ОШИБКА: Не задан BOT_TOKEN!")
        print("Задайте переменную окружения BOT_TOKEN на Render.com")
        return
    
    try:
        # Создаем приложение (НОВЫЙ стиль - работает в 20.7)
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрируем обработчики команд
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("settings", settings_command))
        
        # Регистрируем обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Регистрируем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Запускаем бота
        print("\n✅ Бот запущен! Ожидаю сообщений...")
        print("Нажмите Ctrl+C для остановки")
        
        # Запускаем polling (бесконечный цикл)
        application.run_polling(
            allowed_updates=Update.ALL_UPDATES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        print("Проверьте токен бота и настройки")

# ========== ТОЧКА ВХОДА ==========
if __name__ == '__main__':
    main()
