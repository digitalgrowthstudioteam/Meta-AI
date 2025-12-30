  """
Digital Growth Studio (Meta-AI)
Main application entry point
"""

from fastapi import FastAPI

app = FastAPI(
    title="Digital Growth Studio",
    description="Meta Ads AI Optimization Platform",
    version="0.1.0"
)


@app.get("/")
def health_check():
    return {"status": "ok"}
