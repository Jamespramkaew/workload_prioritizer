from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Workload Prioritizer API", version="1.0.0")

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Next.js dev server
        "http://127.0.0.1:3000",      # Alternative
        "http://localhost:8000",      # Backend itself
        "http://127.0.0.1:8000",      # Alternative
    ],
    allow_credentials=True,
    allow_methods=["*"],              # อนุญาตทุก HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],              # อนุญาตทุก headers
)

@app.get("/")
def read_root():
    return {"message": "Hello from Workload Prioritizer Backend!"}

@app.get("/ping")
def ping_system():
    return {"status": "success", "detail": "pong!"}
