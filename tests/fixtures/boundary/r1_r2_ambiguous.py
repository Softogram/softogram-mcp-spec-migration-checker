BASKETS = {}


def add_item(ctx, item):
    BASKETS[ctx.session_id] = BASKETS.get(ctx.session_id, []) + [item]
