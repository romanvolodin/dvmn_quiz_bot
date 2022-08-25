import logging
from random import choice

import redis
from environs import Env
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

from quiz import parse_quiz_from_dir


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

QUIZ = 1

keyboard = [
    ["Новый вопрос", "Сдаться"],
    ["Мой счет"],
]
reply_markup = ReplyKeyboardMarkup(keyboard)


def start(update, context):
    update.message.reply_text(
        "Привет! Я бот для викторины!", reply_markup=reply_markup
    )
    return QUIZ


def ask_question(update, context):
    quiz = context.bot_data["quiz"]
    db = context.bot_data["db"]
    user = update.message.from_user

    random_question, correct_answer = choice(list(quiz.items()))
    db.set(user["id"], correct_answer)

    update.message.reply_text(random_question, reply_markup=reply_markup)
    return QUIZ


def check_answer(update, context):
    db = context.bot_data["db"]
    user = update.message.from_user
    user_answer = update.message.text
    correct_answer = db.get(user["id"]).decode()

    reply = "Не верно, попробуйте еще раз."

    if user_answer.lower() in correct_answer.lower():
        points = 100
        score = db.get(f"{user['id']}_score")

        if score:
            points = int(score.decode()) + points

        reply = 'Правильно! Для следующего вопроса нажмите "Новый вопрос"'
        db.set(f"{user['id']}_score", points)
        db.delete(user["id"])

    update.message.reply_text(reply, reply_markup=reply_markup)
    return QUIZ


def give_up(update, context):
    db = context.bot_data["db"]
    user = update.message.from_user
    reply = 'Сначала надо задать вопрос. Нажмите кнопку "Новый вопрос"'
    correct_answer = db.get(user["id"])

    if correct_answer:
        decoded_answer = correct_answer.decode()
        reply = (
            f"Правильный ответ: {decoded_answer}\n"
            'Для продолжения кнопку "Новый вопрос"'
        )
        db.delete(user["id"])
    update.message.reply_text(reply, reply_markup=reply_markup)
    return QUIZ


def show_user_score(update, context):
    db = context.bot_data["db"]
    user = update.message.from_user
    reply = (
        "Вы пока не набрали ни одного очка. "
        'Попробуйте ответить на пару вопросов. Для запуска нажмите "Новый вопрос".'
    )
    score = db.get(f"{user['id']}_score")

    if score:
        reply = f"Ваш счет: {score.decode()} очков."

    update.message.reply_text(reply, reply_markup=reply_markup)
    return QUIZ


def stop_quiz(update, context):
    db = context.bot_data["db"]
    user = update.message.from_user

    correct_answer = db.get(user["id"])
    if correct_answer:
        db.delete(user["id"])

    score = db.get(f"{user['id']}_score")
    if score:
        db.delete(f"{user['id']}_score")

    update.message.reply_text(
        "Это была славная битва!", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()

    db = redis.Redis(host=env("REDIS_URL"), port=env("REDIS_PORT"))
    quiz = parse_quiz_from_dir(env("QUIZ_PATH"))

    updater = Updater(env("TG_TOKEN"))

    dispatcher = updater.dispatcher
    dispatcher.bot_data["db"] = db
    dispatcher.bot_data["quiz"] = quiz
    dispatcher.add_handler(
        ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                QUIZ: [
                    CommandHandler("cancel", stop_quiz),
                    MessageHandler(
                        Filters.regex("Новый вопрос"), ask_question
                    ),
                    MessageHandler(Filters.regex("Сдаться"), give_up),
                    MessageHandler(Filters.regex("Мой счет"), show_user_score),
                    MessageHandler(Filters.text, check_answer),
                ],
            },
            fallbacks=[CommandHandler("cancel", stop_quiz)],
        )
    )
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
