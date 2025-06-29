# Video Processing Cron Job Setup

This directory contains a cron job system for automatically processing video submissions from the database.

## Files

- `cron_processor.py` - Main Python script that processes video submissions
- `run_cron.sh` - Shell script wrapper for the cron job
- `cron_processor.log` - Log file created by the cron job (auto-generated)

## How It Works

1. The cron job queries the `video_submissions` table for rows where `processed` is `NULL`
2. It selects the most recently updated submission (ordered by `updated_at` DESC)
3. Downloads the video from Supabase Storage
4. Runs the annotation script (`annotate_with_opencv_pillow.py`)
5. Uploads the processed video back to Supabase Storage
6. Updates the database record with processing results
7. Cleans up temporary files

## Database Schema Requirements

The `video_submissions` table should have these columns:
- `id` (primary key)
- `file_name` (string) - path to the video file in storage
- `email` (string) - user's email address
- `processed` (boolean/null) - processing status (NULL = unprocessed, true = success, false = failed)
- `processed_at` (timestamp) - when processing was completed
- `output_file_name` (string) - path to the processed video in storage
- `error_message` (string) - error details if processing failed
- `processed_data` (jsonb) - additional processing metadata
- `created_at` (timestamp) - when the submission was created
- `updated_at` (timestamp) - when the submission was last updated

## Setting Up the Cron Job

### 1. Test the Script Manually

First, test that the script works:

```bash
cd webapp/backend
./run_cron.sh
```

### 2. Add to Crontab

Edit your crontab:

```bash
crontab -e
```

Add one of these lines depending on how often you want to run it:

```bash
# Run every 5 minutes
*/5 * * * * /full/path/to/webapp/backend/run_cron.sh >> /full/path/to/webapp/backend/cron.log 2>&1

# Run every 10 minutes
*/10 * * * * /full/path/to/webapp/backend/run_cron.sh >> /full/path/to/webapp/backend/cron.log 2>&1

# Run every hour
0 * * * * /full/path/to/webapp/backend/run_cron.sh >> /full/path/to/webapp/backend/cron.log 2>&1

# Run every 2 hours
0 */2 * * * /full/path/to/webapp/backend/run_cron.sh >> /full/path/to/webapp/backend/cron.log 2>&1
```

### 3. Environment Variables

Make sure your `.env` file contains:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET=running-form-analysis-input
```

### 4. Permissions

Ensure the script has execute permissions:
```bash
chmod +x webapp/backend/run_cron.sh
```

## Monitoring

### Log Files

- `cron_processor.log` - Detailed Python logging
- `cron.log` - Shell script output (if you redirect cron output)

### Check Cron Status

```bash
# View cron logs
tail -f webapp/backend/cron_processor.log

# Check if cron is running
ps aux | grep cron

# View system cron logs
sudo tail -f /var/log/syslog | grep CRON
```

### Manual Testing

```bash
# Test the script directly
cd webapp/backend
python3 cron_processor.py

# Test with shell wrapper
./run_cron.sh
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Make sure the script is executable
2. **Environment Variables**: Ensure `.env` file exists and has correct values
3. **Python Path**: Make sure `python3` is in the PATH when cron runs
4. **Working Directory**: The script changes to its own directory, but cron might run from a different location

### Debug Mode

To run with more verbose logging, modify `cron_processor.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO to DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_processor.log'),
        logging.StreamHandler()
    ]
)
```

## Database Queries

### Check Unprocessed Submissions

```sql
SELECT * FROM video_submissions 
WHERE processed IS NULL 
ORDER BY updated_at DESC;
```

### Check Processing Status

```sql
SELECT 
    id, 
    file_name, 
    email, 
    processed, 
    processed_at, 
    output_file_name,
    error_message
FROM video_submissions 
ORDER BY updated_at DESC;
```

### Reset Failed Submissions

```sql
UPDATE video_submissions 
SET processed = NULL, 
    processed_at = NULL, 
    output_file_name = NULL, 
    error_message = NULL 
WHERE processed = false;
``` 