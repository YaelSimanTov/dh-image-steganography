from PIL import Image
import numpy as np
from scipy.ndimage import generic_filter
END_MARKER = "$t3g0$"
from Extract_DH_From_Image_2 import extract_dh_from_image_standard_lsb
from Embed_DH_Values_Into_Image_11 import embed_with_standard_lsb_without_AES
def embed_B_into_image(message, input_image, output_image):
    embed_with_standard_lsb_without_AES(input_image, message, output_image)
    print(f"✅ DH values ( B ) have been embedded into the image '{output_image}' successfully.")


def extract_B_from_image(image):
    b = extract_dh_from_image_standard_lsb(image)
    return b
