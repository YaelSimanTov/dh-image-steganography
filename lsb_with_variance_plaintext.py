from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
import re

END_MARKER = "$t3g0$"


def local_variance(block):
    return np.var(block)

def embed_message_variance(message, input_image, output_image):
    """
        Embeds a plaintext message into an image using adaptive LSB steganography based on local variance.

        The image is divided into 3x3 blocks, and for each block, the local variance is calculated
        to determine which pair of LSB positions to use for hiding 2 bits. This ensures bits are hidden
        more effectively in visually noisy regions.

        The message is prepended with a header containing the min and max variance values, and
        appended with a global END_MARKER to signal message termination during extraction.

        Parameters:
            message (str): The message to be embedded into the image.
            input_image (str): Path to the input image (should be in RGB format).
            output_image (str): Path where the output image with the hidden message will be saved.

        Returns:
            None. The modified image is saved to the specified output path.

        Notes:
            - Uses a 2-bit embedding scheme with 6 LSB position pairs.
            - The global variable END_MARKER must be defined (e.g. END_MARKER = "$t3g0$").
            - The message is embedded into the red channel only.
            - No encryption is used in this version.
        """
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
    """
       Extracts a plaintext message from an image using variance-based LSB steganography.

       The function first extracts a short header (assumed to be 20 characters) from the image
       using a fixed LSB pair. This header encodes the min and max variance values used during
       embedding. Based on the variance map, it dynamically selects LSB bit pairs for extracting
       the message bits from the red channel of each 3x3 block.

       Parameters:
           input_image (str): Path to the image containing the embedded message.

       Returns:
           str: The extracted message without the variance header and END_MARKER.
                If the header cannot be decoded, an empty string is returned.

       Notes:
           - The function assumes the message ends with a global END_MARKER (e.g., "$t3g0$").
           - The variance is computed using a 3x3 neighborhood on the grayscale version of the image.
           - The function uses 6 pre-defined LSB bit-pairs based on variance binning.
       """
    img = Image.open(input_image).convert("RGB")
    array = np.array(img)
    gray = img.convert("L")
    gray_arr = np.array(gray)
    var_map = generic_filter(gray_arr, local_variance, size=3, mode='reflect')
    lsb_pairs = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]

    # Step 1: Extract initial header (20 characters should be enough)
    header_bits = []
    max_header_bits = 20 * 8   # assume 20 characters for the header
    for y in range(1, gray_arr.shape[0] - 1, 3):
        for x in range(1, gray_arr.shape[1] - 1, 3):
            r = array[y, x, 0]
            pos1, pos2 = lsb_pairs[0] # Using the first pair for header extraction
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
        print("Error: Failed to decode the header:", repr(header))
        return ""

    step = (max_var - min_var) / 6 if max_var > min_var else 1

   # Step 2: Extracting the message based on variance
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

    #Decoding bits into a message
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
    message_r = re.sub(pattern, '', message).lstrip()     #Removing the prefix from the beginning of the message
    print(" the message is: ", message_r)
    return message_r



# Example usage:
# embed_message_variance("Hello world! it is a beautiful day , this year 2025", "clean.png", "op88uuo.png")
# extract_message_variance("op88uuo.png")
