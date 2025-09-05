#!/usr/bin/env python3
"""Test script for AWS SES email delivery"""

import os
import sys
import argparse
from datetime import datetime
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Add the project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ainewsbot.ses_delivery import SESDelivery
from ainewsbot.utilities import send_email, log


def test_ses_direct():
    """Test SES delivery directly"""
    print("\n=== Testing Direct SES Delivery ===")
    
    try:
        ses = SESDelivery()
        
        # Check quota first
        print("\nChecking SES quota...")
        quota = ses.get_send_quota()
        if quota:
            print(f"  Max 24-hour send: {quota.get('max_24_hour_send', 'N/A')}")
            print(f"  Sent last 24 hours: {quota.get('sent_last_24_hours', 'N/A')}")
            print(f"  Max send rate: {quota.get('max_send_rate', 'N/A')}")
        
        # Send test email
        subject = f"AInewsbot SES Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { background-color: #4CAF50; color: white; padding: 10px; }
                .content { padding: 20px; }
                .footer { background-color: #f1f1f1; padding: 10px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>AInewsbot SES Test Email</h1>
            </div>
            <div class="content">
                <h2>Test Successful!</h2>
                <p>This email was sent using AWS SES through the AInewsbot ses_delivery module.</p>
                <p>Timestamp: {}</p>
                <h3>Configuration:</h3>
                <ul>
                    <li>Sender: {}</li>
                    <li>Region: {}</li>
                    <li>Delivery Method: AWS SES</li>
                </ul>
            </div>
            <div class="footer">
                <p>AInewsbot - AI News Aggregator</p>
            </div>
        </body>
        </html>
        """.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ses.sender,
            ses.region
        )
        
        print(f"\nSending test email...")
        print(f"  From: {ses.sender}")
        print(f"  To: {ses.recipient}")
        print(f"  Subject: {subject}")
        
        result = ses.send_email(subject, html_content)
        
        if result['success']:
            print(f"\n✅ Email sent successfully!")
            print(f"  Message ID: {result['message_id']}")
            print(f"  Recipient: {result['recipient']}")
        else:
            print(f"\n❌ Failed to send email")
            print(f"  Error: {result.get('error_code', 'Unknown')}")
            print(f"  Message: {result.get('error_message', 'No details')}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error testing SES: {e}")
        return False
    
    return True


def test_send_email_wrapper(method='ses'):
    """Test the send_email wrapper function"""
    print(f"\n=== Testing send_email() with method='{method}' ===")
    
    # Temporarily set the delivery method
    original_method = os.environ.get('EMAIL_DELIVERY', 'ses')
    os.environ['EMAIL_DELIVERY'] = method
    
    try:
        subject = f"AInewsbot {method.upper()} Wrapper Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        html_content = f"""
        <html>
        <body>
            <h1>send_email() Wrapper Test</h1>
            <p>This email was sent using the send_email() wrapper with delivery method: {method}</p>
            <p>Timestamp: {datetime.now()}</p>
        </body>
        </html>
        """
        
        print(f"  Delivery method: {method}")
        print(f"  Subject: {subject}")
        
        success = send_email(subject, html_content)
        
        if success:
            print(f"✅ Email sent successfully using {method}")
            if method == 'file':
                print("  Check the 'out' directory for the saved email file")
        else:
            print(f"❌ Failed to send email using {method}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Restore original method
        os.environ['EMAIL_DELIVERY'] = original_method
    
    return True


def verify_email_address(email):
    """Verify an email address with SES (for sandbox mode)"""
    print(f"\n=== Verifying Email Address ===")
    print(f"  Email: {email}")
    
    try:
        ses = SESDelivery()
        if ses.verify_email_identity(email):
            print(f"✅ Verification email sent to {email}")
            print("  Please check your inbox and click the verification link")
            return True
        else:
            print(f"❌ Failed to send verification email")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Test AWS SES email delivery for AInewsbot')
    parser.add_argument('--verify', type=str, help='Email address to verify with SES')
    parser.add_argument('--method', type=str, default='ses', 
                        choices=['ses', 'gmail', 'file'],
                        help='Delivery method to test (default: ses)')
    parser.add_argument('--skip-direct', action='store_true',
                        help='Skip direct SES test')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("AInewsbot SES Email Delivery Test")
    print("=" * 50)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"  EMAIL_DELIVERY: {os.getenv('EMAIL_DELIVERY', 'not set (default: ses)')}")
    print(f"  AWS_REGION: {os.getenv('AWS_REGION', 'not set (default: us-east-1)')}")
    print(f"  SES_SENDER_EMAIL: {os.getenv('SES_SENDER_EMAIL', 'not set')}")
    print(f"  SES_RECIPIENT_EMAIL: {os.getenv('SES_RECIPIENT_EMAIL', 'not set')}")
    
    # Check for AWS credentials
    has_aws_creds = (
        os.getenv('AWS_ACCESS_KEY_ID') or
        os.path.exists(os.path.expanduser('~/.aws/credentials')) or
        os.getenv('AWS_PROFILE')
    )
    print(f"  AWS Credentials: {'✅ Found' if has_aws_creds else '❌ Not found'}")
    
    if args.verify:
        return verify_email_address(args.verify)
    
    all_passed = True
    
    # Test direct SES
    if not args.skip_direct and args.method == 'ses':
        if not test_ses_direct():
            all_passed = False
            print("\n⚠️  Direct SES test failed. Common issues:")
            print("  1. Email not verified in SES (check AWS Console)")
            print("  2. Account in sandbox mode (can only send to verified emails)")
            print("  3. AWS credentials not configured")
            print("  4. Wrong AWS region")
    
    # Test wrapper
    if not test_send_email_wrapper(args.method):
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())