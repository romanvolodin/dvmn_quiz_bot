from itertools import count
from random import randint


def parse_quiz_from_file(file):
    quiz = {}
    counter = count()

    number = next(counter)
    question = None
    answer = None

    for text in file.read().split("\n\n"):
        if not text:
            continue

        header, body = text.split("\n", maxsplit=1)

        if header.lower().strip().startswith("вопрос"):
            question = " ".join(body.split())

        if header.lower().strip().startswith("ответ"):
            answer = " ".join(body.split())

        if question and answer:
            quiz[number] = {}
            quiz[number]["question"] = question
            quiz[number]["answer"] = answer
            number = next(counter)
            question = None
            answer = None

    return quiz


def main():
    with open("tmp/quiz-questions/120br.txt", "r", encoding="KOI8-R") as file:
        quiz = parse_quiz_from_file(file)
    print(quiz)


if __name__ == "__main__":
    main()
