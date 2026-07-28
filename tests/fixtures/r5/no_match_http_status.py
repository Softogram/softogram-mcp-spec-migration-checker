def handle(response):
    if response.status_code == 404:
        return "not found"
