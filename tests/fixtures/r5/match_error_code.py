def handle(err):
    if err.code == -32601:
        raise ValueError("bad method")
