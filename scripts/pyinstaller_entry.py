"""Entry script for the PyInstaller standalone-binary build.

PyInstaller needs a plain script to analyze, not just an installed
package's console-script entry point. This just calls the real one.
See mcp-migration-check.spec and .github/workflows/release.yml.
"""

from mcp_migration_check.cli import main

if __name__ == "__main__":
    main()
