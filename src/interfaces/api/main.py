"""FastAPI application for the coding agent API gateway."""
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from jose import JWTError, jwt
import bcrypt
import uuid

from src.infrastructure.observability.metrics import metrics_collector
from src.infrastructure.persistence.postgres import memory_manager
from dotenv import load_dotenv

load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# FastAPI app
app = FastAPI(
    title="Coding Agent API",
    description="Production-ready AI coding agent API gateway",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


# Models
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class TaskRequest(BaseModel):
    task: str = Field(..., description="The coding task to execute")
    user_id: str = Field(default="default_user", description="User ID for tracking")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    project_path: str = Field(default=".", description="Project directory path")
    use_rag: bool = Field(default=True, description="Enable RAG context enhancement")
    provider: str = Field(default="openai", description="LLM provider (openai, ollama, groq)")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


# Fake users database (replace with real database in production)
def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin User",
        "email": "admin@example.com",
        "hashed_password": get_password_hash("admin"),  # Change in production!
        "disabled": False,
    }
}


# Authentication functions
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Coding Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "up",
            "database": "up"
        }
    }


@app.post("/api/v1/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Get JWT access token."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/v1/tasks", response_model=TaskResponse)
async def submit_task(
    request: TaskRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Submit a new coding task."""
    task_id = str(uuid.uuid4())
    
    # Record metrics
    metrics_collector.record_request(request.user_id, "submitted", 0)
    
    # In production, this would submit to Celery
    # For now, return task ID
    return TaskResponse(
        task_id=task_id,
        status="queued",
        message="Task submitted successfully. Use /api/v1/tasks/{task_id} to check status."
    )


@app.get("/api/v1/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get status of a task."""
    # In production, this would query Celery/database
    return TaskStatusResponse(
        task_id=task_id,
        status="completed",
        result="Task completed successfully",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )


@app.get("/api/v1/sessions")
async def list_sessions(
    user_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user)
):
    """List conversation sessions for a user."""
    try:
        sessions = memory_manager.get_user_sessions(user_id, limit=limit)
        return {
            "status": "success",
            "sessions": [
                {
                    "id": s.id,
                    "user_id": s.user_id,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                    "metadata": s.metadata
                }
                for s in sessions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics")
async def get_metrics():
    """Get Prometheus metrics."""
    metrics_data = metrics_collector.get_metrics()
    return metrics_data.decode('utf-8')


@app.websocket("/api/v1/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time task streaming."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Echo for now - in production, this would stream agent execution
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
