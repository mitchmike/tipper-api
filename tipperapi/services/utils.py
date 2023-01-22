

def safe_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except:
        return None
