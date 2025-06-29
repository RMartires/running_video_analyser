# Email Notification Setup Guide

This guide explains how to set up email notifications for video processing completion using Brevo's Transactional Email API.

## Prerequisites

1. **Brevo Account**: Sign up at [brevo.com](https://www.brevo.com/)
2. **API Key**: Get your API key from the Brevo dashboard
3. **Verified Sender**: Set up a verified sender email address

## Environment Variables

Add these variables to your `.env` file:

```bash
# Brevo API Configuration
BREVO_API_KEY=your_brevo_api_key_here
SENDER_EMAIL=your_verified_sender@yourdomain.com

# Supabase Storage URL (for video links)
SUPABASE_STORAGE_URL=https://your-project.supabase.co/storage/v1/object/public
SUPABASE_BUCKET=running-form-analysis-input
```

## Brevo API Setup

### 1. Get Your API Key

1. Log in to your Brevo account
2. Go to **Settings** → **API Keys**
3. Create a new API key with **SMTP** permissions
4. Copy the API key to your `.env` file

### 2. Verify Your Sender Email

1. Go to **Settings** → **Senders & IP**
2. Add and verify your sender email address
3. Use this email in the `SENDER_EMAIL` environment variable

### 3. Test Your Setup

Run the email test script:

```bash
cd webapp/backend
python3 send_email.py
```

## Email Template Features

The email template includes:

- **Professional Design**: Clean, responsive HTML layout
- **Video Information**: Original filename and processing timestamp
- **Processing Time**: How long the analysis took
- **Direct Video Link**: One-click access to the processed video
- **Feature List**: What's included in the analysis
- **Fallback Text**: Plain text version for email clients that don't support HTML

## Customization

### Modify Email Template

Edit the `html_content` and `text_content` in `send_email.py` to customize:

- Colors and styling
- Company branding
- Email content and tone
- Call-to-action buttons

### Add More Variables

You can add more dynamic content by:

1. Adding parameters to `send_processing_completion_email()`
2. Updating the email template to use the new variables
3. Passing the data from `cron_processor.py`

## Video URL Generation

The `generate_video_url()` function creates public URLs for processed videos. You may need to:

1. **Configure Public Access**: Make your Supabase storage bucket public
2. **Use Signed URLs**: For private videos, implement signed URL generation
3. **Custom Domain**: Set up a custom domain for video URLs

### Example Supabase Storage Setup

```sql
-- Make bucket public (if needed)
-- This is done in Supabase dashboard under Storage settings
```

## Monitoring

### Email Delivery Status

Brevo provides delivery tracking. Check your Brevo dashboard for:

- Email delivery rates
- Bounce rates
- Open rates
- Click rates

### Logs

Email sending is logged in:
- `cron_processor.log` - Processing and email status
- Brevo dashboard - Delivery and engagement metrics

## Troubleshooting

### Common Issues

1. **API Key Invalid**: Check your Brevo API key in `.env`
2. **Sender Not Verified**: Verify your sender email in Brevo
3. **Video URL Not Accessible**: Check Supabase storage permissions
4. **Email Not Sending**: Check network connectivity and API limits

### Debug Mode

Enable debug logging in `send_email.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

### Test Email Function

```python
from send_email import send_processing_completion_email

success = send_processing_completion_email(
    user_email="test@example.com",
    video_name="test_video.mp4",
    output_file_url="https://example.com/video.mp4",
    processing_time="2 minutes 30 seconds"
)
print(f"Email sent: {success}")
```

## Security Considerations

1. **API Key Security**: Never commit API keys to version control
2. **Email Validation**: Validate email addresses before sending
3. **Rate Limiting**: Respect Brevo's API rate limits
4. **Error Handling**: Handle email failures gracefully

## Cost Considerations

Brevo pricing is based on:
- Number of emails sent
- API calls made
- Additional features used

Check [Brevo's pricing page](https://www.brevo.com/pricing/) for current rates. 