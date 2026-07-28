# PyInstaller build spec for a standalone, single-file executable.
#
# Built per-OS (macOS, Linux, Windows) in .github/workflows/release.yml,
# one artifact per platform, attached to the GitHub Release. This is what
# lets a user download one file and run it directly - no Python install,
# no `pip install`, no cloning this repo.
#
# rules.toml is not a .py file, so PyInstaller's default analysis won't
# pick it up on its own - it's added explicitly via `datas` below, at the
# same relative path the package expects at runtime
# (mcp_migration_check/rules/rules.toml), so the engine's existing
# Path(__file__)-based lookup keeps working unchanged inside the bundle.
#
# Build locally with: pyinstaller mcp-migration-check.spec

a = Analysis(
    ["scripts/pyinstaller_entry.py"],
    pathex=["src"],
    binaries=[],
    datas=[("src/mcp_migration_check/rules/rules.toml", "mcp_migration_check/rules")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="mcp-migration-check",
    console=True,
)
