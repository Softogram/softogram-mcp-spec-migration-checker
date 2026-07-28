def handle(err):
    if err.code == -32002:
        raise ValueError("basket not found")
