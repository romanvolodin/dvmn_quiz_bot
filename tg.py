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

from main import parse_quiz_from_file


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

    random_question = choice(quiz)
    context.user_data["correct_answer"] = random_question["answer"]
    db.set(user["id"], random_question["question"])

    update.message.reply_text(
        random_question["question"], reply_markup=reply_markup
    )
    return QUIZ


def check_answer(update, context):
    user_answer = update.message.text
    correct_answer = context.user_data["correct_answer"]

    reply = "Не верно, попробуйте еще раз."

    if user_answer.lower() in correct_answer.lower():
        reply = 'Правильно! Для следующего вопроса нажмите "Новый вопрос"'
        context.user_data["score"] = context.user_data.get("score", 0) + 100
        del context.user_data["correct_answer"]

    update.message.reply_text(reply, reply_markup=reply_markup)
    return QUIZ


def give_up(update, context):
    reply = 'Сначала надо задать вопрос. Нажмите кнопку "Новый вопрос"'
    correct_answer = context.user_data.get("correct_answer")
    if correct_answer:
        reply = (
            f"Правильный ответ: {correct_answer}\n"
            'Для продолжения кнопку "Новый вопрос"'
        )
        del context.user_data["correct_answer"]
    update.message.reply_text(reply, reply_markup=reply_markup)
    return QUIZ


def show_user_score(update, context):
    reply = (
        "Вы пока не набрали ни одного очка. "
        'Попробуйте ответить на пару вопросов. Для запуска нажмите "Новый вопрос".'
    )
    score = context.user_data.get("score", 0)

    if score:
        reply = f"Ваш счет: {score} очков."

    update.message.reply_text(reply, reply_markup=reply_markup)
    return QUIZ


def stop_quiz(update, context):
    correct_answer = context.user_data.get("correct_answer")
    if correct_answer:
        del context.user_data["correct_answer"]

    score = context.user_data.get("score")
    if score:
        del context.user_data["score"]

    update.message.reply_text(
        "Это была славная битва!", reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()

    db = redis.Redis(host=env("REDIS_URL"), port=env("REDIS_PORT"))
    with open("tmp/quiz-questions/120br.txt", "r", encoding="KOI8-R") as file:
        quiz = parse_quiz_from_file(file)

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
