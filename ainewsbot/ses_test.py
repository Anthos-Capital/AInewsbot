"""AWS Lambda handler for testing SES email functionality"""
import json
import os
from datetime import datetime
from .ses_delivery import SESDelivery


def handler(event, context):
    """Lambda handler for SES email testing
    
    Args:
        event: Lambda event object
        context: Lambda context object
        
    Returns:
        dict: API Gateway response format
    """
    # Parse request if from API Gateway
    if 'body' in event:
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            body = {}
    else:
        body = event
    
    # Get parameters
    recipient = body.get('recipient', os.environ.get('SES_RECIPIENT_EMAIL'))
    subject = body.get('subject', f'SES Test - {datetime.now().isoformat()}')
    message = body.get('message', 'This is a test email from AInewsbot Lambda function')
    
    if not recipient:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Recipient email is required'})
        }
    
    # Create HTML content
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>AInewsbot SES Test</h2>
        <p>{message}</p>
        <hr>
        <p style="color: #666; font-size: 12px;">
            Sent from Lambda function: {context.function_name}<br>
            Stage: {os.environ.get('STAGE', 'unknown')}<br>
            Timestamp: {datetime.now().isoformat()}
        </p>
    </body>
    </html>
    """
    
    # Initialize SES and send email
    try:
        ses = SESDelivery(sender=os.environ.get('SES_SENDER_EMAIL'))
        result = ses.send_email(
            subject=subject,
            html_content=html_content,
            recipient=recipient
        )
        
        if result['success']:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': True,
                    'message': f'Email sent to {recipient}',
                    'messageId': result['message_id']
                })
            }
        else:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'success': False,
                    'error': result.get('error_message', 'Failed to send email')
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }