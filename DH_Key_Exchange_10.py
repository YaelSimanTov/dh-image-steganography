import random

# Step 1: Generate a shared prime p and base g
p = 7919  # Example small prime (for real use, choose a large prime)
g = 2     # Primitive root

# Step 2: Each side chooses a private key
a = random.randint(2, p - 2)  # Alice's private key
# b = random.randint(2, p - 2)  # Bob's private key

# Step 3: Each side computes their public key
A = pow(g, a, p)  # Alice's public key
# B = pow(g, b, p)  # Bob's public key

# Step 4: Each side computes the shared secret key
# S_Alice = pow(B, a, p)  # Alice computes shared key from Bob's public key
# S_Bob = pow(A, b, p)    # Bob computes shared key from Alice's public key

# Output
print("Shared prime (p):", p)
print("Primitive root (g):", g)
print("\nAlice's private key (a):", a)
print("Alice's public key (A):", A)
# print("\nBob's private key (b):", b)
# print("Bob's public key (B):", B)
# print("\nAlice's shared secret:", S_Alice)
# print("Bob's shared secret:", S_Bob)
# print("Keys match:", S_Alice == S_Bob)

def generate_dh_values():
    return p, g, A, a

