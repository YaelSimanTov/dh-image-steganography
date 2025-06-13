from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
END_MARKER = "$t3g0$"
from isb_with_variance_plaintext import extract_message_variance


def extract_dh_from_image_standard_lsb(image_path):
    """
       Extracts a Diffie-Hellman value embedded in an image using standard LSB steganography.

       The function reads the least significant bit of each RGB value, reconstructs the bitstream,
       converts it to characters, and stops once the END_MARKER is found. It returns the message
       with the marker removed.

       Parameters:
           image_path (str): Path to the image that contains the embedded DH value.

       Returns:
           str or None: The extracted string without the END_MARKER if found; otherwise, None.

       Notes:
           Requires a global variable END_MARKER (e.g., END_MARKER = "$t3g0$").
           The embedding method must use standard LSB encoding with a known end marker.
       """
    img = Image.open(image_path)
    img = img.convert("RGB")
    data = np.array(img).flatten()

    bits = ""
    for value in data:
        bits += str(value & 1)

    # Divide into groups of 8 bits
    chars = [bits[i:i+8] for i in range(0, len(bits), 8)]
    message = ""
    for char in chars:
        decoded_char = chr(int(char, 2))
        message += decoded_char
        if END_MARKER in message:
            break

    if END_MARKER in message:
        return message.replace(END_MARKER, "")
    else:
        return None

def parse_dh_values(message):
    try:
        p_str, g_str, A_str = message.split(":")
        return int(p_str), int(g_str), int(A_str)
    except:
        return None, None, None

def extract_dh_from_image(image, method):
    if method == '1':
        message = extract_dh_from_image_standard_lsb(image)
    elif method == '2':
         message = extract_message_variance(image)
    if message:
        p, g, A = parse_dh_values(message)
    else:
        print(" No valid message found in the image.")
    return p, g, A



