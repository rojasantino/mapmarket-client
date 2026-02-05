# utils/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config
import os

class EmailService:
    """Email service for sending OTP and order notifications"""
    
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.from_name = os.environ.get('FROM_NAME', 'MapMarket')

    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send an email"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add text version (fallback)
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True, "Email sent successfully"
        except Exception as e:
            print(f"Email sending error: {e}")
            return False, str(e)

    def send_otp_email(self, to_email, otp_code, purpose="verification"):
        """Send OTP verification email"""
        subject = f"Your MapMarket Verification Code: {otp_code}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .otp-box {{ background: white; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
                .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 8px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>MapMarket</h1>
                    <p>Email Verification</p>
                </div>
                <div class="content">
                    <h2>Hello!</h2>
                    <p>Your verification code for {purpose} is:</p>
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                    </div>
                    <p><strong>This code will expire in 10 minutes.</strong></p>
                    <p>If you didn't request this code, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 MapMarket. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        MapMarket Email Verification
        
        Your verification code for {purpose} is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't request this code, please ignore this email.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_order_confirmation_email(self, to_email, order_number, total_amount, items):
        """Send order confirmation email"""
        subject = f"Order Confirmation - {order_number}"
        
        items_html = ""
        for item in items:
            items_html += f"""
            <tr>
                <td>{item.get('name', 'Product')}</td>
                <td>{item.get('quantity', 1)}</td>
                <td>₹{item.get('price', 0)}</td>
            </tr>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #667eea; color: white; }}
                .total {{ font-size: 20px; font-weight: bold; color: #667eea; text-align: right; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Order Confirmed!</h1>
                    <p>Order #{order_number}</p>
                </div>
                <div class="content">
                    <h2>Thank you for your order!</h2>
                    <p>Your order has been confirmed and will be processed shortly.</p>
                    <table>
                        <tr>
                            <th>Item</th>
                            <th>Quantity</th>
                            <th>Price</th>
                        </tr>
                        {items_html}
                    </table>
                    <div class="total">Total: ₹{total_amount}</div>
                    <p>You can track your order status in your account dashboard.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)

    def send_delivery_notification(self, to_email, order_number, delivery_otp, estimated_delivery):
        """Send delivery notification with OTP"""
        subject = f"Your Order is Out for Delivery - {order_number}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; }}
                .otp-box {{ background: white; border: 2px solid #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #667eea; letter-spacing: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚚 Out for Delivery!</h1>
                    <p>Order #{order_number}</p>
                </div>
                <div class="content">
                    <h2>Your order is on the way!</h2>
                    <p>Estimated delivery: <strong>{estimated_delivery}</strong></p>
                    <p>Please share this OTP with the delivery person to confirm delivery:</p>
                    <div class="otp-box">
                        <div class="otp-code">{delivery_otp}</div>
                    </div>
                    <p><strong>Important:</strong> Only share this OTP when you receive your order.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, html_content)
