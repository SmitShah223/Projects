"""
utils/open_pdf.py — Cross-platform PDF opener.
Opens a PDF file with the system's default viewer (Preview on macOS,
Adobe/Edge on Windows, Evince/Okular on Linux).

Usage:
    python3 src/utils/open_pdf.py path/to/file.pdf
"""

import subprocess
import sys
import os


def open_pdf(file_path: str):
    """Open a PDF file with the OS default viewer."""
    if not os.path.exists(file_path):
        print(f"[OPEN] File not found: {file_path}")
        return

    if sys.platform.startswith("darwin"):       # macOS
        subprocess.call(["open", file_path])
    elif os.name == "nt":                        # Windows
        os.startfile(file_path)
    elif os.name == "posix":                     # Linux / Unix
        subprocess.call(["xdg-open", file_path])
    else:
        print("[OPEN] Unsupported platform.")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "output.pdf"
    open_pdf(path)
