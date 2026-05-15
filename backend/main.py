from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.analyze import analyze_contract
from services.extract_pdf import extract_text as extract_pdf_text

app = FastAPI(title="Clause — Contract Compliance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class AnalyzeRequest(BaseModel):
    text: str
    freelancer_mode: bool = False


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if len(req.text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Contract text too short.")
    try:
        return await analyze_contract(req.text, req.freelancer_mode)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    freelancer_mode: str = Form("false"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    try:
        pdf_bytes = await file.read()
        text = extract_pdf_text(pdf_bytes)
        if len(text.strip()) < 100:
            raise HTTPException(status_code=400, detail="Could not extract enough text from this PDF.")
        return await analyze_contract(text[:40000], freelancer_mode.lower() == "true")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
