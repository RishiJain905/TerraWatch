from fastapi import FastAPI

app = FastAPI(title="TerraWatch API", version="0.1.0")

@app.get("/api/metadata")
async def metadata():
    return {"status": "ok", "phase": 1}