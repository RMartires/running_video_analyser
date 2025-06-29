import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
from supabase import create_client, Client
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
BUCKET = os.environ.get("SUPABASE_BUCKET", "running-form-analysis-input")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        buckets = supabase.storage.list_buckets()
        print("Supabase connection OK. Buckets:", buckets)
    except Exception as e:
        print("Supabase connection failed:", e)
    yield

app = FastAPI(lifespan=lifespan)

class ProcessRequest(BaseModel):
    file_name: str

@app.post("/process-video")
async def process_video(req: ProcessRequest):
    input_file = req.file_name
    local_input = f"./temp/{os.path.basename(input_file)}"
    local_output = f"./temp/annotated_{os.path.basename(input_file)}"
    output_file = f"outputs/annotated_{os.path.basename(input_file)}"

    # Null check: verify file exists in storage
    try:
        # Extract the directory and file name
        if "/" in input_file:
            dir_path, file_only = os.path.split(input_file)
        else:
            dir_path, file_only = "", input_file
        print(dir_path)
        file_list = supabase.storage.from_(BUCKET).list(dir_path)
        print(file_list)
        if not any(f["name"] == file_only for f in file_list):
            raise HTTPException(status_code=404, detail=f"File not found in storage: {input_file}")
    except Exception as e:
        msg = str(e)
        if "File not found in storage" in msg or "404" in msg:
            raise HTTPException(status_code=404, detail=f"Error checking file existence: {msg}")
        else:
            raise HTTPException(status_code=500, detail=f"Error checking file existence: {msg}")

    # 1. Download from Supabase Storage
    try:
        res = supabase.storage.from_(BUCKET).download(input_file)
        with open(local_input, "wb") as f:
            f.write(res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download video: {e}")

    # 2. Run annotation script
    try:
        subprocess.run([
            "python3", "./annotate_with_opencv_pillow.py", local_input, local_output
        ], check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Annotation script failed: {e}")

    # 3. Upload annotated file to Supabase Storage
    try:
        with open(local_output, "rb") as f:
            supabase.storage.from_(BUCKET).upload(output_file, f, {"content-type": "video/mp4"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload annotated video: {e}")

    return {"status": "success", "output_file": output_file} 