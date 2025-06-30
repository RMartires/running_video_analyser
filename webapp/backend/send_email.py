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
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Running Analysis Results</title>
</head>
<body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background-color: #f5f5f5;">
    
    <!-- Main Container -->
    <div style="max-width: 600px; margin: 0 auto; background-color: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #4f46e5, #7c3aed); padding: 40px 30px; text-align: center; color: white;">
            <h1 style="margin: 0; font-size: 28px; font-weight: bold;">🏃‍♂️ Running Analysis Results</h1>
            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Your personalized running form analysis</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 30px;">
            <p style="font-size: 16px; color: #333; margin: 0 0 30px 0; line-height: 1.5;">
                Great job on your run! Here are your key metrics from our analysis:
            </p>
            
            <!-- Metrics Grid -->
            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 30px;">
                
                <!-- Step Count -->
                <div style="flex: 1; min-width: 250px; background-color: #f8fafc; padding: 25px; border-radius: 8px; text-align: center; border-left: 4px solid #3b82f6;">
                    <div style="color: #3b82f6; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Step Count
                    </div>
                    <div style="font-size: 36px; font-weight: bold; color: #1e293b; margin-bottom: 5px;">
                        2,847
                    </div>
                    <div style="color: #64748b; font-size: 14px;">
                        total steps
                    </div>
                </div>
                
                <!-- Cadence -->
                <div style="flex: 1; min-width: 250px; background-color: #f8fafc; padding: 25px; border-radius: 8px; text-align: center; border-left: 4px solid #10b981;">
                    <div style="color: #10b981; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Cadence
                    </div>
                    <div style="font-size: 36px; font-weight: bold; color: #1e293b; margin-bottom: 5px;">
                        172
                    </div>
                    <div style="color: #64748b; font-size: 14px;">
                        steps per minute
                    </div>
                </div>
                
            </div>
            
            <div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 30px;">
                
                <!-- Foot Strike -->
                <div style="flex: 1; min-width: 250px; background-color: #f8fafc; padding: 25px; border-radius: 8px; text-align: center; border-left: 4px solid #f59e0b;">
                    <div style="color: #f59e0b; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Foot Strike
                    </div>
                    <div style="font-size: 28px; font-weight: bold; color: #1e293b; margin-bottom: 5px;">
                        Midfoot
                    </div>
                    <div style="color: #64748b; font-size: 14px;">
                        strike pattern
                    </div>
                </div>
                
                <!-- Posture Angle -->
                <div style="flex: 1; min-width: 250px; background-color: #f8fafc; padding: 25px; border-radius: 8px; text-align: center; border-left: 4px solid #8b5cf6;">
                    <div style="color: #8b5cf6; font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 8px;">
                        Posture Angle
                    </div>
                    <div style="font-size: 36px; font-weight: bold; color: #1e293b; margin-bottom: 5px;">
                        5.2°
                    </div>
                    <div style="color: #64748b; font-size: 14px;">
                        forward lean
                    </div>
                </div>
                
            </div>
            
            <!-- Analysis Summary -->
            <div style="background-color: #ecfdf5; border-left: 4px solid #10b981; padding: 20px; border-radius: 0 8px 8px 0; margin-bottom: 30px;">
                <p style="margin: 0; color: #065f46; font-size: 15px; line-height: 1.6;">
                    <strong>Analysis Summary:</strong> Your running form shows excellent cadence and good posture alignment. The midfoot strike pattern is efficient and reduces impact stress.
                </p>
            </div>
            
            <!-- CTA Button -->
            <div style="text-align: center; margin-bottom: 20px;">
                <a href="{output_file_url}" style="display: inline-block; background: linear-gradient(135deg, #4f46e5, #7c3aed); color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; font-size: 16px; font-weight: bold;">
                    📹 View Detailed Analysis on Video
                </a>
            </div>
            
            <p style="text-align: center; color: #64748b; font-size: 14px; margin: 0;">
                Click above to see your detailed video analysis with visual annotations
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 25px; text-align: center; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 10px 0; color: #64748b; font-size: 16px;">
                Keep up the great work! 🎉
            </p>
            <p style="margin: 0; color: #94a3b8; font-size: 13px; line-height: 1.4;">
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
    Generate a public URL for the processed video.
    This assumes you have a public bucket or can generate signed URLs.
    
    Args:
        file_path: Path to the video file in storage
        
    Returns:
        str: Public URL to the video
    """
    # For now, return a placeholder URL
    # You'll need to implement this based on your Supabase storage setup
    base_url = os.environ.get("SUPABASE_URL", "https://your-project.supabase.co/storage/v1/object/public")
    bucket_name = os.environ.get("SUPABASE_BUCKET", "running-form-analysis-input")
    
    return f"{base_url}/{bucket_name}/{file_path}"

if __name__ == "__main__":
    # Test the email functionality
    test_email = "test@example.com"
    test_video = "test_video.mp4"
    test_url = "https://example.com/video.mp4"
    
    success = send_processing_completion_email(test_email, test_video, test_url, "2 minutes 30 seconds")
    print(f"Email sent: {success}") 