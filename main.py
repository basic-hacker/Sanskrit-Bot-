import json
import logging
import os
import asyncio
from telegram import Update, Poll
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PollAnswerHandler,
    CallbackContext,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Enable logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Questions from JSON File
QUESTION_FILE = "quiz.json"
if os.path.exists(QUESTION_FILE):
    with open(QUESTION_FILE, "r", encoding="utf-8") as file:
        questions_data = json.load(file)
else:
    questions_data = []

# Store active quizzes and messages for auto-delete
active_quizzes = {}
sent_messages = {}

# Scheduler for automatic cleanup
scheduler = AsyncIOScheduler()
scheduler.start()

# Telegram Bot Token (Replace with your actual bot token)
TOKEN = os.getenv("BOT_TOKEN")


# Function to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    topics = list(set(q["topic_name"].strip() for q in questions_data))

    if not topics:
        await update.message.reply_text("❌ No topics available.")
        return

    topic_list = "\n".join(f"/quiz {t}" for t in topics)
    await update.message.reply_text(f"📚 **Available Topics:**\n{topic_list}")


# Function to start quiz based on selected topic
async def start_quiz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if len(context.args) == 0:
        await update.message.reply_text("⚠ Please provide a topic name. Example: /quiz वैदिक संहिता")
        return

    user_input_topic = " ".join(context.args).strip()  # Remove extra spaces
    available_topics = {q["topic_name"].strip(): q["topic_name"] for q in questions_data}

    # Match user input with available topics
    matched_topic = available_topics.get(user_input_topic)

    if not matched_topic:
        await update.message.reply_text("⚠ Invalid topic name. Use /start to see available topics.")
        return

    topic_questions = [q for q in questions_data if q["topic_name"] == matched_topic]
    active_quizzes[chat_id] = {"questions": topic_questions, "index": 0}

    await update.message.reply_text(f"🎯 {matched_topic} Quiz Started! You will receive a new question every 30 seconds.")

    # Schedule the first question
    context.job_queue.run_once(send_quiz, 1, chat_id=chat_id)


# Function to send quiz questions every 30 seconds
async def send_quiz(context: CallbackContext) -> None:
    chat_id = context.job.chat_id
    if chat_id not in active_quizzes:
        return

    quiz_data = active_quizzes[chat_id]
    index = quiz_data["index"]

    if index >= len(quiz_data["questions"]):
        del active_quizzes[chat_id]
        await context.bot.send_message(chat_id, "✅ Quiz Completed!")
        return

    question_data = quiz_data["questions"][index]
    quiz_data["index"] += 1

    message = await context.bot.send_poll(
        chat_id,
        question=question_data["question"],
        options=question_data["options"],
        type=Poll.QUIZ,
        correct_option_id=question_data["answer"],
        is_anonymous=False,
    )

    # Store the message for auto-delete
    if chat_id not in sent_messages:
        sent_messages[chat_id] = []

    sent_messages[chat_id].append(message.message_id)

    # Schedule deletion after 15 minutes
    context.job_queue.run_once(delete_old_messages, 900, chat_id=chat_id)

    # Schedule the next question in 30 seconds
    context.job_queue.run_once(send_quiz, 30, chat_id=chat_id)


# Function to handle poll answers
async def handle_poll_answer(update: Update, context: CallbackContext) -> None:
    poll_id = update.poll.id
    logger.info(f"Poll Answer Received: {poll_id}")


# Function to stop the quiz
async def stop_quiz(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if chat_id in active_quizzes:
        del active_quizzes[chat_id]
        await update.message.reply_text("⛔ Quiz Stopped!")
    else:
        await update.message.reply_text("⚠ No active quiz to stop.")


# Function to manually clean chat
async def clean_chat(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    if chat_id in sent_messages:
        for msg_id in sent_messages[chat_id]:
            try:
                await context.bot.delete_message(chat_id, msg_id)
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        sent_messages[chat_id] = []
        await update.message.reply_text("🧹 Chat cleaned!")
    else:
        await update.message.reply_text("⚠ No messages to clean.")


# Function to delete old messages automatically
async def delete_old_messages(context: CallbackContext) -> None:
    chat_id = context.job.chat_id
    if chat_id in sent_messages:
        for msg_id in sent_messages[chat_id]:
            try:
                await context.bot.delete_message(chat_id, msg_id)
            except Exception as e:
                logger.error(f"Error deleting message: {e}")
        sent_messages[chat_id] = []


# Main function
def main():
    application = Application.builder().token(TOKEN).build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", start_quiz))
    application.add_handler(CommandHandler("stopquiz", stop_quiz))
    application.add_handler(CommandHandler("clean", clean_chat))

    # Poll Answer Handler
    application.add_handler(PollAnswerHandler(handle_poll_answer))

    # Run bot
    application.run_polling()


if __name__ == "__main__":
    main()
