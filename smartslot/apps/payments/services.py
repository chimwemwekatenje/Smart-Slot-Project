"""PayChangu payment integration for SmartSlot."""
import uuid
import hmac
import hashlib
import requests
from django.conf import settings

PAYCHANGU_API_URL      = 'https://api.paychangu.com/payment'
PAYCHANGU_VERIFY_URL   = 'https://api.paychangu.com/verify-payment'
PAYCHANGU_MOMO_URL     = 'https://api.paychangu.com/mobile-money'
PAYCHANGU_MOMO_OPS_URL = 'https://api.paychangu.com/mobile-money'

_AUTH_HEADERS = lambda: {
    "Accept":        "application/json",
    "Authorization": f"Bearer {settings.PAYCHANGU_SECRET_KEY}",
}


def initiate_payment(booking, customer_email, customer_first_name, customer_last_name):
    """
    Creates a PayChangu checkout session (redirect flow) for a booking.
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
        "meta": {"booking_id": str(booking.id)},
    }

    response = requests.post(
        PAYCHANGU_API_URL,
        json=payload,
        headers=_AUTH_HEADERS(),
        timeout=30,
    )
    data = response.json()

    if response.status_code == 200 and data.get('status') == 'success':
        return data['data']['checkout_url'], tx_ref

    raise Exception(data.get('message', 'PayChangu payment initiation failed.'))


def get_mobile_money_operators():
    """
    Returns list of supported mobile money operators from PayChangu.
    Each item has: id, name, ref_id, short_code.
    """
    response = requests.get(PAYCHANGU_MOMO_OPS_URL, headers=_AUTH_HEADERS(), timeout=15)
    data = response.json()
    if response.status_code == 200 and data.get('status') == 'success':
        return data.get('data', [])
    return []


def charge_mobile_money(booking, mobile_number, operator_ref_id,
                        first_name, last_name, email):
    """
    Initiates a direct mobile money charge (inline, no redirect).
    Returns the charge response data dict or raises an exception.
    """
    tx_ref = f"SMARTSLOT-{booking.id}-{uuid.uuid4().hex[:8].upper()}"

    payload = {
        "mobile":          mobile_number,          # e.g. "0991234567"
        "amount":          str(booking.resource.price),
        "currency":        "MWK",
        "operator":        operator_ref_id,        # ref_id from operators list
        "tx_ref":          tx_ref,
        "first_name":      first_name,
        "last_name":       last_name,
        "email":           email,
        "callback_url":    settings.PAYCHANGU_CALLBACK_URL,
        "meta": {"booking_id": str(booking.id)},
    }

    response = requests.post(
        PAYCHANGU_MOMO_URL,
        json=payload,
        headers=_AUTH_HEADERS(),
        timeout=30,
    )
    data = response.json()

    if response.status_code == 200 and data.get('status') in ('success', 'pending'):
        charge_data = data.get('data', {})
        charge_data['tx_ref'] = tx_ref
        return charge_data

    raise Exception(data.get('message', 'Mobile money charge failed.'))


def get_charge_details(charge_id):
    """
    Polls the status of a mobile money charge by charge_id.
    Returns the charge data dict or raises an exception.
    """
    response = requests.get(
        f"https://api.paychangu.com/mobile-money/payments/{charge_id}/details",
        headers=_AUTH_HEADERS(),
        timeout=15,
    )
    data = response.json()
    if response.status_code == 200 and data.get('status') == 'success':
        return data.get('data', {})
    raise Exception(data.get('message', 'Could not retrieve charge details.'))


def verify_payment(tx_ref):
    """
    Verifies a transaction with PayChangu server-side.
    Returns the transaction data dict or raises an exception.
    """
    response = requests.get(
        f"{PAYCHANGU_VERIFY_URL}/{tx_ref}",
        headers=_AUTH_HEADERS(),
        timeout=30,
    )
    data = response.json()
    if response.status_code == 200 and data.get('status') == 'success':
        return data['data']
    raise Exception(data.get('message', 'Payment verification failed.'))


def verify_webhook_signature(payload_body: bytes, signature: str) -> bool:
    """
    Verifies the HMAC-SHA512 signature PayChangu sends in X-Paychangu-Signature.
    """
    secret = settings.PAYCHANGU_SECRET_KEY.encode()
    expected = hmac.new(secret, payload_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(expected, signature or '')
