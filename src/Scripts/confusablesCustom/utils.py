def is_ascii(string):
    for char in string:
        if ord(char) >= 128:
            return False
    return True
