import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Header, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.websockets import WebSocket

from database import get_db, init_db
from models import Measurement, State, MeasurementList
from services import MeasurementService
from websocket_manager import websocket_manager

load_dotenv()

app = FastAPI(title="ECG Measurements API", version="1.0")

# Initialize database
init_db()

@app.on_event("startup")
async def startup_event():
    print("ECG Measurements API started")


@app.post("/v1/measurements", response_model=Measurement, status_code=201)
async def create_measurement_from_file(
    file: UploadFile = File(...),
    fs: int = Form(...),
    state: str = Form(...),
    meta: Optional[str] = Form(None),
    user_id: str = Header(alias="user-id"),
    db: Session = Depends(get_db)
):
    """Create ECG measurement from uploaded file"""
    try:
        # Validate state
        try:
            state_enum = State(state)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid state. Must be one of: exercise, rest, daily")
        
        # Validate fs range
        if not (50 <= fs <= 2000):
            raise HTTPException(status_code=400, detail="fs must be between 50 and 2000")
        
        measurement_service = MeasurementService(db)
        
        # Read file content
        content = await file.read()
        
     # Create measurement
        measurement_id = str(uuid.uuid4())
        measurement = await measurement_service.create_measurement_from_file(
            measurement_id=measurement_id,
            filename=file.filename,
            file_content=content,
            fs=fs,
            state=state_enum,
            meta=meta,
            user_id=user_id
        )
        
        return measurement
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/measurements/json", response_model=Measurement, status_code=201)
async def create_measurement_from_json(
    request: dict,
    user_id: str = Header(alias="user-id"),
    db: Session = Depends(get_db)
):
    """Create ECG measurement from JSON array"""
    try:
        # Validate required fields
        if "ecg" not in request or "fs" not in request or "state" not in request:
            raise HTTPException(status_code=400, detail="ecg, fs, and state are required")
        
        # Validate ecg array
        ecg_data = request["ecg"]
        if not isinstance(ecg_data, list) or len(ecg_data) < 10:
            raise HTTPException(status_code=400, detail="ecg must be an array with at least 10 elements")
        
        # Validate fs
        fs = request["fs"]
        if not isinstance(fs, int) or not (50 <= fs <= 2000):
            raise HTTPException(status_code=400, detail="fs must be an integer between 50 and 2000")
        
        # Validate state
        try:
            state_enum = State(request["state"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid state. Must be one of: exercise, rest, daily")
        
        measurement_service = MeasurementService(db)
        
        # Create measurement
        measurement_id = str(uuid.uuid4())
        measurement = await measurement_service.create_measurement_from_json(
            measurement_id=measurement_id,
            ecg_data=ecg_data,
            fs=fs,
            state=state_enum,
            user_id=user_id
        )
        
        return measurement
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/measurements", response_model=MeasurementList)
async def get_user_measurements(
    user_id: str = Header(alias="user-id"),
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all measurements for the current user"""
    measurement_service = MeasurementService(db)
    measurements = measurement_service.get_user_measurements(user_id, limit, offset)
    
    # Get total count
    from models import MeasurementDB
    total = db.query(MeasurementDB).filter(MeasurementDB.user_id == user_id).count()
    
    return MeasurementList(
        measurements=measurements,
        total=total,
        limit=limit,
        offset=offset
    )

@app.get("/v1/measurements/{measurement_id}", response_model=Measurement)
async def get_measurement(
    measurement_id: str,
    user_id: str = Header(alias="user-id"),
    db: Session = Depends(get_db)
):
    """Get measurement by ID (only if user owns it)"""
    measurement_service = MeasurementService(db)
    measurement = measurement_service.get_measurement(measurement_id, user_id)
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    return measurement

@app.patch("/v1/measurements/{measurement_id}", response_model=Measurement)
async def update_measurement(
    measurement_id: str,
    request: dict,
    user_id: str = Header(alias="user-id"),
    db: Session = Depends(get_db)
):
    """Update measurement state (only if user owns it)"""
    measurement_service = MeasurementService(db)
    
    # Check if measurement exists and user owns it
    existing = measurement_service.get_measurement(measurement_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Measurement not found")
    
    # Update state if provided
    if "state" in request:
        try:
            state_enum = State(request["state"])
            measurement = await measurement_service.update_state(measurement_id, state_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid state. Must be one of: exercise, rest, daily")
    else:
        measurement = existing
    
    return measurement

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time updates"""
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for ping/pong
            await websocket.send_text(data)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, user_id)

if __name__ == "__main__":
    import uvicorn
    MeasurementService(next(get_db())).start_rabbit_listener()
    uvicorn.run(app, host="0.0.0.0", port=8080)
