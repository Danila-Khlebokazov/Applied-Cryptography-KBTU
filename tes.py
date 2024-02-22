from des_cipher import decode_text, create_random_key, encode_text


key = create_random_key()

plaintext = "BlowFish"

ciphertext, _ = encode_text(plaintext, key=key)

print(ciphertext)

plaintext_new, _ = decode_text(ciphertext, key)

print(plaintext_new)
