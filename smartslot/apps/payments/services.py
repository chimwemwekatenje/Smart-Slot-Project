"""PayChangu payment integration for SmartSlot."""
import uuid
import hmac
import hashlib
import requests
from django.conf import settings

PAYCHANGU_API_URL    = 'https://api.paychangu.com/payment'
PAYCHANGU_VERIFY_URL = 'https://api.paychangu.com/verify-payment'


def initiate_payment(booking, customer_email, customer_first_name, customer_last_name):
    """
    Creates a PayChangu checkout session for a booking.
    Returns (checkout_url, tx_ref) on success or raises an exception.
    """
    tx_ref = f"SMARTSLOT-{booking.id}-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "amount":      str(booking.resource.price),
        "currency":    "MWK",
        "email":       customer_email,
        "first_name":  customer_first_name,
        "last_name":   customer_last_name,
        "callback_url": settings.PAYCHANGU_CALLBACK_URL,
        "return_url":   settings.PAYCHANGU_RETURN_URL,
        "tx_ref":       tx_ref,
        "customization": {
            "title":       "SmartSlot Booking",
            "description": f"Booking for {booking.resource.name} at {booking.organisation.name}",
        },
        "meta": {
            "booking_id": str(booking.id),
        },
    }

    response = requests.post(
        PAYCHANGU_API_URL,
        json=payload,
        headers={
            "Accept":        "application/json",
            "Authorization": f"Bearer {settings.PAYCHANGU_SECRET_KEY}",
        },
        timeout=30,
    )

    data = response.json()

    if response.status_code == 200 and data.get('status') == 'success':
        checkout_url = data['data']['checkout_url']
        return checkout_url, tx_ref

    raise Exception(data.get('message', 'PayChangu payment initiation failed.'))


def verify_payment(tx_ref):
    """
    Verifies a transaction with PayChangu server-side.
    Returns the transaction data dict or raises an exception.
    """
    response = requests.get(
        f"{PAYCHANGU_VERIFY_URL}/{tx_ref}",
        headers={
            "Accept":        "application/json",
            "Authorization": f"Bearer {settings.PAYCHANGU_SECRET_KEY}",
        },
        timeout=30,
    )

    data = response.json()

    if response.status_code == 200 and data.get('status') == 'success':
        return data['data']

    raise Exception(data.get('message', 'Payment verification failed.'))


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verifies the HMAC-SHA512 signature PayChangu sends in the
    X-Paychangu-Signature header.
    Returns True if valid, False otherwise.
    """
    secret = settings.PAYCHANGU_SECRET_KEY.encode()
    expected = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature or '')
