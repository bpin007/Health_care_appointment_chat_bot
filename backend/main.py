from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from api.calendly_integration import router as calendly_router

app = FastAPI(title="Medical Appointment Scheduling Agent")

# 🔥 Allow frontend to call backend
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # domains allowed for requests
    allow_credentials=True,
    allow_methods=["*"],         # GET, POST, PUT, DELETE...
    allow_headers=["*"],         # Authorization, Content-Type etc
)

# Include routes
app.include_router(chat_router, prefix="/api/chat")
app.include_router(calendly_router, prefix="/api/calendly")

@app.get("/")
def root():
    return {"message": "Appointment Scheduling Agent Backend Running"}
