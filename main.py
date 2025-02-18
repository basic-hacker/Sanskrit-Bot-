import os
import json
import random
import logging
from telegram import Update, Poll
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)

# ✅ Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Load bot token (replace with actual token if needed)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ✅ Load quiz questions from JSON
with open("quiz.json", "r", encoding="utf-8") as file:
    quiz_questions = json.load(file)

# ✅ Store active quizzes
active_quizzes = {}

# ✅ Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcomes users and provides instructions."""
    await update.message.reply_text("🤖 स्वागत है! क्विज़ शुरू करने के लिए /quiz टाइप करें।")

# ✅ Command: /quiz (Ask user to choose a topic)
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to choose a topic before starting the quiz."""
    chat_id = update.message.chat_id

    # Get unique topics
    topic_map = {q["topic_code"]: q["topic_name"] for q in quiz_questions}
    topics = list(topic_map.values())  # List of topic names
    topic_codes = list(topic_map.keys())  # Corresponding topic codes

    # Send poll to choose topic
    message = await update.message.reply_poll(
        question="📚 किस विषय का क्विज़ शुरू करें?",
        options=topics,
        is_anonymous=False
    )

    # Store topic mapping
    active_quizzes[chat_id] = {
        "poll_message_id": message.message_id,
        "topic_map": topic_map,
        "topic_codes": topic_codes,
        "chosen_topic_code": None
    }

# ✅ Handle topic selection
async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start quiz with the selected topic."""
    answer = update.poll_answer
    user_id = answer.user.id
    chat_id = update.effective_chat.id

    if chat_id in active_quizzes:
        topic_map = active_quizzes[chat_id]["topic_map"]
        topic_codes = active_quizzes[chat_id]["topic_codes"]
        selected_topic_code = topic_codes[answer.option_ids[0]]  # Get topic_code from index

        # Set the chosen topic code
        active_quizzes[chat_id]["chosen_topic_code"] = selected_topic_code
        selected_topic_name = topic_map[selected_topic_code]  # Get topic_name

        await context.bot.send_message(chat_id, f"✅ {selected_topic_name} का क्विज़ शुरू हो रहा है!")
        await send_quiz(update, context)

# ✅ Function to send quiz questions
async def send_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a quiz question every 30 seconds."""
    chat_id = update.effective_chat.id

    if chat_id not in active_quizzes or not active_quizzes[chat_id]["chosen_topic_code"]:
        return  # No active quiz

    # Get topic_code
    selected_topic_code = active_quizzes[chat_id]["chosen_topic_code"]

    # Fetch questions from the selected topic_code
    topic_questions = [q for q in quiz_questions if q["topic_code"] == selected_topic_code]
    
    if not topic_questions:
        await context.bot.send_message(chat_id, "❌ इस विषय के लिए कोई प्रश्न उपलब्ध नहीं है।")
        return

    question_data = random.choice(topic_questions)
    question = question_data["question"]
    options = question_data["options"]
    correct_index = question_data["answer"]

    # Send the quiz poll
    message = await context.bot.send_poll(
        chat_id=chat_id,
        question=question,
        options=options,
        type=Poll.QUIZ,
        correct_option_id=correct_index,
        is_anonymous=False
    )

    # Store message ID for deletion
    context.job_queue.run_once(delete_message, when=900, data={"chat_id": chat_id, "message_id": message.message_id})

# ✅ Auto-delete messages after 15 minutes
async def delete_message(context: ContextTypes.DEFAULT_TYPE):
    """Deletes quiz messages after 15 minutes."""
    job = context.job
    data = job.data

    try:
        await context.bot.delete_message(data["chat_id"], data["message_id"])
    except Exception as e:
        logger.warning(f"❌ Failed to delete message: {e}")

# ✅ Command: /stopquiz (Stops the quiz)
async def stop_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops the ongoing quiz."""
    chat_id = update.effective_chat.id
    if chat_id in active_quizzes:
        del active_quizzes[chat_id]
        await update.message.reply_text("⛔ क्विज़ बंद कर दिया गया।")
    else:
        await update.message.reply_text("⚠ कोई भी क्विज़ सक्रिय नहीं है।")

# ✅ Command: /startquiz (Restarts quiz)
async def restart_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restarts the quiz."""
    chat_id = update.effective_chat.id
    if chat_id in active_quizzes:
        await update.message.reply_text("✅ क्विज़ फिर से शुरू हो रहा है...")
        await send_quiz(update, context)
    else:
        await update.message.reply_text("⚠ कोई भी क्विज़ सक्रिय नहीं है। पहले /quiz कमांड का उपयोग करें।")

# ✅ Command: /clearchat (Deletes bot messages)
async def clear_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes all messages sent by the bot in the chat."""
    chat_id = update.message.chat_id

    async for message in context.bot.get_chat_history(chat_id, limit=50):
        try:
            await context.bot.delete_message(chat_id, message.message_id)
        except Exception as e:
            logger.warning(f"❌ Failed to delete message: {e}")

    await update.message.reply_text("✅ चैट साफ़ कर दी गई!", quote=True)

# ✅ Main function to run bot
def main():
    """Run the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # ✅ Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", start_quiz))
    application.add_handler(CommandHandler("stopquiz", stop_quiz))
    application.add_handler(CommandHandler("startquiz", restart_quiz))
    application.add_handler(CommandHandler("clearchat", clear_chat))

    # ✅ Poll Answer Handler (to capture topic selection)
    application.add_handler(MessageHandler(filters.PollAnswer, handle_poll_answer))

    logger.info("✅ Quiz Bot is running... 🚀")
    application.run_polling()

if __name__ == "__main__":
    main()
