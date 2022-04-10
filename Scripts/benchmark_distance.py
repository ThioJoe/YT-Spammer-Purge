"""
Benchmark rapidfuzz and python-Levenshtein time

Author:
    Pushpam Punjabi
    Machine Learning Engineer
"""

import random
from datetime import datetime

import numpy as np
from Levenshtein import ratio
from rapidfuzz import fuzz

print("\nGenerating experiment...")

# Create random sentences
CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
lengths = np.arange(10, 1000)
NUM_PAIRS = 10000

# Initialize string lists
x = []
y = []

# Generate random strings
for _ in range(NUM_PAIRS):
    x_len = random.choice(lengths)
    y_len = random.choice(lengths)
    temp_x = []
    temp_y = []
    for _ in range(x_len):
        temp_x.append(random.choice(CHARS))
    for _ in range(y_len):
        temp_y.append(random.choice(CHARS))
    x.append("".join(temp_x))
    y.append("".join(temp_y))

print("Generated experiment.\n\nRunning benchmark...")

# Benchmart time for python-Levenshtein
start = datetime.now()
for sen_x, sen_y in zip(x, y):
    value = ratio(sen_x, sen_y)
end = datetime.now()
print(f"\npython-Levenshtein time: {end - start}")

# Benchmart time for rapidfuzz
start = datetime.now()
for sen_x, sen_y in zip(x, y):
    value = fuzz.ratio(sen_x, sen_y) / 100
end = datetime.now()
print(f"rapidfuzz time: {end - start}\n")
