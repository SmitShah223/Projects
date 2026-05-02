"""
utils/pdf_encrypt.py — AES-256 PDF encryption using MAC-address-derived key.

Encrypts the generated PDF so it can only be opened on the machine that
generated it. The encryption key is derived from the machine's MAC address
with a simple Caesar cipher shift (+3 on each character's ASCII value).

Usage:
    from utils.pdf_encrypt import encrypt_pdf, decrypt_pdf
    encrypt_pdf("output.pdf", "encrypted.pdf")
    decrypt_pdf("encrypted.pdf", "decrypted.pdf")
"""

import uuid
import sys
import os

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("Run: pip install pymupdf")


def get_mac_address() -> str:
    """Returns MAC address as a 12-char hex string with no colons."""
    mac = uuid.getnode()
    mac_str = ('%012X' % mac)
    return mac_str


def derive_key(mac: str) -> str:
    """
    Derive an encryption key from the MAC address using Caesar cipher (+3).
    Each character's ASCII value is shifted by 3.
    """
    return "".join(chr(ord(c) + 3) for c in mac)


def encrypt_pdf(input_path: str, output_path: str) -> str:
    """
    Encrypt a PDF with AES-256 using a MAC-address-derived key.
    The owner password is key + "o"; user password is key.
    Permissions: accessibility only (read-only, no copy/print).

    Returns the owner password (for decryption).
    """
    mac        = get_mac_address()
    key        = derive_key(mac)
    owner_pw   = key + "o"
    user_pw    = key

    doc = fitz.open(input_path)
    doc.save(
        output_path,
        owner_pw   = owner_pw,
        user_pw    = user_pw,
        encryption = fitz.PDF_ENCRYPT_AES_256,
        permissions= fitz.PDF_PERM_ACCESSIBILITY,
    )
    doc.close()
    print(f"[ENCRYPT] PDF encrypted → {output_path}")
    return owner_pw


def decrypt_pdf(encrypted_path: str, output_path: str) -> bool:
    """
    Decrypt an AES-256 encrypted PDF using the MAC-address-derived key.
    Saves a plain (unencrypted) copy to output_path.
    Returns True on success.
    """
    mac      = get_mac_address()
    key      = derive_key(mac)
    owner_pw = key + "o"

    doc = fitz.open(encrypted_path)

    if not doc.needs_pass:
        print("[DECRYPT] PDF is not password-protected.")
        doc.close()
        return False

    rc = doc.authenticate(owner_pw)
    if rc not in (1, 4, 6):
        print("[DECRYPT] Authentication failed — wrong machine or corrupted key.")
        doc.close()
        return False

    # Save without encryption
    doc.save(output_path, encryption=fitz.PDF_ENCRYPT_NONE)
    doc.close()
    print(f"[DECRYPT] PDF decrypted → {output_path}")
    return True


def read_encrypted_pdf(encrypted_path: str):
    """Print text content of each page in an encrypted PDF."""
    mac      = get_mac_address()
    key      = derive_key(mac)
    owner_pw = key + "o"

    doc = fitz.open(encrypted_path)
    if doc.needs_pass:
        rc = doc.authenticate(owner_pw)
        if rc not in (1, 4, 6):
            sys.exit("[DECRYPT] Bad owner password — cannot read PDF.")

    for i, page in enumerate(doc):
        print(f"\n--- Page {i + 1} ---")
        print(page.get_text())
    doc.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="PDF Encrypt/Decrypt utility")
    parser.add_argument("action",  choices=["encrypt", "decrypt", "read"])
    parser.add_argument("input",   help="Input PDF path")
    parser.add_argument("--output", default="output.pdf", help="Output PDF path")
    args = parser.parse_args()

    if args.action == "encrypt":
        encrypt_pdf(args.input, args.output)
    elif args.action == "decrypt":
        decrypt_pdf(args.input, args.output)
    elif args.action == "read":
        read_encrypted_pdf(args.input)
