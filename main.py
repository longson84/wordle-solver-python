import random
import requests


def load_word_lists(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f.readlines() if len(line.strip()) == 5]


def filter_words(words, guess, feedback):
    filtered_words = words

    for i, letter in enumerate(guess):
        if feedback[i] == 'green':
            filtered_words = [word for word in filtered_words if word[i] == letter]
        elif feedback[i] == 'yellow':
            filtered_words = [word for word in filtered_words if letter in word and word[i] != letter]
        elif feedback[i] == 'grey':
            filtered_words = [word for word in filtered_words if letter not in word]

    return filtered_words


def parse_feedback(api_feedback):
    return ['grey' if f['result'] == 'absent' else 'yellow' if f['result'] == 'present' else 'green' for f in
            api_feedback]


def make_guess(word_list, get_url, seed, size=5):
    my_guess = random.choice(word_list)

    params = {
        'guess': my_guess,
        'size': size,
        'seed': seed
    }

    r = requests.get(get_url, params=params)

    if r.status_code == 200:
        api_feedback = r.json()
        feedback_parsed = parse_feedback(api_feedback)
        return my_guess, feedback_parsed
    else:
        print("Error making API call")
        return None, None


if __name__ == '__main__':

    m_file_path = 'wordle-list/words'
    url = "https://wordle.votee.dev:8000/random"

    words = load_word_lists(m_file_path)

    guess, feedback = make_guess(words, url, 123)

    attempt = 1

    max_attempts = 6

    while attempt <= max_attempts:

        print(f"Attempt {attempt}: {guess}")
        print("Feedback: ", feedback)

        if all(f == 'green' for f in feedback):
            print("Correct!")
            break

        words = filter_words(words, guess, feedback)
        guess, feedback = make_guess(words, url, 123)
        attempt += 1

    if attempt > max_attempts:
        print(f"Failed to solve within {max_attempts} attempts")
