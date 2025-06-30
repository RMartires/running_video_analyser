import os
import logging
import requests
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Brevo API configuration
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

# Supabase configuration for signed URLs
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BUCKET = os.environ.get("SUPABASE_BUCKET", "running-form-analysis-input")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def send_processing_completion_email(
    user_email: str,
    video_name: str,
    output_file_url: str,
    processing_time: Optional[str] = None,
    metrics: Optional[dict] = None
) -> bool:
    """
    Send a processing completion email to the user using Brevo's Transactional Email API.
    
    Args:
        user_email: The recipient's email address
        video_name: Original video filename
        output_file_url: Public URL to the processed video
        processing_time: Optional processing duration string
        metrics: Optional dictionary containing analysis metrics
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    
    if not BREVO_API_KEY:
        logger.error("BREVO_API_KEY not found in environment variables")
        return False
    
    # Create email content
    subject = "Your Running Form Analysis is Ready! 🏃‍♂️"
    
    # Extract metrics for email template
    step_count = metrics.get('Step Count', 'N/A') if metrics else 'N/A'
    cadence = metrics.get('Cadence', 'N/A') if metrics else 'N/A'
    foot_strike = metrics.get('Foot Strike', 'N/A') if metrics else 'N/A'
    posture_angle = metrics.get('Posture Angle', 'N/A') if metrics else 'N/A'
    
    # Format posture angle if it's a number
    if isinstance(posture_angle, (int, float)):
        posture_angle = f"{posture_angle:.1f}°"
    
    # HTML email template
    html_content = f"""
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Running Analysis Results</title>
</head>
<body style="margin: 0; padding: 10px; font-family: Arial, sans-serif; background-color: #f5f5f5; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; color-scheme: light dark;">
    
    <!-- Main Container -->
    <div style="max-width: 600px; margin: 0 auto; background-color: #1a1a1a; color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: clamp(20px, 5vw, 40px) clamp(15px, 4vw, 30px); text-align: center; color: white;">
            <h1 style="margin: 0; font-size: clamp(24px, 5vw, 28px); font-weight: bold; color: #ffffff;">🏃‍♂️ Running Analysis Results</h1>
            <p style="margin: 10px 0 0 0; font-size: clamp(14px, 4vw, 16px); opacity: 0.9; color: #ffffff;">Your personalized running form analysis</p>
        </div>
        
        <!-- Content -->
        <div style="padding: clamp(15px, 4vw, 30px);">
            <p style="font-size: clamp(14px, 4vw, 16px); color: #ffffff; margin: 0 0 20px 0; line-height: 1.5;">
                Great job on your run! Here are your key metrics from our analysis:
            </p>
            
            <!-- Metrics Grid -->
            <div>
                <!-- Step Count -->
                <div style="background-color: rgba(59, 130, 246, 0.1); padding: clamp(15px, 4vw, 25px); border-radius: 8px; text-align: center; border-left: 4px solid #3b82f6; margin-bottom: 24px;">
                    <div style="color: #60a5fa; font-size: clamp(12px, 3.5vw, 14px); font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Step Count
                    </div>
                    <div style="font-size: clamp(28px, 6vw, 36px); font-weight: bold; color: #ffffff; margin-bottom: 5px;">
                        {step_count}
                    </div>
                    <div style="color: #9ca3af; font-size: clamp(12px, 3.5vw, 14px);">
                        total steps
                    </div>
                </div>
                <!-- Cadence -->
                <div style="background-color: rgba(16, 185, 129, 0.1); padding: clamp(15px, 4vw, 25px); border-radius: 8px; text-align: center; border-left: 4px solid #10b981; margin-bottom: 24px;">
                    <div style="color: #34d399; font-size: clamp(12px, 3.5vw, 14px); font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Cadence
                    </div>
                    <div style="font-size: clamp(28px, 6vw, 36px); font-weight: bold; color: #ffffff; margin-bottom: 5px;">
                        {cadence}
                    </div>
                    <div style="color: #9ca3af; font-size: clamp(12px, 3.5vw, 14px);">
                        steps per minute
                    </div>
                </div>
                <!-- Foot Strike -->
                <div style="background-color: rgba(245, 158, 11, 0.1); padding: clamp(15px, 4vw, 25px); border-radius: 8px; text-align: center; border-left: 4px solid #f59e0b; margin-bottom: 24px;">
                    <div style="color: #fbbf24; font-size: clamp(12px, 3.5vw, 14px); font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Foot Strike
                    </div>
                    <div style="font-size: clamp(24px, 5vw, 28px); font-weight: bold; color: #ffffff; margin-bottom: 5px;">
                        {foot_strike.title()}
                    </div>
                    <div style="color: #9ca3af; font-size: clamp(12px, 3.5vw, 14px);">
                        strike pattern
                    </div>
                </div>
                <!-- Posture Angle -->
                <div style="background-color: rgba(139, 92, 246, 0.1); padding: clamp(15px, 4vw, 25px); border-radius: 8px; text-align: center; border-left: 4px solid #8b5cf6;">
                    <div style="color: #a78bfa; font-size: clamp(12px, 3.5vw, 14px); font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Posture Angle
                    </div>
                    <div style="font-size: clamp(28px, 6vw, 36px); font-weight: bold; color: #ffffff; margin-bottom: 5px;">
                        {posture_angle}
                    </div>
                    <div style="color: #9ca3af; font-size: clamp(12px, 3.5vw, 14px);">
                        forward lean
                    </div>
                </div>
            </div>
            
            <!-- Analysis Summary -->
            <div style="background-color: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: clamp(15px, 4vw, 20px); border-radius: 0 8px 8px 0; margin-bottom: 20px; margin-top: 32px;">
                <p style="margin: 0; color: #34d399; font-size: clamp(13px, 3.8vw, 15px); line-height: 1.6;">
                    <strong>Analysis Summary:</strong> Your running form shows excellent cadence and good posture alignment. The {foot_strike} strike pattern is efficient and reduces impact stress.
                </p>
            </div>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin-bottom: 20px;">
                <a href="{output_file_url}" style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; text-decoration: none; padding: clamp(12px, 3vw, 15px) clamp(20px, 5vw, 30px); border-radius: 8px; font-size: clamp(14px, 4vw, 16px); font-weight: bold; width: auto; max-width: 100%; box-sizing: border-box;">
                    📹 View Detailed Analysis on Video
                </a>
            </div>
            
            <p style="text-align: center; color: #9ca3af; font-size: clamp(12px, 3.5vw, 14px); margin: 0;">
                Click above to see your detailed video analysis with visual annotations
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: clamp(15px, 4vw, 25px); text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.1);">
            <p style="margin: 0 0 10px 0; color: #9ca3af; font-size: clamp(14px, 4vw, 16px);">
                Keep up the great work! 🎉
            </p>
            <p style="margin: 0; color: #6b7280; font-size: clamp(11px, 3.2vw, 13px); line-height: 1.4;">
                This analysis was generated by your AI running coach.<br>
                Questions? Reply to this email for support.
            </p>
        </div>
        
    </div>
    
</body>
</html>
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
        "htmlContent": html_content
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
    Generate a signed URL for the processed video that expires in 1 week.
    Args:
        file_path: Path to the video file in storage (e.g., outputs/annotated_foo.mp4)
    Returns:
        str: Signed URL to the video
    """
    try:
        # 1 week = 604800 seconds
        result = supabase.storage.from_(BUCKET).create_signed_url(file_path, expires_in=604800)
        signed_url = result.get('signedURL') or result.get('signed_url')
        if not signed_url:
            logger.error(f"No signed URL returned for {file_path}: {result}")
            return ""
        return signed_url
    except Exception as e:
        logger.error(f"Failed to generate signed URL for {file_path}: {e}")
        return ""

if __name__ == "__main__":
    # Test the email functionality
    test_email = "test@example.com"
    test_video = "test_video.mp4"
    test_url = "https://example.com/video.mp4"
    
    success = send_processing_completion_email(test_email, test_video, test_url, "2 minutes 30 seconds")
    print(f"Email sent: {success}") 