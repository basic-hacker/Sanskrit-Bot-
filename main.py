import os
import json
import random
import logging
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue

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

# Dictionary to track active quizzes per chat
active_quizzes = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command to welcome users."""
    await update.message.reply_text("🤖 Welcome to the Quiz Bot!\n\nCommands:\n/startquiz - Start automatic quiz\n/stopquiz - Stop the quiz")

async def send_quiz(context: ContextTypes.DEFAULT_TYPE):
    """Sends a new quiz question."""
    job = context.job
    chat_id = job.chat_id

    # If the chat ID is not in active_quizzes, stop sending questions
    if chat_id not in active_quizzes:
        return

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

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts an automatic quiz that sends questions every 30 seconds."""
    chat_id = update.effective_chat.id

    # Check if quiz is already running
    if chat_id in active_quizzes:
        await update.message.reply_text("🚀 The quiz is already running!")
        return

    # Add chat to active quizzes
    active_quizzes[chat_id] = True

    # Schedule the quiz job every 30 seconds
    context.job_queue.run_repeating(send_quiz, interval=30, first=0, chat_id=chat_id)

    await update.message.reply_text("✅ Quiz started! A new question will be sent every 30 seconds.")

async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops the automatic quiz."""
    chat_id = update.effective_chat.id

    # Check if quiz is running
    if chat_id not in active_quizzes:
        await update.message.reply_text("⚠️ No quiz is running!")
        return

    # Remove chat from active quizzes
    del active_quizzes[chat_id]

    # Remove all scheduled jobs for this chat
    context.job_queue.stop()

    await update.message.reply_text("🛑 Quiz stopped!")

def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("startquiz", start_quiz))
    application.add_handler(CommandHandler("stopquiz", stop_quiz))

    logger.info("✅ Quiz Bot is running... 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
