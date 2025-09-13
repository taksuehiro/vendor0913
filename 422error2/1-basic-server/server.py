from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Server is running"}

@app.get("/test")
def test():
    return {"test": "success", "method": "GET"}

@app.post("/test")
def test_post():
    return {"test": "success", "method": "POST"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

