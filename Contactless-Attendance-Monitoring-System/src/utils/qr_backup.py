"""
utils/qr_backup.py — QR Code backup attendance for failed face recognition.

Matches paper Section II-F:
  - Offered after MAX_FAILED_ATTEMPTS face recognition failures
  - QR Code is newly generated per request and valid for only 5 seconds
  - After expiry, the QR cannot be reused — prevents proxy attendance

Flow:
  1. Generate a time-limited token (HMAC-SHA256 of candidate_id + timestamp)
  2. Encode token into a QR code image
  3. Send QR to candidate's device (display on screen / send via email/SMS)
  4. Candidate scans QR within 5 seconds
  5. System verifies token freshness and marks attendance

Dependencies:
    pip3 install qrcode[pil] Pillow
"""

import os
import sys
import hmac
import hashlib
import time
import json
import base64
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import QR_VALIDITY_SECONDS

try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    print("[QR] qrcode library not installed. Run: pip3 install qrcode[pil]")

# Secret key for HMAC signing — change this in production
QR_SECRET = os.environ.get("QR_SECRET", "change_me_in_production")


def _sign_token(payload: dict) -> str:
    """HMAC-SHA256 sign a JSON payload."""
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    sig = hmac.new(QR_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(
        json.dumps({**payload, "sig": sig}).encode()
    ).decode()


def _verify_token(token_str: str) -> tuple:
    """
    Verify a QR token.

    Returns:
        (True,  candidate_id) if valid and not expired
        (False, reason_str)   otherwise
    """
    try:
        decoded  = base64.urlsafe_b64decode(token_str.encode()).decode()
        data     = json.loads(decoded)
        sig      = data.pop("sig")

        # Re-sign and compare
        payload_bytes = json.dumps(data, sort_keys=True).encode()
        expected_sig  = hmac.new(QR_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(sig, expected_sig):
            return False, "Invalid signature"

        # Check expiry
        age = time.time() - data["timestamp"]
        if age > QR_VALIDITY_SECONDS:
            return False, f"QR expired ({age:.1f}s > {QR_VALIDITY_SECONDS}s)"

        return True, data["candidate_id"]

    except Exception as e:
        return False, f"Token parse error: {e}"


def generate_qr(candidate_id: str, candidate_name: str):
    """
    Generate a time-limited QR code for the given candidate.

    Returns:
        (qr_image, token_str)  — PIL Image object and the raw token string
        or (None, None)        — if qrcode library not available
    """
    if not QR_AVAILABLE:
        return None, None

    token = _sign_token({
        "candidate_id": candidate_id,
        "name":         candidate_name,
        "timestamp":    time.time(),
    })

    qr = qrcode.QRCode(
        version          = 1,
        error_correction = qrcode.constants.ERROR_CORRECT_H,
        box_size         = 10,
        border           = 4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    print(f"[QR] Generated QR for {candidate_name} (valid {QR_VALIDITY_SECONDS}s)")
    return img, token


def verify_qr_scan(token_str: str) -> tuple:
    """
    Verify a scanned QR token.

    Returns:
        (True,  candidate_id, name) if valid
        (False, reason,       None) if invalid
    """
    valid, result = _verify_token(token_str)

    if valid:
        # result is candidate_id; we need to also decode name from token
        decoded = base64.urlsafe_b64decode(token_str.encode()).decode()
        data    = json.loads(decoded)
        return True, data["candidate_id"], data.get("name", "Unknown")
    else:
        return False, result, None


def display_qr_on_oled(qr_image):
    """
    Display the QR code on an OLED screen connected to the Raspberry Pi.
    Uses luma.oled library.

    This is optional — system works without OLED.
    pip3 install luma.oled luma.core
    """
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import ssd1306
        from luma.core.render import canvas

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial)

        # Resize QR image to fit OLED (128×64)
        qr_resized = qr_image.convert("L").resize((64, 64))

        with canvas(device) as draw:
            device.display(qr_resized.convert(device.mode))

        print("[QR] QR code displayed on OLED.")

    except ImportError:
        print("[QR] luma.oled not installed — OLED display skipped.")
    except Exception as e:
        print(f"[QR] OLED display failed: {e}")
