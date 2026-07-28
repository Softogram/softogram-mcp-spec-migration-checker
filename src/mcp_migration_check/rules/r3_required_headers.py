"""R3 - hand-rolled transport missing the two new required request fields.

See docs/low-level-design/003-r3-transport-detection.md for the full
signal-order table this implements, and the answer to "does R3 even have
an app-code target" (issue #20): `Mcp-Method`/`Mcp-Name` are transport-layer
headers the official MCP Python SDK's Streamable HTTP transport handles
internally, so this rule only fires on hand-rolled MCP-over-HTTP transport
code that bypasses the SDK's built-in transport - never on SDK-managed
servers, and never on servers whose transport is decided at runtime (that
is the NEEDS-MANUAL-CHECK case).
"""

from __future__ import annotations

import ast

from mcp_migration_check.models import NEEDS_MANUAL_CHECK, NeedsManualCheck

_REQUIRED_HEADERS = {"mcp-method", "mcp-name"}
_ROUTE_DECORATOR_METHODS = {"route", "post"}
_WEB_FRAMEWORK_MODULES = {"starlette", "fastapi", "uvicorn"}
_ASGI_PARAMS = ("scope", "receive", "send")
_SDK_STREAMABLE_HTTP_NAMES = {"streamable_http_app", "streamable_http_asgi_app"}


def _decorator_mentions_mcp(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False
    is_route_call = (
        isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr in _ROUTE_DECORATOR_METHODS
    )
    if not is_route_call:
        return False
    for node in ast.walk(decorator):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "mcp" in node.value.lower():
                return True
    return False


def _is_raw_asgi_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    arg_names = [a.arg for a in node.args.args]
    return arg_names[-3:] == list(_ASGI_PARAMS)


def _find_handrolled_endpoints(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    endpoints: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if any(_decorator_mentions_mcp(dec) for dec in node.decorator_list):
            endpoints.append(node)
        elif _is_raw_asgi_signature(node):
            endpoints.append(node)
    return endpoints


def _file_has_both_header_literals(tree: ast.AST) -> bool:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            if lowered in _REQUIRED_HEADERS:
                found.add(lowered)
    return _REQUIRED_HEADERS.issubset(found)


def _find_run_transport(tree: ast.AST) -> str | None:
    """Return 'literal-web', 'literal-stdio', 'default-stdio', or 'runtime'.

    Returns None if no run() call or SDK transport construct is found at all.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        is_run_call = isinstance(node.func, ast.Attribute) and node.func.attr == "run"
        if is_run_call:
            for keyword in node.keywords:
                if keyword.arg != "transport":
                    continue
                if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                    value = keyword.value.value.lower()
                    if value in ("streamable-http", "http", "sse"):
                        return "literal-web"
                    return "literal-stdio"
                return "runtime"
            return "default-stdio"

        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in _SDK_STREAMABLE_HTTP_NAMES:
            return "literal-web"
    return None


def _has_web_framework_import(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in _WEB_FRAMEWORK_MODULES for alias in node.names):
                return True
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in _WEB_FRAMEWORK_MODULES:
                return True
    return False


def match(file_path: str, tree: ast.AST, source_lines: list[str]) -> list[int] | NeedsManualCheck:
    del file_path, source_lines

    endpoints = _find_handrolled_endpoints(tree)
    if endpoints:
        if _file_has_both_header_literals(tree):
            return []
        return sorted(node.lineno for node in endpoints)

    transport = _find_run_transport(tree)
    if transport in ("literal-web", "literal-stdio", "default-stdio"):
        return []
    if transport == "runtime":
        return NEEDS_MANUAL_CHECK

    if _has_web_framework_import(tree):
        return NEEDS_MANUAL_CHECK

    return []
