import random
from random import choice

import redis
import vk_api as vk
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from quiz import parse_quiz_from_file


KEYBOARD = VkKeyboard()
KEYBOARD.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
KEYBOARD.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
KEYBOARD.add_line()
KEYBOARD.add_button("Мой счет")


def start(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message="Привет! Я бот для проведения викторины!",
        random_id=random.randint(1, 1000),
        keyboard=KEYBOARD.get_keyboard(),
    )


def ask_question(event, vk_api, quiz, db):
    random_question, correct_answer = choice(list(quiz.items()))
    db.set(event.user_id, correct_answer)

    vk_api.messages.send(
        user_id=event.user_id,
        message=random_question,
        random_id=random.randint(1, 1000),
        keyboard=KEYBOARD.get_keyboard(),
    )


def check_answer(event, vk_api, db):
    user_answer = event.text
    correct_answer = db.get(event.user_id).decode()

    reply = "Не верно, попробуйте еще раз."

    if user_answer.lower() in correct_answer.lower():
        points = 100
        score = db.get(f"{event.user_id}_score")

        if score:
            points = int(score.decode()) + points

        reply = 'Правильно! Для следующего вопроса нажмите "Новый вопрос"'
        db.set(f"{event.user_id}_score", points)
        db.delete(event.user_id)

    vk_api.messages.send(
        user_id=event.user_id,
        message=reply,
        random_id=random.randint(1, 1000),
        keyboard=KEYBOARD.get_keyboard(),
    )


def give_up(event, vk_api, db):
    reply = 'Сначала надо задать вопрос. Нажмите кнопку "Новый вопрос"'
    correct_answer = db.get(event.user_id)

    if correct_answer:
        decoded_answer = correct_answer.decode()
        reply = (
            f"Правильный ответ: {decoded_answer}\n"
            'Для продолжения кнопку "Новый вопрос"'
        )
        db.delete(event.user_id)

    vk_api.messages.send(
        user_id=event.user_id,
        message=reply,
        random_id=random.randint(1, 1000),
        keyboard=KEYBOARD.get_keyboard(),
    )


def show_user_score(event, vk_api, db):
    reply = (
        "Вы пока не набрали ни одного очка. Попробуйте ответить "
        'на пару вопросов. Для запуска нажмите "Новый вопрос".'
    )
    score = db.get(f"{event.user_id}_score")
    if score:
        reply = f"Ваш счет: {score.decode()} очков."

    vk_api.messages.send(
        user_id=event.user_id,
        message=reply,
        random_id=random.randint(1, 1000),
        keyboard=KEYBOARD.get_keyboard(),
    )


if __name__ == "__main__":
    env = Env()
    env.read_env()

    db = redis.Redis(host=env("REDIS_URL"), port=env("REDIS_PORT"))
    with open("tmp/quiz-questions/120br.txt", "r", encoding="KOI8-R") as file:
        quiz = parse_quiz_from_file(file)

    vk_session = vk.VkApi(token=env("VK_ACCESS_KEY"))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text.lower() == "старт":
                start(event, vk_api)
                continue

            if event.text == "Новый вопрос":
                ask_question(event, vk_api, quiz, db)
                continue

            if event.text == "Сдаться":
                give_up(event, vk_api, db)
                continue

            if event.text == "Мой счет":
                show_user_score(event, vk_api, db)
                continue

            check_answer(event, vk_api, db)
