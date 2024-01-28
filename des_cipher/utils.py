# DES - Data Encryption Standard Algorithm
# Code is written by Danila Khlebokazov
from .constants import KEY_LENGTH


def permutation(block: str, perm_table: list) -> str:
    """
    Permutation function

    :param block:
    :param perm_table:
    :return permuted string:
    """
    return "".join([block[new_pos - 1] for new_pos in perm_table])  # -1 because starts with 1


def xor(a, b) -> str:
    return "".join([str(int(x) ^ int(y)) for x, y in zip(a, b)])


def plaintext_to_bits(plaintext: str) -> str:
    """
    Plaintext to bits
    :param plaintext:
    :return:
    """
    return "".join([format(ord(c), '08b') for c in plaintext])


def bytes_to_bits(byte_sequence):
    """
    Bytes to bits
    :param byte_sequence:
    :return:
    """
    bits = ''.join(format(byte, '08b') for byte in byte_sequence)
    return bits


def bits_to_text(bits: str) -> str:
    """
    Bits to text
    :param bits:
    :return:
    """
    # divide string in 8 bits (1 byte)
    bytes_list = [bits[i:i + 8] for i in range(0, len(bits), 8)]
    # transform each byte to symbol
    text = ''.join([chr(int(byte, 2)) for byte in bytes_list])
    return text


def shift_key(key: str, shift: int) -> str:
    """
    Shifts key to left on specific number
    :param key:
    :param shift:
    :return:
    """
    return key[shift:] + key[: shift]


def create_random_key() -> str:
    from random import choice
    return ''.join(choice('01') for _ in range(KEY_LENGTH))


def bits_to_bytes(bits):
    # Make sure the length of bits is a multiple of 8
    bits = bits.zfill((len(bits) + 7) // 8 * 8)

    # Convert binary string to integer
    integer_value = int(bits, 2)

    # Convert integer to bytes
    byte_representation = integer_value.to_bytes((integer_value.bit_length() + 7) // 8, 'big')

    return byte_representation
