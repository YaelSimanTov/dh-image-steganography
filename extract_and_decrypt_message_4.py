from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from hashlib import sha256
from PIL import Image
import numpy as np
from isb_with_variance_aes import extract_message_variance
END_MARKER = "$t3g0$"

def derive_aes_key(shared_secret):
    return sha256(str(shared_secret).encode()).digest()

def extract_bits_from_image(image_path):
    """
       Extracts a hidden message from an image using standard LSB (Least Significant Bit) decoding.

       The function reads the least significant bit of each pixel value (RGB flattened),
       reconstructs the bitstream, converts it to bytes, and stops once it detects the END_MARKER.

       Parameters:
           image_path (str): Path to the input image containing the embedded message.

       Returns:
           bytes: The extracted hidden message as a bytes object, excluding the END_MARKER.

       Note:
           The global variable END_MARKER must be defined (e.g. END_MARKER = "$t3g0$").
           The message must have been embedded using a matching LSB-based method.
       """
    img = Image.open(image_path)
    img = img.convert("RGB")
    data = np.array(img).flatten()

    bits = ""
    for val in data:
        bits += str(val & 1)

    # Convert bits to bytes until END_MARKER appears
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    byte_list = []
    current_text = ""
    for char in chars:
        char_val = chr(int(char, 2))
        current_text += char_val
        byte_list.append(int(char, 2))
        if END_MARKER in current_text:
            break

    return bytes(byte_list[:-len(END_MARKER)])

def aes_decrypt_message(cipher_bytes, key):
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(cipher_bytes)
    return unpad(decrypted, AES.block_size).decode()


def extract_and_decrypt_message(image, S, method):
    S = str(S)

    """
    Extract and decrypt a hidden message from an image using the selected method.

    Parameters:
        image (str): Path to the image.
        S (str or int): Shared secret for AES decryption.
        method (str): Extraction method - '1' for regular LSB, '2' for variance-based.
    """
    print(f"\n Trying to extract from image: {image}")
    print(f" Using shared secret (S) = {S}")
    print(f" Method selected: {'LSB with AES' if method == '1' else 'Local Variance-based LSB'}")

    if method == '1':
        # Method 1: Extract bits using regular LSB + decrypt AES
        cipher_data = extract_bits_from_image(image)
        aes_key = derive_aes_key(S)
        print(f" Derived AES key: {aes_key.hex()}")
        print(f" Extracted {len(cipher_data)} bytes from LSB")

        try:
            message = aes_decrypt_message(cipher_data, aes_key)
            print(f" The message is:\n{message}")
        except Exception as e:
            print(f" Failed to decrypt message: {e}")

    elif method == '2':
        # Method 2: Use variance-based extraction
        print(" Extracting message using local variance-based LSB...")
        extract_message_variance(image, S)

    else:
        print(" Unknown method. Use '1' for LSB or '2' for variance-based.")

