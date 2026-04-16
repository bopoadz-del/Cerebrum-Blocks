import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.dependencies import require_api_key

router = APIRouter()

MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp",
    ".txt", ".md", ".csv", ".json", ".xml",
    ".mp3", ".mp4", ".wav", ".webm",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"
}

DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)


@router.post("/upload")
async def upload_v1(file: UploadFile = File(...), auth: dict = Depends(require_api_key)):
    """File upload endpoint (v1 API).

    Accepts validated files and stores them. Returns URL for processing.
    """
    try:
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        if file_size > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"File too large. Max size: {MAX_UPLOAD_SIZE} bytes")

        # Validate and sanitize filename
        original_name = (file.filename or "unknown").strip()
        if not original_name or original_name in (".", ".."):
            raise HTTPException(status_code=400, detail="Invalid filename")

        # Prevent path traversal
        original_name = os.path.basename(original_name.replace("\\", "/"))
        _, ext = os.path.splitext(original_name.lower())
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

        # Generate unique filename
        file_id = str(uuid.uuid4())[:8]
        filename = f"{file_id}_{original_name}"
        filepath = os.path.join(DATA_DIR, filename)

        # Save uploaded file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Return URL for processing
        base_url = os.getenv("API_BASE_URL", "https://cerebrum-platform-api.onrender.com")
        return {
            "url": f"{base_url}/static/{filename}",
            "filename": original_name,
            "stored_as": filename,
            "size": file_size
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Upload failed")


@router.post("/v1/upload")
async def upload_v1_endpoint(file: UploadFile = File(...), auth: dict = Depends(require_api_key)):
    """File upload endpoint (v1 API alias)."""
    return await upload_v1(file, auth)
