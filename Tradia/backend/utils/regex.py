import re

def get_numbers(value):
    # If it's already an int, return as is
    if isinstance(value, int):
        return value
    
    # If it's a string of digits only, convert to int
    if isinstance(value, str) and value.isdigit():
        return int(value)
    
    # Otherwise, try extracting digits from the string
    match = re.search(r"\d+", str(value))
    if match:
        return int(match.group())
    
    # If no number found, return None (or raise an error)
    return None
