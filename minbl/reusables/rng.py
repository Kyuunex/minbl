import string
import random


def get_random_string(length):
    letters = string.ascii_lowercase+string.ascii_uppercase+string.digits
    return ''.join(random.choice(letters) for _ in range(length))

