STATE = {}


def remember(session_id, value):
    STATE[session_id] = value
