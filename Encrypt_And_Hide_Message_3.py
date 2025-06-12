from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256
from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
from lsb_with_variance_AES import embed_message_variance

END_MARKER = "$t3g0$"

def derive_aes_key(shared_secret):
    # המרה של המספר הסודי למחרוזת, ואז גיבוב ל-256 ביט
    return sha256(str(shared_secret).encode()).digest()

def aes_encrypt_message(message, key):
    cipher = AES.new(key, AES.MODE_ECB)
    padded_msg = pad(message.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded_msg)
    return encrypted

def bytes_to_bits(byte_data):
    return ''.join(format(byte, '08b') for byte in byte_data) + ''.join(format(ord(c), '08b') for c in END_MARKER)

def embed_with_standard_lsb(image_path, cipher_bytes, output_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    data = np.array(img)
    flat = data.flatten()

    bits = bytes_to_bits(cipher_bytes)
    if len(bits) > len(flat):
        raise ValueError("Message is too large to embed in image.")

    for i in range(len(bits)):
        flat[i] = (flat[i] & 254) | int(bits[i])

    embedded = flat.reshape(data.shape)
    result_img = Image.fromarray(embedded.astype(np.uint8))
    result_img.save(output_path)
    print(f"✅ Encrypted message embedded into {output_path}")

def encrypt_and_embed_message(message, S, input_image, output_image, method):
    S = str(S)
    if method == '1':
        key = derive_aes_key(S)
        cipher_bytes = aes_encrypt_message(message, key)
        embed_with_standard_lsb(input_image, cipher_bytes, output_image)
    elif method == '2':
        embed_message_variance(message, input_image, output_image, S)
    else:
        print("❌ Invalid embedding method.")


# # שימוש:
# if __name__ == "__main__":
#     shared_secret = 123456  # המפתח שהתקבל מ-DH (S)
#     original_image = "clean_image.png"  # תמונה נקייה (ריקה)
#     output_image = "encrypted_message.png"
#
#     message = "הודעה סודית לצד השני"
#
#     aes_key = derive_aes_key(shared_secret)
#     encrypted_msg = aes_encrypt_message(message, aes_key)
#     embed_cipher_in_image(original_image, encrypted_msg, output_image)
