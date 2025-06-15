from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from hashlib import sha256
from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
from lsb_with_variance_aes import embed_message_variance

END_MARKER = "$t3g0$"

def derive_aes_key(shared_secret):
    # Convert the secret number to a string, then hash it to 256 bits
    return sha256(str(shared_secret).encode()).digest()

def aes_encrypt_message(message, key):
    cipher = AES.new(key, AES.MODE_ECB)
    padded_msg = pad(message.encode(), AES.block_size)
    encrypted = cipher.encrypt(padded_msg)
    return encrypted

def bytes_to_bits(byte_data):
    return ''.join(format(byte, '08b') for byte in byte_data) + ''.join(format(ord(c), '08b') for c in END_MARKER)

def embed_with_standard_lsb(image_path, cipher_bytes, output_path):
    """
       Embeds an encrypted byte sequence into an image using standard LSB (Least Significant Bit) steganography.

       The function modifies the least significant bit of each pixel component (R, G, B)
       in the flattened image data to encode the provided ciphertext.

       Parameters:
           image_path (str): Path to the input image file (should be in RGB format).
           cipher_bytes (bytes): Encrypted message as a bytes object to be embedded into the image.
           output_path (str): Path to save the resulting image with the embedded message.

       Raises:
           ValueError: If the message is too large to fit in the image's pixel data.

       Returns:
           None. Saves the modified image to the specified output path.

       Notes:
           - Uses 1 bit per color channel component.
           - Assumes the input image is large enough to contain all the message bits.
           - Make sure to use a corresponding extraction function to retrieve the message.
       """
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
    print(f" Encrypted message embedded into {output_path}")

def encrypt_and_embed_message(message, S, input_image, output_image, method):
    """
        Encrypts a plaintext message and embeds it into an image using the selected steganographic method.

        Depending on the selected method, the function either:
        - Uses AES encryption and standard LSB steganography (method '1'), or
        - Uses variance-based adaptive LSB embedding (method '2').

        Parameters:
            message (str): The plaintext message to encrypt and embed.
            S (str or int): Shared secret used to derive the AES encryption key.
            input_image (str): Path to the input image file (RGB format).
            output_image (str): Path to save the image with the embedded message.
            method (str): Embedding method to use:
                          - '1' for standard LSB with AES encryption
                          - '2' for variance-based adaptive LSB (plaintext)

        Returns:
            None. The image with the embedded message is saved to the specified output path.

        Notes:
            - Requires functions: derive_aes_key(), aes_encrypt_message(), embed_with_standard_lsb(), embed_message_variance().
            - The image must be large enough to contain the encrypted message.
            - The global END_MARKER should be used inside embed_message_variance if needed.
        """
    S = str(S)
    if method == '1':
        key = derive_aes_key(S)
        cipher_bytes = aes_encrypt_message(message, key)
        embed_with_standard_lsb(input_image, cipher_bytes, output_image)
    elif method == '2':
        embed_message_variance(message, input_image, output_image, S)
    else:
        print(" Invalid embedding method.")



# # Usage:
# if __name__ == "__main__":
#     shared_secret = 123456  # The key received from DH (S)
#     original_image = "clean_image.png"  # Clean (empty) image
#     output_image = "encrypted_message.png"
#
#     message = "Secret message to the other side"
#
#     aes_key = derive_aes_key(shared_secret)
#     encrypted_msg = aes_encrypt_message(message, aes_key)
#     embed_cipher_in_image(original_image, encrypted_msg, output_image)
