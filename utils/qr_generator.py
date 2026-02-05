# utils/qr_generator.py
import qrcode
from io import BytesIO
import base64

class QRGenerator:
    """Utility class for generating QR codes for payments"""
    
    @staticmethod
    def generate_upi_qr_code(upi_id, amount, payee_name="MapMarket", transaction_note=""):
        """
        Generate UPI QR code
        
        Args:
            upi_id: UPI ID of the merchant
            amount: Payment amount
            payee_name: Name of the payee
            transaction_note: Optional transaction note
            
        Returns:
            tuple: (upi_string, base64_image)
        """
        # Create UPI payment string
        upi_string = (
            f"upi://pay?"
            f"pa={upi_id}&"
            f"pn={payee_name}&"
            f"am={float(amount)}&"
            f"cu=INR"
        )
        
        if transaction_note:
            upi_string += f"&tn={transaction_note}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_string)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return upi_string, img_str
    
    @staticmethod
    def generate_generic_qr_code(data):
        """
        Generate a generic QR code from any data
        
        Args:
            data: String data to encode
            
        Returns:
            str: Base64 encoded QR code image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return img_str
