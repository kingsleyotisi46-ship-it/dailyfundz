"""
Email notification utilities for DAILYFUNDZBOOST
"""
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """Send branded welcome email to new user with dark mode design"""
    try:
        from django.core.mail import EmailMultiAlternatives
        
        subject = 'Welcome to DAILYFUNDZBOOST! 🚀 Your SMM Partner'
        
        # Plain text fallback
        text_message = f"""
Hi {user.username}!

Welcome to DAILYFUNDZBOOST - Your Premium SMM & Digital Services Partner!

🎉 Your account is now active and ready to use!

What You Can Do:
✅ Buy Instagram followers, likes & views
✅ Boost TikTok engagement & growth
✅ Get YouTube views & subscribers
✅ Purchase virtual phone numbers
✅ Access 100+ social media services

Getting Started:
1. Add funds to your wallet via OPay
   Account: {getattr(settings, 'OPAY_ACCOUNT', '9070910294')}
   Name: DAILYFUNDZBOOST

2. Browse our affordable services

3. Place your first order and watch your growth!

Need Help?
💬 WhatsApp: {getattr(settings, 'COMPANY_WHATSAPP', '+2349073042472')}
📧 Email: support@dailyfundzboost.trade
🌐 Website: https://dailyfundzboost.trade

Thank you for choosing DAILYFUNDZBOOST!

Best regards,
The DAILYFUNDZBOOST Team
"""
        
        # Beautiful HTML version with dark mode
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0a0a0f; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #1a1a2e; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
                    
                    <!-- Header with gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); padding: 40px 20px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: 800; text-shadow: 0 2px 8px rgba(0,0,0,0.3); letter-spacing: -0.5px;">
                                💰 DAILYFUNDZBOOST
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #f0f0f0; font-size: 14px; opacity: 0.95; font-weight: 500;">
                                Premium SMM & Digital Services
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Welcome message -->
                    <tr>
                        <td style="padding: 40px 30px 30px 30px;">
                            <div style="text-align: center; margin-bottom: 30px;">
                                <div style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); padding: 12px 24px; border-radius: 50px; margin-bottom: 20px;">
                                    <span style="color: #ffffff; font-size: 18px; font-weight: 700;">🎉 Welcome Aboard!</span>
                                </div>
                            </div>
                            
                            <p style="color: #e0e0e0; font-size: 18px; line-height: 1.6; margin: 0 0 20px 0;">
                                Hi <strong style="color: #f093fb;">{user.username}</strong>!
                            </p>
                            
                            <p style="color: #b0b0b0; font-size: 16px; line-height: 1.8; margin: 0 0 30px 0;">
                                Your account is now <strong style="color: #4ade80;">active and ready</strong>! Start boosting your social media presence with our premium services.
                            </p>
                            
                            <!-- Services grid -->
                            <div style="background: #16213e; border-radius: 12px; padding: 24px; margin-bottom: 30px; border: 1px solid #2a2a4e;">
                                <h2 style="color: #ffffff; font-size: 20px; margin: 0 0 16px 0; font-weight: 700;">🚀 What You Can Do:</h2>
                                <table width="100%" border="0" cellspacing="0" cellpadding="8">
                                    <tr>
                                        <td style="color: #4ade80; font-size: 20px; width: 30px;">✓</td>
                                        <td style="color: #d0d0d0; font-size: 15px; line-height: 1.6;">Instagram followers, likes & views</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #4ade80; font-size: 20px;">✓</td>
                                        <td style="color: #d0d0d0; font-size: 15px; line-height: 1.6;">TikTok growth & engagement</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #4ade80; font-size: 20px;">✓</td>
                                        <td style="color: #d0d0d0; font-size: 15px; line-height: 1.6;">YouTube views & subscribers</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #4ade80; font-size: 20px;">✓</td>
                                        <td style="color: #d0d0d0; font-size: 15px; line-height: 1.6;">Virtual phone numbers</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #4ade80; font-size: 20px;">✓</td>
                                        <td style="color: #d0d0d0; font-size: 15px; line-height: 1.6;">100+ social media services</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Getting started -->
                            <div style="background: #16213e; border-radius: 12px; padding: 24px; margin-bottom: 30px; border: 1px solid #2a2a4e;">
                                <h2 style="color: #ffffff; font-size: 20px; margin: 0 0 20px 0; font-weight: 700;">📝 Getting Started:</h2>
                                
                                <div style="margin-bottom: 20px; padding-left: 10px; border-left: 3px solid #667eea;">
                                    <p style="color: #f093fb; font-size: 16px; font-weight: 600; margin: 0 0 8px 0;">Step 1: Add Funds</p>
                                    <p style="color: #b0b0b0; font-size: 14px; margin: 0 0 8px 0; line-height: 1.6;">
                                        Transfer to OPay:<br>
                                        <strong style="color: #4ade80;">9070910294</strong><br>
                                        <strong style="color: #ffffff;">DAILYFUNDZBOOST</strong>
                                    </p>
                                </div>
                                
                                <div style="margin-bottom: 20px; padding-left: 10px; border-left: 3px solid #667eea;">
                                    <p style="color: #f093fb; font-size: 16px; font-weight: 600; margin: 0 0 8px 0;">Step 2: Browse Services</p>
                                    <p style="color: #b0b0b0; font-size: 14px; margin: 0; line-height: 1.6;">
                                        Explore our affordable packages
                                    </p>
                                </div>
                                
                                <div style="padding-left: 10px; border-left: 3px solid #667eea;">
                                    <p style="color: #f093fb; font-size: 16px; font-weight: 600; margin: 0 0 8px 0;">Step 3: Place Order</p>
                                    <p style="color: #b0b0b0; font-size: 14px; margin: 0; line-height: 1.6;">
                                        Watch your growth begin!
                                    </p>
                                </div>
                            </div>
                            
                            <!-- CTA Button -->
                            <div style="text-align: center; margin: 40px 0 30px 0;">
                                <a href="https://dailyfundzboost.trade/login/" style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: #ffffff; text-decoration: none; padding: 16px 48px; border-radius: 50px; font-size: 18px; font-weight: 700; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4); transition: transform 0.2s;">
                                    🚀 Start Growing Now
                                </a>
                            </div>
                            
                            <!-- Support -->
                            <div style="background: #0f172a; border-radius: 12px; padding: 20px; text-align: center; border: 1px solid #1e293b;">
                                <p style="color: #ffffff; font-size: 16px; margin: 0 0 12px 0; font-weight: 600;">Need Help?</p>
                                <p style="color: #b0b0b0; font-size: 14px; margin: 0; line-height: 1.8;">
                                    💬 <strong style="color: #4ade80;">WhatsApp:</strong> +2349073042472<br>
                                    📧 <strong style="color: #4ade80;">Email:</strong> support@dailyfundzboost.trade<br>
                                    🌐 <strong style="color: #4ade80;">Website:</strong> dailyfundzboost.trade
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #0f0f1e; padding: 30px 20px; text-align: center; border-top: 1px solid #2a2a4e;">
                            <p style="color: #808080; font-size: 13px; margin: 0 0 8px 0; line-height: 1.6;">
                                Thank you for choosing <strong style="color: #f093fb;">DAILYFUNDZBOOST</strong>
                            </p>
                            <p style="color: #606060; font-size: 12px; margin: 0; line-height: 1.6;">
                                © 2026 DAILYFUNDZBOOST. All rights reserved.<br>
                                Your trusted SMM & digital services partner
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        # Send email with both text and HTML versions
        email = EmailMultiAlternatives(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=True)
        
        logger.info(f"Welcome email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")


def send_deposit_approved_email(deposit):
    """Send branded email when deposit is approved - dark mode design"""
    try:
        from django.core.mail import EmailMultiAlternatives
        
        user = deposit.user
        symbol = '₦' if deposit.currency == 'NGN' else '$'
        subject = f'✅ Deposit Approved! {symbol}{deposit.amount:,.0f} Added to Your Wallet'
        
        # Plain text fallback
        text_message = f"""
Hi {user.username}!

🎉 Great news! Your deposit has been approved and credited to your wallet.

💰 DEPOSIT DETAILS:
━━━━━━━━━━━━━━━━━
Amount: {symbol}{deposit.amount:,.0f}
Status: Approved ✅
Reference: DEP-{deposit.id}
Date: {deposit.created_at.strftime('%Y-%m-%d %H:%M')} UTC

Your funds are now ready to use! Start ordering and grow your social media presence.

Login now: https://dailyfundzboost.trade/login/

Thank you for using DAILYFUNDZBOOST!

Best regards,
The DAILYFUNDZBOOST Team
"""
        
        # Beautiful HTML version with dark mode
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0a0a0f; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #1a1a2e; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
                    
                    <!-- Header with gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 20px; text-align: center;">
                            <div style="font-size: 60px; margin-bottom: 10px;">✅</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; text-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                                Deposit Approved!
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #f0f0f0; font-size: 14px; opacity: 0.95; font-weight: 500;">
                                Your funds have been credited
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px 30px 30px;">
                            <p style="color: #e0e0e0; font-size: 18px; line-height: 1.6; margin: 0 0 30px 0;">
                                Hi <strong style="color: #10b981;">{user.username}</strong>!
                            </p>
                            
                            <p style="color: #b0b0b0; font-size: 16px; line-height: 1.8; margin: 0 0 30px 0;">
                                🎉 <strong style="color: #4ade80;">Great news!</strong> Your deposit has been approved and your wallet has been credited.
                            </p>
                            
                            <!-- Amount card -->
                            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); border-radius: 16px; padding: 30px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);">
                                <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin: 0 0 8px 0; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">
                                    Amount Credited
                                </p>
                                <p style="color: #ffffff; font-size: 48px; font-weight: 800; margin: 0; line-height: 1; text-shadow: 0 2px 8px rgba(0,0,0,0.2);">
                                    {symbol}{deposit.amount:,.0f}
                                </p>
                            </div>
                            
                            <!-- Details -->
                            <div style="background: #16213e; border-radius: 12px; padding: 24px; margin-bottom: 30px; border: 1px solid #2a2a4e;">
                                <h2 style="color: #ffffff; font-size: 18px; margin: 0 0 16px 0; font-weight: 700;">📋 Transaction Details</h2>
                                <table width="100%" border="0" cellspacing="0" cellpadding="10">
                                    <tr>
                                        <td style="color: #808080; font-size: 14px; padding: 8px 0;">Status:</td>
                                        <td align="right" style="padding: 8px 0;">
                                            <span style="background: #10b981; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                                                ✓ Approved
                                            </span>
                                        </td>
                                    </tr>
                                    <tr style="border-top: 1px solid #2a2a4e;">
                                        <td style="color: #808080; font-size: 14px; padding: 8px 0;">Reference:</td>
                                        <td align="right" style="color: #e0e0e0; font-size: 14px; font-weight: 600; padding: 8px 0;">DEP-{deposit.id}</td>
                                    </tr>
                                    <tr style="border-top: 1px solid #2a2a4e;">
                                        <td style="color: #808080; font-size: 14px; padding: 8px 0;">Date:</td>
                                        <td align="right" style="color: #e0e0e0; font-size: 14px; font-weight: 600; padding: 8px 0;">{deposit.created_at.strftime('%b %d, %Y %H:%M')}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- CTA -->
                            <div style="background: #0f172a; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #1e293b; margin-bottom: 20px;">
                                <p style="color: #e0e0e0; font-size: 16px; margin: 0 0 20px 0; line-height: 1.6;">
                                    Your funds are ready! Start boosting your social media now.
                                </p>
                                <a href="https://dailyfundzboost.trade/login/" style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: #ffffff; text-decoration: none; padding: 16px 48px; border-radius: 50px; font-size: 16px; font-weight: 700; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);">
                                    🚀 Start Ordering Now
                                </a>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #0f0f1e; padding: 30px 20px; text-align: center; border-top: 1px solid #2a2a4e;">
                            <p style="color: #808080; font-size: 13px; margin: 0 0 8px 0; line-height: 1.6;">
                                Thank you for using <strong style="color: #10b981;">DAILYFUNDZBOOST</strong>
                            </p>
                            <p style="color: #606060; font-size: 12px; margin: 0; line-height: 1.6;">
                                © 2026 DAILYFUNDZBOOST. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        # Send email with both text and HTML versions
        email = EmailMultiAlternatives(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=True)
        
        logger.info(f"Deposit approved email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send deposit approved email: {e}")


def send_deposit_rejected_email(deposit):
    """Send branded email when deposit is rejected - dark mode design"""
    try:
        from django.core.mail import EmailMultiAlternatives
        
        user = deposit.user
        symbol = '₦' if deposit.currency == 'NGN' else '$'
        subject = f'⚠️ Deposit Update Required - {symbol}{deposit.amount:,.0f}'
        
        # Plain text fallback
        text_message = f"""
Hi {user.username},

Your deposit request for {symbol}{deposit.amount:,.0f} could not be processed.

Reference: DEP-{deposit.id}
Reason: {deposit.admin_note or 'Payment not verified'}

What to do next:
1. Ensure you transferred to the correct OPay account: 9070910294
2. Account name should be: DAILYFUNDZBOOST
3. Upload a clear screenshot of your payment receipt
4. Try again or contact our support team

Need help?
💬 WhatsApp: +2349073042472
📧 Email: support@dailyfundzboost.trade

We're here to help!

Best regards,
DAILYFUNDZBOOST Team
"""
        
        # Beautiful HTML version with dark mode
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="dark">
    <meta name="supported-color-schemes" content="dark">
</head>
<body style="margin: 0; padding: 0; background-color: #0a0a0f; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;">
    <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #0a0a0f; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="100%" max-width="600" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px; background-color: #1a1a2e; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 40px 20px; text-align: center;">
                            <div style="font-size: 60px; margin-bottom: 10px;">⚠️</div>
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 800; text-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                                Action Required
                            </h1>
                            <p style="margin: 8px 0 0 0; color: #f0f0f0; font-size: 14px; opacity: 0.95; font-weight: 500;">
                                Deposit needs attention
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px 30px 30px;">
                            <p style="color: #e0e0e0; font-size: 18px; line-height: 1.6; margin: 0 0 20px 0;">
                                Hi <strong style="color: #f59e0b;">{user.username}</strong>,
                            </p>
                            
                            <p style="color: #b0b0b0; font-size: 16px; line-height: 1.8; margin: 0 0 30px 0;">
                                Your deposit request for <strong style="color: #ffffff;">{symbol}{deposit.amount:,.0f}</strong> could not be processed at this time.
                            </p>
                            
                            <!-- Details -->
                            <div style="background: #16213e; border-radius: 12px; padding: 24px; margin-bottom: 30px; border: 1px solid #2a2a4e;">
                                <h2 style="color: #ffffff; font-size: 18px; margin: 0 0 16px 0; font-weight: 700;">📋 Deposit Details</h2>
                                <table width="100%" border="0" cellspacing="0" cellpadding="10">
                                    <tr>
                                        <td style="color: #808080; font-size: 14px; padding: 8px 0;">Reference:</td>
                                        <td align="right" style="color: #e0e0e0; font-size: 14px; font-weight: 600; padding: 8px 0;">DEP-{deposit.id}</td>
                                    </tr>
                                    <tr style="border-top: 1px solid #2a2a4e;">
                                        <td style="color: #808080; font-size: 14px; padding: 8px 0;">Reason:</td>
                                        <td align="right" style="color: #f59e0b; font-size: 14px; font-weight: 600; padding: 8px 0;">{deposit.admin_note or 'Payment not verified'}</td>
                                    </tr>
                                </table>
                            </div>
                            
                            <!-- Action required -->
                            <div style="background: #0f172a; border-radius: 12px; padding: 24px; border: 1px solid #1e293b; margin-bottom: 30px;">
                                <h2 style="color: #ffffff; font-size: 18px; margin: 0 0 16px 0; font-weight: 700;">✅ What to Do Next:</h2>
                                
                                <div style="margin-bottom: 16px; padding-left: 10px; border-left: 3px solid #f59e0b;">
                                    <p style="color: #e0e0e0; font-size: 15px; margin: 0; line-height: 1.6;">
                                        <strong>1.</strong> Verify payment details<br>
                                        <span style="color: #808080; font-size: 13px;">Account: <strong style="color: #4ade80;">9070910294</strong><br>Name: <strong style="color: #ffffff;">DAILYFUNDZBOOST</strong></span>
                                    </p>
                                </div>
                                
                                <div style="margin-bottom: 16px; padding-left: 10px; border-left: 3px solid #f59e0b;">
                                    <p style="color: #e0e0e0; font-size: 15px; margin: 0; line-height: 1.6;">
                                        <strong>2.</strong> Upload clear payment screenshot
                                    </p>
                                </div>
                                
                                <div style="padding-left: 10px; border-left: 3px solid #f59e0b;">
                                    <p style="color: #e0e0e0; font-size: 15px; margin: 0; line-height: 1.6;">
                                        <strong>3.</strong> Submit again or contact support
                                    </p>
                                </div>
                            </div>
                            
                            <!-- Support -->
                            <div style="background: #16213e; border-radius: 12px; padding: 24px; text-align: center; border: 1px solid #2a2a4e;">
                                <p style="color: #ffffff; font-size: 16px; margin: 0 0 16px 0; font-weight: 600;">Need Help? We're Here! 💬</p>
                                <p style="color: #b0b0b0; font-size: 14px; margin: 0; line-height: 1.8;">
                                    <strong style="color: #4ade80;">WhatsApp:</strong> +2349073042472<br>
                                    <strong style="color: #4ade80;">Email:</strong> support@dailyfundzboost.trade
                                </p>
                                <div style="margin-top: 20px;">
                                    <a href="https://dailyfundzboost.trade/login/" style="display: inline-block; background: linear-gradient(135deg, #667eea, #764ba2); color: #ffffff; text-decoration: none; padding: 14px 36px; border-radius: 50px; font-size: 15px; font-weight: 700; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);">
                                        Try Again
                                    </a>
                                </div>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #0f0f1e; padding: 30px 20px; text-align: center; border-top: 1px solid #2a2a4e;">
                            <p style="color: #808080; font-size: 13px; margin: 0 0 8px 0; line-height: 1.6;">
                                <strong style="color: #f59e0b;">DAILYFUNDZBOOST</strong> - We're here to help
                            </p>
                            <p style="color: #606060; font-size: 12px; margin: 0; line-height: 1.6;">
                                © 2026 DAILYFUNDZBOOST. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        # Send email with both text and HTML versions
        email = EmailMultiAlternatives(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=True)
        
        logger.info(f"Deposit rejected email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send deposit rejected email: {e}")


def send_order_completed_email(order):
    """Send email when order is completed"""
    try:
        user = order.user
        subject = f'Order #{order.id} Completed! ✅'
        message = f"""
Hi {user.username}!

Your order has been completed successfully!

Order Details:
- Service: {order.service.name}
- Quantity: {order.quantity:,}
- Link: {order.link}
- Status: Completed ✅

Thank you for using DAILYFUNDZBOOST! Order again anytime.

Login: https://dailyfundzboost.onrender.com/login/

Best regards,
DAILYFUNDZBOOST Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        logger.info(f"Order completed email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send order completed email: {e}")


def send_referral_earning_email(referral, amount, currency='NGN'):
    """Send email when referral commission is earned"""
    try:
        user = referral.referrer
        symbol = '₦' if currency == 'NGN' else '$'
        subject = f'You earned {symbol}{amount} from referral! 💰'
        message = f"""
Hi {user.username}!

Great news! You just earned a referral commission!

Amount: {symbol}{amount}
From: {referral.referred.username}'s deposit
Commission Rate: {referral.commission_rate}%

Total Referral Earnings: {symbol}{referral.total_earned}

Keep sharing your referral link to earn more!
Your link: https://dailyfundzboost.onrender.com/register/?ref={referral.referral_code}

Best regards,
DAILYFUNDZBOOST Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        logger.info(f"Referral earning email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send referral earning email: {e}")


def send_password_reset_email(user, reset_url):
    """Send password reset email"""
    try:
        subject = f'Reset Your Password - {settings.COMPANY_NAME}'
        message = f"""
Hi {user.username}!

You requested to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request this, please ignore this email or contact support.

Need help? WhatsApp: {settings.COMPANY_WHATSAPP}

Best regards,
DAILYFUNDZBOOST Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return False


def send_ticket_reply_email(ticket, message_text, is_staff=True):
    """Send email when ticket receives a reply"""
    try:
        user = ticket.user
        sender = "Support Team" if is_staff else user.username
        subject = f'Reply to Ticket #{ticket.id}: {ticket.subject}'
        message = f"""
Hi {user.username}!

{'Our support team' if is_staff else 'You'} replied to your support ticket:

Ticket: #{ticket.id} - {ticket.subject}
Status: {ticket.get_status_display()}

Message:
{message_text}

{'You can reply to this ticket in your dashboard.' if is_staff else ''}

View ticket: https://dailyfundzboost.onrender.com/support/ticket/{ticket.id}/

Best regards,
DAILYFUNDZBOOST Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=True,
        )
        logger.info(f"Ticket reply email sent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to send ticket reply email: {e}")


# =============================================================================
# ADMIN NOTIFICATIONS - Sent to support@dailyfundzboost.trade
# =============================================================================

def get_admin_email():
    """Get admin notification email from settings"""
    return getattr(settings, 'ADMIN_NOTIFICATION_EMAIL', 'support@dailyfundzboost.trade')


def send_admin_new_deposit_notification(deposit):
    """
    Send email to admin when a new deposit is submitted.
    Admin receives this to know there's a pending payment to review.
    Includes one-click approve/reject buttons.
    """
    try:
        from django.conf import settings
        from django.core.mail import EmailMultiAlternatives
        
        user = deposit.user
        symbol = '₦' if deposit.currency == 'NGN' else '$'
        
        # Generate secure action tokens
        token = deposit.generate_action_token()
        base_url = getattr(settings, 'SITE_URL', 'https://dailyfundzboost.trade')
        approve_url = f"{base_url}/api/deposits/approve/{token}/"
        reject_url = f"{base_url}/api/deposits/reject/{token}/"
        admin_url = f"{base_url}/admin/social/deposit/{deposit.id}/change/"
        
        subject = f'🔔 NEW DEPOSIT: {symbol}{deposit.amount} from {user.username} - Action Required'
        
        # Plain text version
        text_message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔔 NEW DEPOSIT REQUEST - ACTION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A new deposit has been submitted and is waiting for your approval.

📋 DEPOSIT DETAILS:
━━━━━━━━━━━━━━━━━━━
• Deposit ID: #{deposit.id}
• Amount: {symbol}{deposit.amount:,.2f}
• Currency: {deposit.currency}
• Status: ⏳ PENDING

👤 USER DETAILS:
━━━━━━━━━━━━━━━━━
• Username: {user.username}
• Email: {user.email}
• User ID: {user.id}

📅 Submitted: {deposit.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

🔗 QUICK ACTIONS:
━━━━━━━━━━━━━━━━━━━
✅ Approve: {approve_url}
❌ Reject: {reject_url}

Or review in admin panel: {admin_url}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAILYFUNDZBOOST Admin Notification System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # HTML version with styled buttons
        html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
        <h1 style="margin: 0; font-size: 24px;">🔔 New Deposit Request</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px;">Action Required</p>
    </div>
    
    <div style="background: #f9f9f9; padding: 30px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 10px 10px;">
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #667eea;">
            <h2 style="margin-top: 0; color: #667eea; font-size: 18px;">📋 Deposit Details</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Deposit ID:</td>
                    <td style="padding: 8px 0;">#{deposit.id}</td>
                </tr>
                <tr style="background: #f5f5f5;">
                    <td style="padding: 8px 0; font-weight: bold;">Amount:</td>
                    <td style="padding: 8px 0; font-size: 20px; color: #28a745; font-weight: bold;">{symbol}{deposit.amount:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Currency:</td>
                    <td style="padding: 8px 0;">{deposit.currency}</td>
                </tr>
                <tr style="background: #f5f5f5;">
                    <td style="padding: 8px 0; font-weight: bold;">Status:</td>
                    <td style="padding: 8px 0;"><span style="background: #ffc107; color: #000; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">⏳ PENDING</span></td>
                </tr>
            </table>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745;">
            <h2 style="margin-top: 0; color: #28a745; font-size: 18px;">👤 User Details</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">Username:</td>
                    <td style="padding: 8px 0;">{user.username}</td>
                </tr>
                <tr style="background: #f5f5f5;">
                    <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                    <td style="padding: 8px 0;">{user.email}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; font-weight: bold;">User ID:</td>
                    <td style="padding: 8px 0;">#{user.id}</td>
                </tr>
                <tr style="background: #f5f5f5;">
                    <td style="padding: 8px 0; font-weight: bold;">Submitted:</td>
                    <td style="padding: 8px 0;">{deposit.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</td>
                </tr>
            </table>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <p style="margin-bottom: 20px; font-size: 16px; font-weight: bold; color: #333;">Choose an action:</p>
            
            <a href="{approve_url}" style="display: inline-block; background: #28a745; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin: 0 10px 10px 10px; box-shadow: 0 4px 6px rgba(40, 167, 69, 0.3);">
                ✅ APPROVE & RELEASE FUNDS
            </a>
            
            <a href="{reject_url}" style="display: inline-block; background: #dc3545; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px; margin: 0 10px 10px 10px; box-shadow: 0 4px 6px rgba(220, 53, 69, 0.3);">
                ❌ REJECT & CANCEL
            </a>
        </div>
        
        <div style="background: #e9ecef; padding: 15px; border-radius: 8px; margin-top: 20px; text-align: center;">
            <p style="margin: 5px 0; font-size: 14px; color: #666;">Or review the payment screenshot in the admin panel:</p>
            <a href="{admin_url}" style="color: #667eea; text-decoration: none; font-weight: bold;">View in Admin Panel →</a>
        </div>
        
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 12px;">
            <p style="margin: 5px 0;">DAILYFUNDZBOOST Admin Notification System</p>
            <p style="margin: 5px 0;">Links expire in 24 hours</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Send email with both text and HTML versions
        email = EmailMultiAlternatives(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [get_admin_email()],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=True)
        
        logger.info(f"Admin notification sent for deposit #{deposit.id}")
    except Exception as e:
        logger.error(f"Failed to send admin deposit notification: {e}")


def send_admin_new_user_notification(user):
    """
    Send email to admin when a new user registers.
    Admin receives user details for records.
    """
    try:
        subject = f'👤 NEW USER REGISTERED: {user.username}'
        message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 NEW USER REGISTRATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A new user has registered on DAILYFUNDZBOOST.

📋 USER DETAILS:
━━━━━━━━━━━━━━━━━
• Username: {user.username}
• Email: {user.email}
• User ID: {user.id}
• First Name: {user.first_name or 'Not provided'}
• Last Name: {user.last_name or 'Not provided'}

📅 Registered: {user.date_joined.strftime('%Y-%m-%d %H:%M:%S')} UTC

📊 QUICK STATS:
━━━━━━━━━━━━━━━━
Total Users: Check admin dashboard

🔗 VIEW USER:
━━━━━━━━━━━━━━
Admin Panel: https://dailyfundzboost.trade/admin/auth/user/{user.id}/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAILYFUNDZBOOST Admin Notification System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [get_admin_email()],
            fail_silently=True,
        )
        logger.info(f"Admin notification sent for new user: {user.username}")
    except Exception as e:
        logger.error(f"Failed to send admin new user notification: {e}")


def send_admin_new_ticket_notification(ticket):
    """
    Send email to admin when a new support ticket is created.
    """
    try:
        user = ticket.user
        subject = f'🎫 NEW SUPPORT TICKET: #{ticket.id} - {ticket.subject}'
        message = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎫 NEW SUPPORT TICKET - ACTION REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A new support ticket has been submitted.

📋 TICKET DETAILS:
━━━━━━━━━━━━━━━━━━━
• Ticket ID: #{ticket.id}
• Subject: {ticket.subject}
• Priority: {ticket.get_priority_display()}
• Status: {ticket.get_status_display()}

👤 FROM USER:
━━━━━━━━━━━━━━
• Username: {user.username}
• Email: {user.email}

💬 MESSAGE:
━━━━━━━━━━━━
{ticket.message[:500]}{'...' if len(ticket.message) > 500 else ''}

📅 Submitted: {ticket.created_at.strftime('%Y-%m-%d %H:%M:%S')} UTC

🔗 ACTION REQUIRED:
━━━━━━━━━━━━━━━━━━━
Admin Panel: https://dailyfundzboost.trade/admin/social/supportticket/{ticket.id}/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DAILYFUNDZBOOST Admin Notification System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [get_admin_email()],
            fail_silently=True,
        )
        logger.info(f"Admin notification sent for ticket #{ticket.id}")
    except Exception as e:
        logger.error(f"Failed to send admin ticket notification: {e}")
