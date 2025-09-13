from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ValidationError
import uvicorn
import json

app = FastAPI()

class TestModel(BaseModel):
    email: str
    password: str
    optional_field: str = "default"

@app.post("/validate")
async def validate_data(request: Request, data: TestModel):
    # リクエストボディの生ログを確認
    body = await request.body()
    print(f"Raw body: {body}")
    
    return {
        "message": "Validation successful",
        "received": data.dict(),
        "raw_body_length": len(body)
    }

@app.post("/validate-manual")
async def validate_manual(request: Request):
    try:
        body = await request.body()
        print(f"Raw body: {body}")
        
        # JSON解析を手動で試行
        try:
            json_data = json.loads(body)
            print(f"Parsed JSON: {json_data}")
        except json.JSONDecodeError as e:
            return {"error": "Invalid JSON", "details": str(e)}
        
        # Pydanticバリデーションを手動で試行
        try:
            model = TestModel(**json_data)
            return {"message": "Manual validation successful", "data": model.dict()}
        except ValidationError as e:
            return {"error": "Validation error", "details": e.errors()}
            
    except Exception as e:
        return {"error": "Unexpected error", "details": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")

