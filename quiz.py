from os import listdir
from os.path import join

from environs import Env


def parse_quiz_from_file(file):
    quiz = {}

    question = None
    answer = None

    for text in file.read().split("\n\n"):
        if not text:
            continue

        splitted_text = text.split("\n", maxsplit=1)
        if len(splitted_text) == 1:
            continue

        header, body = splitted_text

        if header.lower().strip().startswith("вопрос"):
            question = " ".join(body.split())

        if header.lower().strip().startswith("ответ"):
            answer = " ".join(body.split())

        if question and answer:
            quiz[question] = answer
            question = None
            answer = None

    return quiz


def parse_quiz_from_dir(dir_path):
    quiz = {}
    for file_path in listdir(dir_path):
        with open(join(dir_path, file_path), "r", encoding="KOI8-R") as file:
            quiz.update(**parse_quiz_from_file(file))
    return quiz


if __name__ == "__main__":
    env = Env()
    env.read_env()
    quiz_path = env.path("QUIZ_PATH")
    print(parse_quiz_from_dir(quiz_path))
