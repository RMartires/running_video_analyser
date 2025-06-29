import os
import logging
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Brevo API configuration
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

def send_processing_completion_email(
    user_email: str,
    video_name: str,
    output_file_url: str,
    processing_time: Optional[str] = None
) -> bool:
    """
    Send a processing completion email to the user using Brevo's Transactional Email API.
    
    Args:
        user_email: The recipient's email address
        video_name: Original video filename
        output_file_url: Public URL to the processed video
        processing_time: Optional processing duration string
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    if not BREVO_API_KEY:
        logger.error("BREVO_API_KEY not found in environment variables")
        return False
    
    # Create email content
    subject = "Your Running Form Analysis is Ready! 🏃‍♂️"
    
    # HTML email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Running Form Analysis Complete</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .container {{
                background-color: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .header h1 {{
                color: #2c3e50;
                margin-bottom: 10px;
            }}
            .success-icon {{
                font-size: 48px;
                color: #27ae60;
                margin-bottom: 20px;
            }}
            .content {{
                margin-bottom: 30px;
            }}
            .video-info {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .cta-button {{
                display: inline-block;
                background-color: #3498db;
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .cta-button:hover {{
                background-color: #2980b9;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #7f8c8d;
                font-size: 14px;
            }}
            .processing-time {{
                background-color: #e8f5e8;
                padding: 10px;
                border-radius: 5px;
                margin: 15px 0;
                border-left: 4px solid #27ae60;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="success-icon">✅</div>
                <h1>Your Analysis is Complete!</h1>
                <p>Great news! We've finished analyzing your running form video.</p>
            </div>
            
            <div class="content">
                <p>Hello!</p>
                
                <p>Your running form analysis has been successfully completed. We've processed your video and created a detailed analysis with posture angles, metrics, and visual overlays.</p>
                
                <div class="video-info">
                    <strong>Original Video:</strong> {video_name}<br>
                    <strong>Processed:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
                </div>
                
                {f'<div class="processing-time"><strong>Processing Time:</strong> {processing_time}</div>' if processing_time else ''}
                
                <p>Your annotated video is now ready for viewing. Click the button below to access your analysis:</p>
                
                <div style="text-align: center;">
                    <a href="{output_file_url}" class="cta-button">View Your Analysis Video</a>
                </div>
                
                <p><strong>What's included in your analysis:</strong></p>
                <ul>
                    <li>Posture angle measurements</li>
                    <li>Running form metrics</li>
                    <li>Visual skeleton overlay</li>
                    <li>Professional annotations</li>
                </ul>
                
                <p>If you have any questions about your analysis or need further assistance, please don't hesitate to reach out to our support team.</p>
            </div>
            
            <div class="footer">
                <p>Thank you for using our Running Form Analysis service!</p>
                <p>This is an automated message. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version for email clients that don't support HTML
    text_content = f"""
    Your Running Form Analysis is Ready!
    
    Hello!
    
    Your running form analysis has been successfully completed. We've processed your video and created a detailed analysis with posture angles, metrics, and visual overlays.
    
    Original Video: {video_name}
    Processed: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
    {f'Processing Time: {processing_time}' if processing_time else ''}
    
    Your annotated video is now ready for viewing. Access your analysis at:
    {output_file_url}
    
    What's included in your analysis:
    - Posture angle measurements
    - Running form metrics
    - Visual skeleton overlay
    - Professional annotations
    
    If you have any questions about your analysis or need further assistance, please don't hesitate to reach out to our support team.
    
    Thank you for using our Running Form Analysis service!
    
    This is an automated message. Please do not reply to this email.
    """
    
    # Prepare the email payload
    email_data = {
        "sender": {
            "name": "Running Form Analysis",
            "email": os.environ.get("SENDER_EMAIL", "noreply@runninganalysis.com")
        },
        "to": [
            {
                "email": user_email,
                "name": user_email.split('@')[0]  # Use email prefix as name
            }
        ],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text_content
    }
    
    # Send the email
    try:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": BREVO_API_KEY
        }
        
        response = requests.post(BREVO_API_URL, json=email_data, headers=headers)
        
        if response.status_code == 201:
            logger.info(f"Email sent successfully to {user_email}")
            return True
        else:
            logger.error(f"Failed to send email to {user_email}. Status: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending email to {user_email}: {e}")
        return False

def generate_video_url(file_path: str) -> str:
    """
    Generate a public URL for the processed video.
    This assumes you have a public bucket or can generate signed URLs.
    
    Args:
        file_path: Path to the video file in storage
        
    Returns:
        str: Public URL to the video
    """
    # For now, return a placeholder URL
    # You'll need to implement this based on your Supabase storage setup
    base_url = os.environ.get("SUPABASE_STORAGE_URL", "https://your-project.supabase.co/storage/v1/object/public")
    bucket_name = os.environ.get("SUPABASE_BUCKET", "running-form-analysis-input")
    
    return f"{base_url}/{bucket_name}/{file_path}"

if __name__ == "__main__":
    # Test the email functionality
    test_email = "test@example.com"
    test_video = "test_video.mp4"
    test_url = "https://example.com/video.mp4"
    
    success = send_processing_completion_email(test_email, test_video, test_url, "2 minutes 30 seconds")
    print(f"Email sent: {success}") 