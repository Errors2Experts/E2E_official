import base64
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from urllib.parse import urlencode

import qrcode
from django.conf import settings

TWO_PLACES = Decimal("0.01")


def normalize_payment_amount(amount):
    """
    Convert a backend-controlled payment amount to a positive
    Decimal with exactly two decimal places.
    """

    try:
        normalized = Decimal(str(amount)).quantize(
            TWO_PLACES,
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid payment amount.") from exc

    if normalized <= 0:
        raise ValueError("Payment amount must be greater than zero.")

    return normalized


def build_upi_payment_url(
    amount,
    note="Errors2Experts Payment",
):
    """
    Build a UPI payment URI.

    The amount must come from the Django backend.
    The browser never decides the payable amount.
    """

    upi_id = str(
        getattr(
            settings,
            "UPI_ID",
            "",
        )
    ).strip()

    payee_name = str(
        getattr(
            settings,
            "UPI_PAYEE_NAME",
            "Errors2Experts",
        )
    ).strip()

    if not upi_id:
        raise ValueError("UPI_ID is not configured.")

    normalized_amount = normalize_payment_amount(amount)

    clean_note = str(note or "Errors2Experts Payment").strip()

    params = {
        "pa": upi_id,
        "pn": payee_name,
        "am": f"{normalized_amount:.2f}",
        "cu": "INR",
        "tn": clean_note,
    }

    return "upi://pay?" + urlencode(params)


def generate_upi_qr_base64(
    amount,
    note="Errors2Experts Payment",
):
    """
    Generate a UPI QR dynamically and return a Base64 data URI
    ready to use directly in an HTML <img> element.

    The QR is generated in memory only.
    No QR image file is written to disk.
    """

    payment_url = build_upi_payment_url(
        amount=amount,
        note=note,
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=(qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=4,
    )

    qr.add_data(payment_url)

    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white",
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    encoded_qr = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return "data:image/png;base64," + encoded_qr
