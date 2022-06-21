from random import randint


def parse_quiz_from_file(file):
    quiz = {}
    for text in file.read().split("\n\n"):
        if not text:
            continue
        number = randint(0, 1_000_000)
        header, body = text.split("\n", maxsplit=1)
        if header.startswith("Вопрос"):
            quiz[f"вопрос{number}"] = " ".join(body.split())
        if header.startswith("Ответ"):
            quiz[f"ответ{number}"] = " ".join(body.split())
    return quiz


def main():
    with open("tmp/quiz-questions/120br.txt", "r", encoding="KOI8-R") as file:
        quiz = parse_quiz_from_file(file)
    print(quiz)


if __name__ == "__main__":
    main()
