from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
try:
    from app.core.auditor import run_stealth_audit
except ImportError:
    try:
        from core.auditor import run_stealth_audit
    except ImportError:
        from auditor import run_stealth_audit

app = FastAPI(title="Stealth Engine Remote Auditor")

class AuditRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"status": "Stealth Auditor is running on Hugging Face"}

@app.post("/audit")
async def remote_audit(request: AuditRequest):
    try:
        print(f"REMOTE DEBUG: Auditing {request.url}")
        result = await run_stealth_audit(request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
