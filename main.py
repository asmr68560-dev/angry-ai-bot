import os
import random
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== НАСТРОЙКИ ==========
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

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    greetings = ["О, новый жертва... Чего надо?", "Ты тут? Ну задавай вопрос..."]
    await update.message.reply_text(random.choice(greetings))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Помощь? Сам разбирайся!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = random.choice(AGGRESSIVE_RESPONSES)
    if random.random() < 0.3:
        response += " " + random.choice(["И это твой вопрос?", "Серьезно?", "На это ты время тратишь?"])
    await update.message.reply_text(response)

# ========== ЗАПУСК ==========
def main():
    print("=" * 50)
    print("🤖 Агрессивный Бот запускается...")
    print(f"Токен: {BOT_TOKEN[:10]}...")
    print("=" * 50)
    
    # СОЗДАЕМ ПРИЛОЖЕНИЕ НОВЫМ СПОСОБОМ - БЕЗ Updater!
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен! Ожидаю сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
