"""AWS SES email delivery module for AInewsbot"""
import os
import re
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, Dict, Any
from .utilities import log


class SESDelivery:
    """AWS SES email delivery handler"""
    
    def __init__(self, sender: Optional[str] = None, region: str = None):
        """Initialize SES client
        
        Args:
            sender: Override sender email (defaults to env var)
            region: AWS region for SES (defaults to env var or us-east-1)
        """
        # Get region from env or default
        self.region = region or os.getenv('AWS_REGION', 'us-east-1')
        
        try:
            self.ses_client = boto3.client('ses', region_name=self.region)
        except NoCredentialsError:
            log("ERROR: AWS credentials not found. Please configure AWS credentials.")
            raise
        
        # Get sender and recipient from environment
        self.sender = sender or os.getenv('SES_SENDER_EMAIL', 'noreply@yourdomain.com')
        self.recipient = os.getenv('SES_RECIPIENT_EMAIL', self.sender)
        
        log(f"SES initialized with sender: {self.sender}, region: {self.region}")
        
    def send_email(self, 
                   subject: str, 
                   html_content: str, 
                   text_content: Optional[str] = None,
                   recipient: Optional[str] = None) -> Dict[str, Any]:
        """Send email using AWS SES
        
        Args:
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional, will be generated from HTML if not provided)
            recipient: Override recipient email (optional)
        
        Returns:
            dict: Response with success status and message ID or error
        """
        # Use provided recipient or default
        to_address = recipient or self.recipient
        
        # Generate text content from HTML if not provided
        if not text_content:
            # Simple HTML stripping (remove tags and decode entities)
            text_content = re.sub('<[^<]+?>', '', html_content)
            text_content = text_content.replace('&nbsp;', ' ')
            text_content = text_content.replace('&amp;', '&')
            text_content = text_content.replace('&lt;', '<')
            text_content = text_content.replace('&gt;', '>')
            text_content = text_content.replace('&quot;', '"')
            text_content = text_content.replace('&#39;', "'")
        
        try:
            response = self.ses_client.send_email(
                Source=self.sender,
                Destination={
                    'ToAddresses': [to_address],
                    'CcAddresses': [],
                    'BccAddresses': []
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_content,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_content,
                            'Charset': 'UTF-8'
                        }
                    }
                },
                # Optional: Add configuration set for tracking
                # ConfigurationSetName='your-config-set-name'
            )
            
            message_id = response['MessageId']
            log(f"Email sent successfully to {to_address}. MessageId: {message_id}")
            
            return {
                'success': True,
                'message_id': message_id,
                'recipient': to_address
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            
            # Provide helpful error messages
            if error_code == 'MessageRejected':
                log(f"ERROR: Email rejected by SES: {error_msg}")
                log("Check if your email content violates SES policies")
            elif error_code == 'MailFromDomainNotVerified':
                log(f"ERROR: Sender domain/email not verified: {self.sender}")
                log("Please verify the sender in AWS SES console")
            elif error_code == 'ConfigurationSetDoesNotExist':
                log(f"ERROR: Configuration set not found: {error_msg}")
            elif error_code == 'AccountSendingPausedException':
                log("ERROR: Account sending is paused. Check AWS SES console")
            elif error_code == 'AccountSuspended':
                log("ERROR: AWS SES account is suspended")
            else:
                log(f"ERROR: SES error ({error_code}): {error_msg}")
            
            return {
                'success': False,
                'error_code': error_code,
                'error_message': error_msg
            }
            
        except Exception as e:
            log(f"ERROR: Unexpected error sending email: {str(e)}")
            return {
                'success': False,
                'error_code': 'UnexpectedError',
                'error_message': str(e)
            }
    
    def verify_email_identity(self, email_address: str) -> bool:
        """Verify an email address with SES (for sandbox mode)
        
        Args:
            email_address: Email to verify
            
        Returns:
            bool: Success status
        """
        try:
            self.ses_client.verify_email_identity(EmailAddress=email_address)
            log(f"Verification email sent to {email_address}")
            return True
        except ClientError as e:
            log(f"ERROR verifying email: {e.response['Error']['Message']}")
            return False
    
    def get_send_quota(self) -> Dict[str, Any]:
        """Get current SES sending quota
        
        Returns:
            dict: Quota information
        """
        try:
            response = self.ses_client.get_send_quota()
            return {
                'max_24_hour_send': response.get('Max24HourSend', 0),
                'sent_last_24_hours': response.get('SentLast24Hours', 0),
                'max_send_rate': response.get('MaxSendRate', 0)
            }
        except ClientError as e:
            log(f"ERROR getting send quota: {e.response['Error']['Message']}")
            return {}


# Backward compatibility wrapper
def send_ses(subject: str, html_str: str) -> bool:
    """Drop-in replacement for send_gmail()
    
    Args:
        subject: Email subject
        html_str: HTML content
        
    Returns:
        bool: Success status
    """
    try:
        delivery = SESDelivery()
        result = delivery.send_email(subject, html_str)
        return result['success']
    except Exception as e:
        log(f"ERROR in send_ses wrapper: {str(e)}")
        return False