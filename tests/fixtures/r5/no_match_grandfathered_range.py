# Regression guard: the final changelog explicitly grandfathers
# -32000..-32019 as "implementation-defined... existing SDK usage is
# grandfathered" - safe to keep, must not be flagged.


def handle(err):
    if err.code == -32010:
        raise ValueError("custom app-defined error")
