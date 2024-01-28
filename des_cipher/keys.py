# DES - Data Encryption Standard Algorithm
# Code is written by Danila Khlebokazov
from .utils import *
from .constants import *


def schedule_key(key: str = None) -> (str, [str]):
    if not key:
        key = create_random_key()
        print(key)

    if len(key) != KEY_LENGTH:
        print("KEY IS NOT ENOUGH LENGTH!")
        exit(1)

    not_full_bytes = [key[i * 7:(i + 1) * 7] for i in range(8)]
    extended_key = key
    for i, not_full_byte in enumerate(not_full_bytes):
        number_of_ones = sum([int(bit) for bit in not_full_byte if int(bit) == 1])
        split_point = KEY_BITS_INSERT_ARRAY[i] - 1
        # if 1 remaining
        extended_key = extended_key[:split_point] + ("0" if number_of_ones % 2 else "1") + extended_key[split_point:]
    shuffled_key = permutation(extended_key, KEY_GENERATION_TABLE)
    key_schedule = []
    subkey = shuffled_key
    for shift in SHIFT_ARRAY:
        left_part = subkey[:int(KEY_LENGTH / 2)]
        right_part = subkey[int(KEY_LENGTH / 2):]
        subkey = shift_key(left_part, shift) + shift_key(right_part, shift)
        key_schedule.append(permutation(subkey, SUBKEY_CHOICE_TABLE))

    return key, key_schedule
