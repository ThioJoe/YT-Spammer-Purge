import os
import sys

def assets_path(relative_path):
    if hasattr(sys, '_MEIPASS'): # If running as a pyinstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("Scripts/confusablesCustom/assets"), relative_path) # If running as script, specifies resource folder as /assets

CUSTOM_CONFUSABLE_PATH = os.path.join(assets_path("custom_confusables.txt"))
CONFUSABLES_PATH = os.path.join(assets_path("confusables.txt"))
CONFUSABLE_MAPPING_PATH = os.path.join(assets_path("confusable_mapping.json"))
MAX_SIMILARITY_DEPTH = 2
NON_NORMAL_ASCII_CHARS = ['@']
