"""The matcher registry: one explicit table, rule id -> matcher function.

See docs/low-level-design/001-rule-definition-format.md section 3. Adding a
rule touches exactly three places, all here in rule territory: a new
section in rules.toml, a new matcher module, and one new line below.
"""

from __future__ import annotations

from mcp_migration_check.rules import (
    r1_session_usage,
    r2_session_keyed_memory,
    r3_required_headers,
    r4_phased_out_capabilities,
    r5_error_numbers,
    r6_sse_resumability,
    r7_old_subscribe_handlers,
    r8_old_logging_set_level_handler,
)

REGISTRY = {
    "R1": r1_session_usage.match,
    "R2": r2_session_keyed_memory.match,
    "R3": r3_required_headers.match,
    "R4": r4_phased_out_capabilities.match,
    "R5": r5_error_numbers.match,
    "R6": r6_sse_resumability.match,
    "R7": r7_old_subscribe_handlers.match,
    "R8": r8_old_logging_set_level_handler.match,
}
