from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# 段階的なCORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 最初は全許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/cors-test")
def cors_test():
    return {"cors": "enabled", "origin": "allowed"}

@app.post("/cors-test")
def cors_test_post():
    return {"cors": "POST enabled", "origin": "allowed"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")

