import os
import json
import random
import asyncio
import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

# Load quiz questions safely
try:
    with open("quiz.json", "r", encoding="utf-8") as file:
        quiz_questions = json.load(file)
        if not isinstance(quiz_questions, list):
            raise ValueError("❌ quiz.json should be a list of questions!")
except (json.JSONDecodeError, FileNotFoundError) as e:
    raise ValueError(f"❌ Error loading quiz.json: {e}")

# Global variable to track whether the quiz is running
quiz_running = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command to welcome users."""
    await update.message.reply_text("🤖 Welcome to the Quiz Bot! Use /startquiz to begin the quiz and /stopquiz to stop it.")

async def send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a new quiz question."""
    if not quiz_running:
        return

    chat_id = update.effective_chat.id
    question_data = random.choice(quiz_questions)
    question = question_data["question"]
    options = question_data["options"]
    correct_index = question_data["answer"]

    await context.bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        is_anonymous=False
    )

async def quiz_loop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts an automatic quiz that sends questions every 30 seconds."""
    global quiz_running
    if quiz_running:
        await update.message.reply_text("🚀 The quiz is already running!")
        return

    quiz_running = True
    await update.message.reply_text("✅ Quiz started! A new question will be sent every 30 seconds.")

    while quiz_running:
        await send_quiz(update, context)
        await asyncio.sleep(30)  # Wait for 30 seconds before sending the next question

async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops the automatic quiz."""
    global quiz_running
    if not quiz_running:
        await update.message.reply_text("⚠️ No quiz is running!")
        return

    quiz_running = False
    await update.message.reply_text("🛑 Quiz stopped!")

def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("startquiz", quiz_loop))
    application.add_handler(CommandHandler("stopquiz", stop_quiz))

    logger.info("✅ Quiz Bot is running... 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
