from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
import re

END_MARKER = "$t3g0$"


def local_variance(block):
    return np.var(block)

def embed_message_variance(message, input_image, output_image):
    img = Image.open(input_image).convert("RGB")
    array = np.array(img)
    gray = img.convert("L")
    gray_arr = np.array(gray)

    var_map = generic_filter(gray_arr, local_variance, size=3, mode='reflect')
    min_var = np.min(var_map)
    max_var = np.max(var_map)
    step = (max_var - min_var) / 6 if max_var > min_var else 1

    # Step 1: add header (min_var,max_var) + message + END_MARKER
    header = f"{min_var:.6f},{max_var:.6f}"
    full_message = header + message + END_MARKER

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
                # r = (r & ~(1 << pos1)) | (b1 << pos1)
                # r = (r & ~(1 << pos2)) | (b2 << pos2)
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


def extract_message_variance(input_image):
    img = Image.open(input_image).convert("RGB")
    array = np.array(img)
    gray = img.convert("L")
    gray_arr = np.array(gray)
    var_map = generic_filter(gray_arr, local_variance, size=3, mode='reflect')
    lsb_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    # שלב 1: חילוץ header ראשוני (20 תווים מספיקים)
    header_bits = []
    max_header_bits = 20 * 8  # נגיד 20 תווים לכותרת
    for y in range(1, gray_arr.shape[0] - 1, 3):
        for x in range(1, gray_arr.shape[1] - 1, 3):
            r = array[y, x, 0]
            pos1, pos2 = lsb_pairs[0]  # שימוש זמני בקבוצה הראשונה
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
        if ',' in header and header.count('.') >= 2:
            break

    try:
        min_var, max_var = map(float, header.split(',')[:2])
    except ValueError:
        print("שגיאה: לא ניתן לפענח את הכותרת:", repr(header))
        return ""

    step = (max_var - min_var) / 6 if max_var > min_var else 1

    # שלב 2: חילוץ ההודעה לפי שונות
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

    # פענוח ביטים להודעה
    message = ''
    for i in range(0, len(bits), 8):
        byte = ''.join(bits[i:i + 8])
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        message += char
        if END_MARKER in message:
            message = message.split(END_MARKER)[0]
            break
    pattern = r'^\d+\.\d{6},\d+\.\d{6}'
    message_r = re.sub(pattern, '', message).lstrip()     # הסרה של תחילית ההודעה  מההתחלה
    print(" the message is: ", message_r)
    return message_r



# שימוש לדוגמה
# embed_message_variance("Hello world! it is a beautiful day , this year 2025", "clean.png", "op88uuo.png")
# extract_message_variance("op88uuo.png")
