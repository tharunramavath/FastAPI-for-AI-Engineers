"""
routers/vision.py — File Upload Endpoint
==========================================
CONCEPT: File Uploads with UploadFile

When your model takes images, audio, or PDFs as input,
you need to handle file uploads. FastAPI uses `UploadFile`.

Why AI engineers need this:
  - Vision models (CLIP, GPT-4V, Gemini) take image inputs
  - Whisper takes audio files
  - RAG pipelines take PDF/document uploads
  - Multimodal AI is everywhere

Key difference from JSON endpoints:
  - Instead of Content-Type: application/json
  - Client sends Content-Type: multipart/form-data
  - You use Form() and File() instead of a request body
"""

import uuid
import time
import random
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.middleware.auth import verify_api_key
from app.schemas.response import VisionResponse

router = APIRouter(tags=["Vision"])

# Allowed file types — always validate this server-side
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB in bytes


@router.post(
    "/vision/analyze",
    response_model=VisionResponse,
    summary="Analyze an image with the vision model",
)
async def analyze_image(
    _: str = Depends(verify_api_key),
    file: UploadFile = File(
        ...,
        description="Image file (JPEG, PNG, or WebP). Max 10MB."
    ),
):
    """
    CONCEPT: UploadFile

    `UploadFile` gives you:
      - file.filename       → original filename
      - file.content_type   → MIME type (e.g., "image/jpeg")
      - await file.read()   → the raw bytes
      - await file.seek(0)  → reset read position

    In a real vision API:
      1. Read the bytes
      2. Convert to PIL Image or base64
      3. Pass to your vision model
      4. Return the result

    Test with:
      curl -X POST http://localhost:8000/vision/analyze \\
        -H "X-API-Key: test-key-123" \\
        -F "file=@photo.jpg"
    """
    # ── Validation ──────────────────────────────────────────
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {ALLOWED_TYPES}",
        )

    # Read the file into memory
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large: {len(contents)} bytes. Max: {MAX_FILE_SIZE} bytes",
        )

    # ── Mock Inference ───────────────────────────────────────
    start = time.time()

    # In reality: image = Image.open(io.BytesIO(contents))
    #             result = vision_model(image)
    mock_objects = random.sample(
        ["person", "dog", "car", "tree", "building", "laptop", "phone", "book"],
        k=random.randint(2, 4)
    )
    mock_caption = f"An image showing {', '.join(mock_objects[:2])} in a natural setting."

    latency_ms = (time.time() - start) * 1000 + random.uniform(200, 500)

    return VisionResponse(
        request_id=str(uuid.uuid4()),
        filename=file.filename or "unknown",
        file_size_bytes=len(contents),
        detected_objects=mock_objects,
        caption=mock_caption,
        latency_ms=round(latency_ms, 2),
    )
