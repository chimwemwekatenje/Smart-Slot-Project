"""
PayChangu Payment Gateway Integration
Handles payment processing, verification, and webhook handling
"""
import requests
import hmac
import hashlib
from django.conf import settings
from django.utils.timezone import now
from .models import Payment


class PayChanguService:
    """Service for interacting with PayChangu payment gateway"""
    
    BASE_URL = "https://api.paychangu.com/payment/initiate"
    VERIFY_URL = "https://api.paychangu.com/payment/verify"
    
    @classmethod
    def get_credentials(cls):
        """Get PayChangu credentials from settings"""
        return {
            'public_key': settings.PAYCHANGU_PUBLIC_KEY,
            'secret_key': settings.PAYCHANGU_SECRET_KEY,
            'callback_url': settings.PAYCHANGU_CALLBACK_URL,
            'return_url': settings.PAYCHANGU_RETURN_URL,
        }
    
    @classmethod
    def initiate_payment(cls, booking, amount, email, phone):
        """
        Initiate a payment with PayChangu
        
        Args:
            booking: Booking object
            amount: Payment amount (decimal)
            email: Customer email
            phone: Customer phone number
            
        Returns:
            dict: Payment response with redirect URL and reference
        """
        if not settings.PAYCHANGU_PUBLIC_KEY:
            raise ValueError("PayChangu credentials not configured in .env")
        
        payload = {
            'amount': float(amount),
            'currency': 'KES',  # Default to KES, adjust as needed
            'email': email,
            'phone_number': phone,
            'merchant_public_key': settings.PAYCHANGU_PUBLIC_KEY,
            'tx_ref': f'booking-{booking.id}-{now().timestamp()}',
            'customization[title]': 'SmartSlot Booking Payment',
            'customization[description]': f'Payment for booking {booking.id}',
            'redirect_url': settings.PAYCHANGU_RETURN_URL,
            'callback_url': settings.PAYCHANGU_CALLBACK_URL,
        }
        
        try:
            response = requests.post(cls.BASE_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                return {
                    'success': True,
                    'redirect_url': data.get('data', {}).get('redirect_url'),
                    'reference': data.get('data', {}).get('id'),
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Payment initiation failed'),
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Payment gateway error: {str(e)}',
            }
    
    @classmethod
    def verify_payment(cls, reference):
        """
        Verify a payment with PayChangu
        
        Args:
            reference: PayChangu payment reference/ID
            
        Returns:
            dict: Verification response with payment status
        """
        if not settings.PAYCHANGU_SECRET_KEY:
            raise ValueError("PayChangu credentials not configured in .env")
        
        payload = {
            'merchant_public_key': settings.PAYCHANGU_PUBLIC_KEY,
            'id': reference,
        }
        
        try:
            response = requests.post(cls.VERIFY_URL, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('success'):
                payment_data = data.get('data', {})
                return {
                    'success': True,
                    'status': payment_data.get('status'),  # 'Completed', 'Pending', 'Failed'
                    'amount': payment_data.get('amount'),
                    'reference': payment_data.get('id'),
                }
            else:
                return {
                    'success': False,
                    'error': data.get('message', 'Payment verification failed'),
                }
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Payment gateway error: {str(e)}',
            }
    
    @classmethod
    def verify_webhook_signature(cls, payload, signature):
        """
        Verify PayChangu webhook signature for security
        
        Args:
            payload: Webhook payload (dict or JSON string)
            signature: HMAC signature from PayChangu
            
        Returns:
            bool: True if signature is valid
        """
        import json
        
        if isinstance(payload, dict):
            payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        else:
            payload_str = payload
        
        expected_signature = hmac.new(
            settings.PAYCHANGU_SECRET_KEY.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)


def create_payment(booking, amount):
    """
    Create a Payment record in the database
    
    Args:
        booking: Booking object
        amount: Payment amount
        
    Returns:
        Payment: Created Payment object
    """
    payment = Payment.objects.create(
        booking=booking,
        amount=amount,
        status=Payment.StatusChoices.PENDING,
    )
    return payment


def update_payment_status(reference, status, paychangu_ref=None):
    """
    Update payment status based on PayChangu webhook/verification
    
    Args:
        reference: Internal payment reference
        status: New status ('Success', 'Failed', etc.)
        paychangu_ref: PayChangu payment reference
    """
    try:
        payment = Payment.objects.get(id=reference)
        payment.status = status
        if paychangu_ref:
            payment.paychangu_reference = paychangu_ref
        payment.save()
        return payment
    except Payment.DoesNotExist:
        return None
