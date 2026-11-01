"""打包课程项目：排除虚拟环境、缓存、数据库与临时预览文件。"""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "我的知识小栈-课程项目完整资料.zip"
PREFIX = "我的知识小栈"

EXCLUDED_DIRS = {
    ".venv", "venv", ".git", "__pycache__", ".pytest_cache", ".idea", ".vscode",
    "_ppt_assets", "instance", "node_modules",
}
EXCLUDED_FILES = {
    ".env", "demo.db", "verification.db",
    "admin-dashboard-preview.html",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log"}


def should_skip(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDED_DIRS:
        return True
    if any(part.startswith(".edge-") or part.startswith(".dsh-office-") for part in path.parts):
        return True
    if path.name in EXCLUDED_FILES:
        return True
    if path.suffix in EXCLUDED_SUFFIXES:
        return True
    if path.name.endswith(".zip"):
        return True
    return False


files: list[Path] = []
for path in ROOT.rglob("*"):
    if not path.is_file():
        continue
    relative = path.relative_to(ROOT)
    if should_skip(relative):
        continue
    files.append(path)

OUT.unlink(missing_ok=True)
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for path in sorted(files):
        relative = path.relative_to(ROOT)
        archive.write(path, (Path(PREFIX) / relative).as_posix())

print(f"saved: {OUT}")
print(f"files: {len(files)}")
print(f"size: {OUT.stat().st_size / 1024 / 1024:.2f} MB")
