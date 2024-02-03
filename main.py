import json
import os
import random
import requests
from openai import OpenAI


def load_word_lists(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines() if len(line.strip()) == 5]


def filter_words(words, guess, feedback):
    filtered_words = words

    for i, letter in enumerate(guess):
        if feedback[i]['result'] == 'correct':
            filtered_words = [word for word in filtered_words if word[i] == letter]
        elif feedback[i]['result'] == 'present':
            filtered_words = [word for word in filtered_words if letter in word and word[i] != letter]
        elif feedback[i]['result'] == 'absent':
            filtered_words = [word for word in filtered_words if letter not in word]

    return filtered_words


def get_feedback_from_guess(guess, get_url, seed, size=5):
    params = {
        'guess': guess,
        'size': size,
        'seed': seed
    }

    r = requests.get(get_url, params=params)

    if r.status_code == 200:
        feedback = r.json()
        return guess, feedback
    else:
        print("Error making API call")
        return None, None


def make_guess(word_list, url, seed, size=5):
    my_guess = random.choice(word_list)

    return get_feedback_from_guess(my_guess, url, seed, size)


def solve_with_llm(url, seed, size=5):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    guess = "salet"
    prompt = ""
    chars = []
    guessed = []
    guessed_str = "Exclude the following words: "

    for turn in range(20):

        guess, feedback = get_feedback_from_guess(guess, url, seed, size)

        if all(f['result'] == 'correct' for f in feedback):
            print(f"Correct! The right answer is {guess}")
            break

        print(f"Turn {turn + 1}, guess is {guess}, not correct")

        guessed.append(guess)
        guessed_str += f", {guess}, "

        for f in feedback:
            if f['result'] == 'absent':
                if not f['guess'] in chars:
                    chars.append(f['guess'])
                    prompt += f"non of the characters is {f['guess']},\n"
            elif f['result'] == 'correct':
                if not f['guess'] in chars:
                    chars.append(f['guess'])
                    prompt += f"c{f['slot'] + 1} is {f['guess']},\n"
            else:
                if not f['guess'] in chars:
                    chars.append(f['guess'])
                    prompt += f"one of c1, c2, c3, c4, c5 is {f['guess']}, but c{f['slot'] + 1} is not {f['guess']},\n"

        user_content = f"""Generate an array of 5 characters c1, c2, c3, c4, c5 that together form a meaningful word, and we know that:\n{prompt}. 
Give the answer in a JSON format with the schema: c1: character 1, c2: character 2, c3: character, c4: character, c5: character, {guessed_str}"""


        completion = client.chat.completions.create(
            model='gpt-4-0125-preview',
            messages=[
                {"role": "system",
                 "content": "You are a great Wordle solver who always find the answer within no more than 5 turns."},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"}
        )

        re = json.loads(completion.choices[0].message.content)

        guess = f"{re['c1']}{re['c2']}{re['c3']}{re['c4']}{re['c5']}"

        turn += 1


def solve_normal(file_path, url, seed, size=5):
    words = load_word_lists(file_path)

    guess, feedback = make_guess(words, url, seed, size)

    attempt = 1

    max_attempts = 6

    while attempt <= max_attempts:

        print(f"Attempt {attempt}: {guess}")
        # print("Feedback: ", feedback)

        if all(f['result'] == 'correct' for f in feedback):
            print("Correct!")
            break

        words = filter_words(words, guess, feedback)
        guess, feedback = make_guess(words, url, 123)
        attempt += 1

    if attempt > max_attempts:
        print(f"Failed to solve within {max_attempts} attempts")


if __name__ == '__main__':
    url = "https://wordle.votee.dev:8000/random"

    file_path = 'wordle-list/words'

    solve_normal(file_path, url, 110)

    # solve_with_llm(url, 123)
