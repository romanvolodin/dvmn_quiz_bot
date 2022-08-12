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

USER_CHOICE, CHECK_ANSWER = range(2)

keyboard = [
    ["Новый вопрос", "Сдаться"],
    ["Мой счет"],
]
reply_markup = ReplyKeyboardMarkup(keyboard)


def start(update, context):
    update.message.reply_text(
        "Привет! Я бот для викторины!", reply_markup=reply_markup
    )
    return USER_CHOICE


def ask_question(update, context):
    quiz = context.bot_data["quiz"]
    random_question = choice(quiz)
    context.user_data["correct_answer"] = random_question["answer"]

    update.message.reply_text(
        random_question["question"], reply_markup=reply_markup
    )
    return CHECK_ANSWER


def check_answer(update, context):
    answer = update.message.text
    if answer == "Сдаться":
        # FIXME: копипаста функции give_up
        update.message.reply_text(
            "Правильный ответ: Да", reply_markup=reply_markup
        )
        return USER_CHOICE
    if answer == "да":
        update.message.reply_text(
            'Правильно! Для следующего вопроса нажмите "Новый вопрос"',
            reply_markup=reply_markup,
        )
        return USER_CHOICE
    update.message.reply_text(
        "Не верно, попробуйте еще раз.", reply_markup=reply_markup
    )
    return CHECK_ANSWER


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
    return USER_CHOICE


def show_user_score(update, context):
    update.message.reply_text(
        "Ваш счет: 100500 очков.", reply_markup=reply_markup
    )
    return USER_CHOICE


def cancel(update, context):
    update.message.reply_text("Bye!", reply_markup=ReplyKeyboardRemove())
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
                USER_CHOICE: [
                    MessageHandler(
                        Filters.regex("Новый вопрос"), ask_question
                    ),
                    MessageHandler(Filters.regex("Сдаться"), give_up),
                    MessageHandler(Filters.regex("Мой счет"), show_user_score),
                ],
                CHECK_ANSWER: [MessageHandler(Filters.text, check_answer)],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )
    )
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
