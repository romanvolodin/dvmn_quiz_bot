import logging

import redis
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, CommandHandler, Updater


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def start(update, context):
    keyboard = [
        [
            InlineKeyboardButton("Новый вопрос", callback_data="question"),
            InlineKeyboardButton("Сдаться", callback_data="give_up"),
        ],
        [InlineKeyboardButton("Мой счёт", callback_data="score")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "Привет! Я бот для викторины!", reply_markup=reply_markup
    )


def button(update, context):
    query = update.callback_query
    query.answer()

    db = context.bot_data["db"]
    db.set(query.from_user.id, query.data)

    if query.data == "question":
        query.edit_message_text(text=f"Новый вопрос")
    if query.data == "give_up":
        query.edit_message_text(text=f"Вы сдались")
    if query.data == "score":
        query.edit_message_text(text=f"Ваш счет: 100500")


def main():
    env = Env()
    env.read_env()

    db = redis.Redis(host=env("REDIS_URL"), port=env("REDIS_PORT"))

    updater = Updater(env("TG_TOKEN"))

    dispatcher = updater.dispatcher
    dispatcher.bot_data["db"] = db
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
