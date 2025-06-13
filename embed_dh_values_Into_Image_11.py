from PIL import Image
import numpy as np
from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
from isb_with_variance_plaintext import embed_message_variance
END_MARKER = "$t3g0$" #Marker indicating end of message


def create_dh_message(p, g, A):
    return f"{p}:{g}:{A}"

def int_to_bin_str(x, bits=16):
    return format(x, f'0{bits}b')

def message_to_bits(message):
    return ''.join(format(ord(c), '08b') for c in message + END_MARKER)


def embed_with_standard_lsb_without_AES(image_path, message, output_path):
    """
     Embeds a plaintext message into an image using standard LSB (Least Significant Bit) steganography,
     without any encryption (no AES involved).

     Each bit of the message is embedded into the least significant bit of each pixel component
     (R, G, B) in a flattened version of the image data.

     Parameters:
         image_path (str): Path to the input image file (should be in RGB format).
         message (str): The plaintext message to embed into the image.
         output_path (str): Path where the output image with the hidden message will be saved.

     Raises:
         ValueError: If the message is too long to fit in the image.

     Returns:
         None. The modified image is saved to the specified output path.
     """
    img = Image.open(image_path)
    img = img.convert("RGB")
    data = np.array(img)

    flat_data = data.flatten()
    bits = message_to_bits(message)

    if len(bits) > len(flat_data):
        raise ValueError("Message is too long to embed in this image!")

    for i in range(len(bits)):
        flat_data[i] = (flat_data[i] & 254) | int(bits[i])

    # reshape and save image
    new_data = flat_data.reshape(data.shape)
    new_img = Image.fromarray(new_data.astype(np.uint8))
    new_img.save(output_path)


def dh_key_generation_and_embedding(p, g, A, input_image, output_image, method):
    message = create_dh_message(p, g, A)
    if method == '1':
        embed_with_standard_lsb_without_AES(input_image, message, output_image)
        print(f" DH values (p, g, A) have been embedded into the image '{output_image}' successfully.")
    elif method == '2':
        embed_message_variance(message, input_image, output_image)
        print(f" DH values (p, g, A) have been embedded into the image '{output_image}' successfully.")

    else:
        print(" Invalid LSB method.")


from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
END_MARKER = "$t3g0$"
from extract_dh_from_image_2 import extract_dh_from_image_standard_lsb

def embed_B_into_image(message, input_image, output_image):
    embed_with_standard_lsb_without_AES(input_image, message, output_image)
    print(f" DH values ( B ) have been embedded into the image '{output_image}' successfully.")


def extract_B_from_image(image):
    b = extract_dh_from_image_standard_lsb(image)
    return b


