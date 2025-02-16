import json
import random
import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, ContextTypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your Telegram Bot Token (Use environment variables for security!)
BOT_TOKEN = "8047194490:AAERGpWtNX5aYsFbnGKnFrJKt4x4n6eaLt4"

# Load quiz questions from JSON file
with open("quiz.json", "r", encoding="utf-8") as file:
    quiz_questions = json.load(file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command to welcome users."""
    await update.message.reply_text("🤖 Welcome to the Quiz Bot! Type /quiz to start a quiz.")

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts a new quiz using Telegram Polls."""
    
    # Select a random question
    question_data = random.choice(quiz_questions)
    question = question_data["question"]
    options = question_data["options"]
    correct_index = question_data["answer"]  # 0-based index of the correct answer

    # Send the quiz as a poll (each time a new quiz starts)
    await update.message.reply_poll(
        question=question,
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        is_anonymous=False  # Users will see who answered what
    )

def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", start_quiz))

    logger.info("✅ Quiz Bot is running... 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
