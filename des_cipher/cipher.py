# DES - Data Encryption Standard Algorithm
# Code is written by Danila Khlebokazov
#
# STRUCTURE
# plaintext(64 bits) -> IP -> N rounds -> FP -> ciphertext(64bits)
import math

from .keys import *


def feistel(block: str, subkey: str) -> str:
    """
    The Feistel F function\n
    Expansion -> Key Mixing -> Substitution -> Permutation

    :param block:
    :param subkey:
    :return:
    """
    block_chunk_size = 6

    block = permutation(block, EXPANSION_TABLE)  # now it's 48 bits
    block = xor(block, subkey)  # xor with subkey

    new_block = ""
    for i in range(0, 8):
        chunk = block[i * block_chunk_size: (i + 1) * block_chunk_size]
        a = chunk[0] + chunk[5]
        b = chunk[1:5]

        a_int = int(a, 2)
        b_int = int(b, 2)

        num = S_BOXES[i][a_int][b_int]
        new_block += f"{num:04b}"

    return permutation(new_block, FEISTEL_PERMUTATION_TABLE)


def round(block: str, subkey: str) -> str:
    """
    Common round in DES
    :param block:
    :param subkey:
    :return:
    """
    left = block[: int(BLOCK_SIZE / 2)]
    right = block[int(BLOCK_SIZE / 2):]

    new_left = right
    new_right = xor(left, feistel(right, subkey))
    return new_left + new_right


def _cipher_flow(bittext: str, key: str = None, decode: bool = False, stepper=None):
    """
    The main ciphering code
    :param bittext:
    :param key:
    :param decode:
    :return:
    """
    # Use ECB(Electronic Cookbook)
    num_of_blocks = math.ceil(len(bittext) / BLOCK_SIZE)
    blocks = [bittext[i * BLOCK_SIZE: (i + 1) * BLOCK_SIZE].ljust(BLOCK_SIZE, "0") for i in range(num_of_blocks)]
    if not key:
        pass

    (key, schedule_keys) = schedule_key(key)

    if stepper:
        stepper.total_steps = len(blocks)

    cipherbits = ""
    for block in blocks:
        block = permutation(block, IP_TABLE)

        if decode:  # decode
            block = block[32:] + block[:32]

        for r in range(NUMBER_OF_ROUNDS):
            round_key = schedule_keys[NUMBER_OF_ROUNDS - 1 - r] if decode else schedule_keys[r]
            block = round(block, round_key)

        if decode:  # decode
            block = block[32:] + block[:32]

        block = permutation(block, FP_TABLE)
        cipherbits += block
        if stepper:
            stepper.step()
    return cipherbits, key


def encode_text(plaintext: str, key: str = None, stepper=None):
    """
    Encodes plaintext with key
    :param plaintext:
    :param key:
    :return:
    """
    bits = plaintext_to_bits(plaintext)
    cipherbits, key = _cipher_flow(bits, key, stepper=stepper)
    return bits_to_text(cipherbits), key


def encode_bits(bits: str, key: str = None, stepper=None):
    """
    Encodes bits with key
    :param bits:
    :param key:
    :return:
    """
    return _cipher_flow(bits, key, stepper=stepper)


def decode_text(cihertext: str, key: str, stepper=None):
    """
    Decodes ciphertext using key
    :param cihertext:
    :param key:
    :return:
    """
    bits = plaintext_to_bits(cihertext)
    plainbits, key = _cipher_flow(bits, key, decode=True, stepper=stepper)
    return bits_to_text(plainbits), key


def decode_bits(bits: str, key: str, stepper=None):
    """
    Decodes bits using key
    :param bits:
    :param key:
    :return:
    """
    return _cipher_flow(bits, key, decode=True, stepper=stepper)
