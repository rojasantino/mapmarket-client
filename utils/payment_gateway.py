# utils/payment_gateway.py
import os
import hmac
import hashlib
import razorpay
import stripe

class RazorpayGateway:
    """Razorpay payment gateway integration"""
    
    def __init__(self):
        self.key_id = os.environ.get('RAZORPAY_KEY_ID', '')
        self.key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
        self.client = razorpay.Client(auth=(self.key_id, self.key_secret))
    
    def create_order(self, amount, currency='INR', receipt=None, notes=None):
        """
        Create a Razorpay order
        
        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code
            receipt: Receipt ID for reference
            notes: Additional notes
            
        Returns:
            dict: Razorpay order details
        """
        try:
            order_data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': currency,
                'receipt': receipt or f'order_{int(os.urandom(4).hex(), 16)}',
                'notes': notes or {}
            }
            
            order = self.client.order.create(data=order_data)
            return True, order
        except Exception as e:
            return False, str(e)
    
    def verify_payment_signature(self, razorpay_order_id, razorpay_payment_id, razorpay_signature):
        """
        Verify Razorpay payment signature
        
        Args:
            razorpay_order_id: Order ID from Razorpay
            razorpay_payment_id: Payment ID from Razorpay
            razorpay_signature: Signature from Razorpay
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Generate signature
            message = f"{razorpay_order_id}|{razorpay_payment_id}"
            generated_signature = hmac.new(
                self.key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return generated_signature == razorpay_signature
        except Exception as e:
            print(f"Signature verification error: {e}")
            return False
    
    def fetch_payment(self, payment_id):
        """Fetch payment details"""
        try:
            payment = self.client.payment.fetch(payment_id)
            return True, payment
        except Exception as e:
            return False, str(e)
    
    def refund_payment(self, payment_id, amount=None):
        """
        Refund a payment
        
        Args:
            payment_id: Payment ID to refund
            amount: Amount to refund (None for full refund)
            
        Returns:
            tuple: (success, refund_data or error_message)
        """
        try:
            refund_data = {}
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = self.client.payment.refund(payment_id, refund_data)
            return True, refund
        except Exception as e:
            return False, str(e)


class StripeGateway:
    """Stripe payment gateway integration"""
    
    def __init__(self):
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
        self.publishable_key = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    
    def create_payment_intent(self, amount, currency='inr', metadata=None):
        """
        Create a Stripe payment intent
        
        Args:
            amount: Amount in smallest currency unit (paise for INR)
            currency: Currency code
            metadata: Additional metadata
            
        Returns:
            tuple: (success, payment_intent or error_message)
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to paise
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return True, intent
        except Exception as e:
            return False, str(e)
    
    def confirm_payment_intent(self, payment_intent_id):
        """Confirm a payment intent"""
        try:
            intent = stripe.PaymentIntent.confirm(payment_intent_id)
            return True, intent
        except Exception as e:
            return False, str(e)
    
    def retrieve_payment_intent(self, payment_intent_id):
        """Retrieve payment intent details"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return True, intent
        except Exception as e:
            return False, str(e)
    
    def create_refund(self, payment_intent_id, amount=None):
        """
        Create a refund
        
        Args:
            payment_intent_id: Payment intent ID
            amount: Amount to refund (None for full refund)
            
        Returns:
            tuple: (success, refund or error_message)
        """
        try:
            refund_data = {'payment_intent': payment_intent_id}
            if amount:
                refund_data['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_data)
            return True, refund
        except Exception as e:
            return False, str(e)
    
    def verify_webhook_signature(self, payload, sig_header, webhook_secret):
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Request body
            sig_header: Stripe-Signature header
            webhook_secret: Webhook secret from Stripe dashboard
            
        Returns:
            tuple: (success, event or error_message)
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return True, event
        except Exception as e:
            return False, str(e)
