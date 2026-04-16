from fastapi import FastAPI

app = FastAPI(title="NotebookLM PPT Agent")


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
