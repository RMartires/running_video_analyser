import os
import logging
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import subprocess
from enum import Enum
import time
from send_email import send_processing_completion_email, generate_video_url
import sys

# Add the parent directory to the path to import the annotation script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from annotate_with_opencv_pillow import annotate_and_process

# Load environment variables
load_dotenv()

# Processing status enum
class ProcessingStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BUCKET = os.environ.get("SUPABASE_BUCKET", "running-form-analysis-input")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def process_video_submission(file_name: str) -> tuple[str, dict]:
    """
    Process a single video submission using the same logic as the main controller.
    Returns a tuple of (output_file_path, final_metrics) on success.
    """
    local_input = f"./temp/{os.path.basename(file_name)}"
    local_output = f"./temp/annotated_{os.path.basename(file_name)}"
    output_file = f"outputs/annotated_{os.path.basename(file_name)}"

    logger.info(f"Processing video: {file_name}")

    # 1. Download from Supabase Storage
    try:
        res = supabase.storage.from_(BUCKET).download(file_name)
        with open(local_input, "wb") as f:
            f.write(res)
        logger.info(f"Downloaded video to: {local_input}")
    except Exception as e:
        logger.error(f"Failed to download video {file_name}: {e}")
        raise

    # 2. Run annotation script
    try:
        # Use a system font for the annotation
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        if not os.path.exists(font_path):
            logger.warning(f"Font file not found: {font_path}, using default")
            font_path = None
        
        # Call the annotation and post-processing function directly
        final_metrics = annotate_and_process(local_input, local_output, font_path)
        
        # Ensure final_metrics is a dictionary
        if final_metrics is None:
            final_metrics = {}
            logger.warning("Annotation function returned None metrics")
        elif not isinstance(final_metrics, dict):
            logger.warning(f"Annotation function returned non-dict metrics: {type(final_metrics)}")
            final_metrics = {}
        
        logger.info(f"Annotation completed for: {file_name}")
        logger.info(f"Final metrics type: {type(final_metrics)}")
        logger.info(f"Final metrics: {final_metrics}")
    except Exception as e:
        logger.error(f"Annotation script failed for {file_name}: {e}")
        raise

    # 3. Upload annotated file to Supabase Storage
    try:
        with open(local_output, "rb") as f:
            supabase.storage.from_(BUCKET).upload(output_file, f, {"content-type": "video/mp4"})
        logger.info(f"Uploaded annotated video to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to upload annotated video {file_name}: {e}")
        raise

    # 4. Clean up local files
    try:
        os.remove(local_input)
        os.remove(local_output)
        logger.info(f"Cleaned up local files for: {file_name}")
    except Exception as e:
        logger.warning(f"Failed to clean up local files for {file_name}: {e}")

    return output_file, final_metrics

def get_next_unprocessed_submission():
    """
    Query the video_submissions table for the latest unprocessed submission.
    Returns the submission data or None if no unprocessed submissions exist.
    """
    try:
        # Query for pending submissions, ordered by updated_at desc
        response = supabase.table('video_submissions').select(
            'id, file_name, email, created_at, updated_at'
        ).eq('processed', ProcessingStatus.PENDING.value).order('updated_at', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            return None
    except Exception as e:
        logger.error(f"Failed to query video_submissions: {e}")
        raise

def mark_submission_processed(submission_id: int, output_file: str, processed_data: dict | None = None):
    """
    Mark a submission as processed in the database.
    """
    try:
        update_data = {
            'processed': ProcessingStatus.SUCCESS.value,
            'updated_at': datetime.utcnow().isoformat(),
            'output_file_name': output_file
        }
        
        if processed_data is not None:
            update_data['processed_data'] = processed_data
        
        supabase.table('video_submissions').update(update_data).eq('id', submission_id).execute()
        logger.info(f"Marked submission {submission_id} as processed")
    except Exception as e:
        logger.error(f"Failed to mark submission {submission_id} as processed: {e}")
        raise

def mark_submission_failed(submission_id: int, error_message: str):
    """
    Mark a submission as failed in the database.
    """
    try:
        update_data = {
            'processed': ProcessingStatus.FAILED.value,
            'processed_at': datetime.utcnow().isoformat(),
            'error_message': error_message
        }
        
        supabase.table('video_submissions').update(update_data).eq('id', submission_id).execute()
        logger.info(f"Marked submission {submission_id} as failed")
    except Exception as e:
        logger.error(f"Failed to mark submission {submission_id} as failed: {e}")
        raise

def main():
    """
    Main function to process the next unprocessed video submission.
    """
    logger.info("Starting cron job to process video submissions")
    
    try:
        # Get the next pending submission
        submission = get_next_unprocessed_submission()
        
        if not submission:
            logger.info("No pending submissions found. All submissions are processed.")
            return
        
        submission_id = submission['id']
        file_name = submission['file_name']
        email = submission['email']
        
        logger.info(f"Processing submission ID: {submission_id}, File: {file_name}, Email: {email}")
        
        # Start timing
        start_time = time.time()
        
        # Process the video
        output_file, final_metrics = process_video_submission('uploads/'+file_name)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        processing_time_str = f"{int(processing_time // 60)} minutes {int(processing_time % 60)} seconds"
        
        # Generate video URL for email
        video_url = generate_video_url(output_file)
        
        # Mark as processed
        processed_data = {
            'updated_at': datetime.utcnow().isoformat(),
            'output_file': output_file,
            'final_metrics': final_metrics
        }
        mark_submission_processed(submission_id, output_file, processed_data)
        
        logger.info(f"Successfully processed submission {submission_id}")
        
        # Send email notification
        try:
            email_sent = send_processing_completion_email(
                user_email=email,
                video_name=file_name,
                output_file_url=video_url,
                processing_time=processing_time_str,
                metrics=final_metrics
            )
            if email_sent:
                logger.info(f"Email notification sent successfully to {email}")
            else:
                logger.warning(f"Failed to send email notification to {email}")
        except Exception as email_error:
            logger.error(f"Error sending email notification to {email}: {email_error}")
        
    except Exception as e:
        logger.error(f"Cron job failed: {e}")
        
        # If we have a submission ID, mark it as failed
        if 'submission' in locals() and submission:
            try:
                mark_submission_failed(submission['id'], str(e))
            except Exception as mark_error:
                logger.error(f"Failed to mark submission as failed: {mark_error}")
        
        raise

if __name__ == "__main__":
    main() 