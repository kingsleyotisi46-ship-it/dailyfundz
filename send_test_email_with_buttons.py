#!/usr/bin/env python
"""
Send test admin notification email with approve/reject buttons
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DAILYFUNDZBOOST.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from social.models import Deposit

# Get the test deposit
deposit = Deposit.objects.get(id=3)
user = deposit.user

# Generate secure token
token = deposit.generate_action_token()
base_url = "https://dailyfundzboost-cwo5.onrender.com"
approve_url = f"{base_url}/deposits/approve/{token}/"
reject_url = f"{base_url}/deposits/reject/{token}/"

subject = f"🔔 TEST: NEW DEPOSIT ₦500 from {user.username} - WITH BUTTONS!"

# HTML email with buttons
html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f4f4f4;">
    <div style="max-width: 600px; margin: 20px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center;">
            <h1 style="margin: 0; font-size: 28px;">🔔 New Deposit Request</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Action Required</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 30px;">
            
            <!-- Deposit Details Card -->
            <div style="background: #f8f9fa; border-left: 4px solid #667eea; border-radius: 8px; padding: 20px; margin-bottom: 25px;">
                <h2 style="margin: 0 0 15px 0; color: #667eea; font-size: 18px;">📋 Deposit Details</h2>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px 0; font-weight: bold; color: #666;">Deposit ID:</td>
                        <td style="padding: 10px 0; text-align: right;">#{deposit.id}</td>
                    </tr>
                    <tr style="background: #fff; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px 0; font-weight: bold; color: #666;">Amount:</td>
                        <td style="padding: 10px 0; text-align: right;">
                            <span style="font-size: 28px; color: #28a745; font-weight: bold;">₦500</span>
                        </td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px 0; font-weight: bold; color: #666;">User:</td>
                        <td style="padding: 10px 0; text-align: right;">{user.username}</td>
                    </tr>
                    <tr style="background: #fff; border-bottom: 1px solid #e0e0e0;">
                        <td style="padding: 10px 0; font-weight: bold; color: #666;">Email:</td>
                        <td style="padding: 10px 0; text-align: right; font-size: 13px;">{user.email}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px 0; font-weight: bold; color: #666;">Status:</td>
                        <td style="padding: 10px 0; text-align: right;">
                            <span style="background: #ffc107; color: #000; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                                ⏳ PENDING
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Action Buttons -->
            <div style="text-align: center; margin: 40px 0 30px 0;">
                <p style="margin-bottom: 25px; font-size: 18px; font-weight: bold; color: #333;">Choose an action:</p>
                
                <!-- Approve Button -->
                <a href="{approve_url}" 
                   style="display: inline-block; 
                          background: #28a745; 
                          color: white; 
                          padding: 18px 45px; 
                          text-decoration: none; 
                          border-radius: 10px; 
                          font-weight: bold; 
                          font-size: 16px; 
                          margin: 10px; 
                          box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
                          transition: all 0.3s;">
                    ✅ APPROVE & RELEASE FUNDS
                </a>
                
                <br>
                
                <!-- Reject Button -->
                <a href="{reject_url}" 
                   style="display: inline-block; 
                          background: #dc3545; 
                          color: white; 
                          padding: 18px 45px; 
                          text-decoration: none; 
                          border-radius: 10px; 
                          font-weight: bold; 
                          font-size: 16px; 
                          margin: 10px; 
                          box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
                          transition: all 0.3s;">
                    ❌ REJECT & CANCEL
                </a>
            </div>
            
            <!-- Note -->
            <div style="background: #e9ecef; border-radius: 8px; padding: 15px; margin-top: 25px; text-align: center;">
                <p style="margin: 5px 0; font-size: 14px; color: #666;">
                    💡 Click a button above to approve or reject this deposit instantly
                </p>
                <p style="margin: 5px 0; font-size: 12px; color: #999;">
                    Links expire in 24 hours for security
                </p>
            </div>
            
        </div>
        
        <!-- Footer -->
        <div style="background: #f8f9fa; padding: 20px; text-align: center; border-top: 1px solid #e0e0e0;">
            <p style="margin: 5px 0; font-size: 12px; color: #999;">DAILYFUNDZBOOST Admin Notification System</p>
            <p style="margin: 5px 0; font-size: 11px; color: #999;">This is a test email with working buttons</p>
        </div>
        
    </div>
</body>
</html>
"""

# Plain text version
text_message = f"""
NEW DEPOSIT REQUEST - ACTION REQUIRED

Deposit ID: #{deposit.id}
Amount: ₦500
User: {user.username} ({user.email})
Status: PENDING

QUICK ACTIONS:
Approve: {approve_url}
Reject: {reject_url}

Links expire in 24 hours.
"""

# Send email
print(f"Sending email to: support@dailyfundzboost.trade")
print(f"Subject: {subject}")

email = EmailMultiAlternatives(
    subject,
    text_message,
    settings.DEFAULT_FROM_EMAIL,
    ['support@dailyfundzboost.trade'],
)
email.attach_alternative(html_message, "text/html")
email.send()

print("\n✅ EMAIL SENT SUCCESSFULLY!")
print(f"\nApprove URL: {approve_url}")
print(f"Reject URL: {reject_url}")
print("\n🎯 Check your inbox at: support@dailyfundzboost.trade")
