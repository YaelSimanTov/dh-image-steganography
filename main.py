import os
from dh_key_exchange_10 import generate_dh_values
from embed_dh_values_into_image_11 import dh_key_generation_and_embedding
from extract_dh_from_image_2 import extract_dh_from_image
from encrypt_and_hide_message_3 import encrypt_and_embed_message
from extract_and_decrypt_message_4 import extract_and_decrypt_message
from embed_and_extract_B_Into_Image_12 import extract_B_from_image, embed_B_into_image
import random

def save_method_for_image(image_filename, method):
    meta_filename = image_filename + ".method.txt"
    with open(meta_filename, "w") as f:
        f.write(method)

def load_method_for_image(image_filename):
    meta_filename = image_filename + ".method.txt"
    try:
        with open(meta_filename, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def check_image_file_exists	(image_filename):
    if not os.path.exists(image_filename):
        print("Image file not found.")
        return False
    else:
        return True

def main_menu():
    print("\n DH Key Exchange + Steganography - Main Menu")
    print("1. Generate and Embed DH values into image (Sender - Step 1)")
    print("2. Extract DH values from image (Receiver - Step 1)")
    print("3. Encrypt message and embed (Sender - Step 2)")
    print("4. Extract and decrypt message (Receiver - Step 2)")
    print("0. Exit")
    return input("Choose an option: ").strip()

def choose_lsb_method():
    print("\nChoose LSB embedding method:")
    print("1. Standard LSB")
    print("2. Local Variance-Based LSB")
    return input("Enter 1 or 2: ").strip()

if __name__ == "__main__":
    while True:
        choice = main_menu()

        if choice == '1':
            # DH key generation + embedding
            p, g, A, a = generate_dh_values()
            print(f"\n Generated DH values:\np = {p}\ng = {g}\nA = {A}")
            image = input("Enter path to image to embed DH values (e.g. horse.png): ")
            if not check_image_file_exists(image): continue

            output = input("Enter output image filename (e.g. dh_embedded.png): ")
            # embed_dh_values_lsb(p, g, A, image, output)
            method = choose_lsb_method()
            save_method_for_image(output, method)
            dh_key_generation_and_embedding(p, g, A, image, output, method) # @NEED TO DO !!

        elif choice == '2':
            image = input("Enter path to image with embedded DH values (e.g. dh_embedded.png): ")
            if not check_image_file_exists(image): continue

            method = load_method_for_image(image)
            p, g, A = extract_dh_from_image(image, method)
            print(f"\n Extracted DH values:\np = {p}\ng = {g}\nA = {A}")
            # Generate receiver's private key b and public key B
            b = random.randint(2, p - 2)
            print("\nBob's private key (b):", b)
            B = pow(g, b, p)
            print("Bob's public key (B):", B)
            image = input("Enter path to image to embed B (e.g. dog.png): ")
            if not check_image_file_exists(image): continue

            output = input("Enter output image filename (e.g. B_embedded.png): ")
            embed_B_into_image(str(B), image, output)

            # Calculate shared secret
            S = pow(A, b, p)
            print(f"\n Bob Calculated shared secret (S) = {S}")

            # Save Bob's shared secret for comparison (only for testing)
            with open("shared_secret.txt", "w") as f:
                f.write(str(S))
            print(" Bob's shared secret saved to shared_secret.txt for later comparison.")

        elif choice == '3':
            image_with_B = input("Enter image file that contains B (e.g. B_embedded.png): ")
            if not check_image_file_exists(image_with_B): continue

            B = int(extract_B_from_image(image_with_B))
            print(f" Extracted B from image: {B}")
            S = pow(B, a, p)
            print(f" Alice Calculated shared secret (S) = {S}")

            # Try to compare with Bob's shared secret if available
            try:
                with open("shared_secret.txt", "r") as f:
                    bob_S = int(f.read().strip())
                if S == bob_S:
                    print(" Shared secret MATCH confirmed between Alice and Bob! ")
                else:
                    print(" Shared secret MISMATCH!  Something went wrong.")
                    continue
            except FileNotFoundError:
                print(" Bob's shared secret file not found. Skipping comparison.")

            message = input("Enter the message to encrypt and embed (e.g. It's a beautiful day. ): ")
            image = input("Enter path to image to embed message (e.g. deer.png): ")
            if not check_image_file_exists(image): continue

            output = input("Enter output image filename (e.g. encrypted_msg.png): ")

            method = choose_lsb_method()
            save_method_for_image(output, method)
            encrypt_and_embed_message(message, S, image, output, method)

        elif choice == '4':
            try:
                with open("shared_secret.txt", "r") as f:
                    S = int(f.read().strip())

                image = input("Enter image file with embedded encrypted message (e.g. encrypted_msg.png): ")
                if not check_image_file_exists(image) : continue

                # S = int(input("Enter shared secret (S): "))
                method = load_method_for_image(image)
                extract_and_decrypt_message(image, S, method) # @NEED TO DO !!
            except FileNotFoundError:
                print(" Bob's shared secret file not found. Skipping comparison.")
            finally:
                if os.path.exists("shared_secret.txt"):
                    os.remove("shared_secret.txt")

        elif choice == '0':
            print(" Exiting.")
            break

        else:
            print(" Invalid option. Please try again.")