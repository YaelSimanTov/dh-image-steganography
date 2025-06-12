from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
import re
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util.Padding import pad, unpad

END_MARKER = "$t3g0$"
# S = "123456"  # הסיסמה לשיתוף


def get_aes_key(password):
    return SHA256.new(password.encode()).digest()


def encrypt_message(message, password):
    key = get_aes_key(password)
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = cipher.encrypt(pad(message.encode(), AES.block_size))
    return ciphertext.hex()


def decrypt_message(hex_ciphertext, password):
    key = get_aes_key(password)
    cipher = AES.new(key, AES.MODE_ECB)
    ciphertext = bytes.fromhex(hex_ciphertext)
    return unpad(cipher.decrypt(ciphertext), AES.block_size).decode()


def local_variance(block):
    return np.var(block)


def embed_message_variance(message, input_image, output_image ,sign):
    img = Image.open(input_image).convert("RGB")
    array = np.array(img)
    gray = img.convert("L")
    gray_arr = np.array(gray)

    var_map = generic_filter(gray_arr, local_variance, size=3, mode='reflect')
    min_var = np.min(var_map)
    max_var = np.max(var_map)
    step = (max_var - min_var) / 6 if max_var > min_var else 1

    encrypted = encrypt_message(message + END_MARKER, sign)
    enc_len = len(encrypted)
    header = f"{min_var:.6f},{max_var:.6f}|{enc_len:04X}"
    full_message = header + "|" + encrypted

    bits = ''.join(f"{ord(c):08b}" for c in full_message)
    lsb_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    idx = 0
    for y in range(1, array.shape[0] - 1, 3):
        for x in range(1, array.shape[1] - 1, 3):
            if idx >= len(bits):
                break
            var = var_map[y, x]
            bin_idx = int((var - min_var) / step) if step else 0
            bin_idx = min(bin_idx, 5)
            pos1, pos2 = lsb_pairs[bin_idx]
            r = array[y, x, 0]
            if idx + 2 <= len(bits):
                b1, b2 = int(bits[idx]), int(bits[idx + 1])
                mask1 = ~(1 << pos1) & 0xFF
                mask2 = ~(1 << pos2) & 0xFF
                r = (r & mask1) | (b1 << pos1)
                r = (r & mask2) | (b2 << pos2)
                array[y, x, 0] = r
                idx += 2
        if idx >= len(bits):
            break

    out = Image.fromarray(array)
    out.save(output_image)
    print(f"✅ Encrypted message embedded into {output_image}")


def extract_message_variance(input_image, sign):
    img = Image.open(input_image).convert("RGB")
    array = np.array(img)
    gray = img.convert("L")
    gray_arr = np.array(gray)
    var_map = generic_filter(gray_arr, local_variance, size=3, mode='reflect')
    lsb_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    header_bits = []
    max_header_bits = 300 * 8  # יותר מקום כדי לתפוס header ארוך
    for y in range(1, gray_arr.shape[0] - 1, 3):
        for x in range(1, gray_arr.shape[1] - 1, 3):
            r = array[y, x, 0]
            pos1, pos2 = lsb_pairs[0]
            header_bits.append(str((r >> pos1) & 1))
            header_bits.append(str((r >> pos2) & 1))
            if len(header_bits) >= max_header_bits:
                break
        if len(header_bits) >= max_header_bits:
            break

    header = ''
    for i in range(0, len(header_bits), 8):
        byte = ''.join(header_bits[i:i + 8])
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        header += char
        if re.search(r'^\d+\.\d{6},\d+\.\d{6}\|[0-9A-Fa-f]{4}\|', header):
            break

    pattern = r'^(\d+\.\d{6}),(\d+\.\d{6})\|([0-9A-Fa-f]{4})\|'
    match = re.match(pattern, header)
    if not match:
        print("שגיאה: HEADER לא תקין.")
        return ""

    min_var = float(match.group(1))
    max_var = float(match.group(2))
    enc_len = int(match.group(3), 16)
    step = (max_var - min_var) / 6 if max_var > min_var else 1

    enc_start = match.end()
    needed_bits = enc_start * 8 + enc_len * 8  # כי hex = 4 ביטים

    bits = []
    for y in range(1, gray_arr.shape[0] - 1, 3):
        for x in range(1, gray_arr.shape[1] - 1, 3):
            var = var_map[y, x]
            bin_idx = int((var - min_var) / step) if step else 0
            bin_idx = min(bin_idx, 5)
            pos1, pos2 = lsb_pairs[bin_idx]
            r = array[y, x, 0]
            bits.append(str((r >> pos1) & 1))
            bits.append(str((r >> pos2) & 1))
            if len(bits) >= needed_bits:
                break
        if len(bits) >= needed_bits:
            break

    message = ''
    for i in range(0, len(bits), 8):
        byte = ''.join(bits[i:i + 8])
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        message += char

    encrypted_part = message[enc_start:enc_start + enc_len]

    try:
        decrypted = decrypt_message(encrypted_part, sign)
    except Exception as e:
        print("שגיאה בפענוח AES:", e)
        return ""

    final_msg = decrypted.split(END_MARKER)[0]
    print("The message is:\n", final_msg)
    return final_msg


# # דוגמה לשימוש:
# embed_message_variance("Hello world! it is a beautiful day, this year 2025", "dog.png", "output_w_secr.png")
# extract_message_variance("output_w_secr.png")
