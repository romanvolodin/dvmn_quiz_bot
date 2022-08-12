import random
from random import choice

import redis
import vk_api as vk
from environs import Env
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkEventType, VkLongPoll

from main import parse_quiz_from_file


KEYBOARD = VkKeyboard()
KEYBOARD.add_button("Новый вопрос", color=VkKeyboardColor.PRIMARY)
KEYBOARD.add_button("Сдаться", color=VkKeyboardColor.NEGATIVE)
KEYBOARD.add_line()
KEYBOARD.add_button("Мой счет")


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        message=f"ECHO: {event.text}",
        random_id=random.randint(1, 1000),
        keyboard=KEYBOARD.get_keyboard(),
    )


def ask_question(event, vk_api, quiz, db):
    random_question = choice(quiz)
    db.set(event.user_id, random_question["answer"])

    vk_api.messages.send(
        user_id=event.user_id,
        message=random_question["question"],
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
            if event.text == "Новый вопрос":
                ask_question(event, vk_api, quiz, db)
                continue

            if event.text == "Сдаться":
                give_up(event, vk_api, db)
                continue
            echo(event, vk_api)
