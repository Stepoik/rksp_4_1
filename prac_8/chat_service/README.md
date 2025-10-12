# ECG Measurements API

FastAPI service for ECG measurements processing according to OpenAPI specification.

## Features

- Create ECG measurements from uploaded files or JSON data
- Store measurements in PostgreSQL database
- Upload files to MinIO object storage
- Send analysis requests to RabbitMQ
- Track measurement status and results
- User authentication via user_id header

## API Endpoints

- `POST /v1/measurements` - Create measurement from uploaded file
- `POST /v1/measurements/json` - Create measurement from JSON array
- `GET /v1/measurements` - Get all measurements for current user
- `GET /v1/measurements/{id}` - Get measurement by ID (only if user owns it)
- `PATCH /v1/measurements/{id}` - Update measurement state (only if user owns it)
- `WS /ws/{user_id}` - WebSocket connection for real-time updates

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment variables:
```bash
cp env_example.txt .env
```

3. Update `.env` with your configuration

4. Run the service:
```bash
python main.py
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `MINIO_ENDPOINT` - MinIO server endpoint
- `MINIO_ACCESS_KEY` - MinIO access key
- `MINIO_SECRET_KEY` - MinIO secret key
- `ECG_BUCKET` - MinIO bucket name for ECG files
- `RABBIT_URL` - RabbitMQ connection string
- `REQUEST_QUEUE` - RabbitMQ queue name for analysis requests

## Usage

All endpoints require `user_id` header for authentication.

### Create measurement from file:
```bash
curl -X POST "http://localhost:8080/v1/measurements" \
  -H "user_id: user123" \
  -F "file=@ecg.csv" \
  -F "fs=200" \
  -F "state=rest"
```

### Create measurement from JSON:
```bash
curl -X POST "http://localhost:8080/v1/measurements/json" \
  -H "user_id: user123" \
  -H "Content-Type: application/json" \
  -d '{
    "ecg": [1.0, 2.0, 3.0, ...],
    "fs": 200,
    "state": "exercise"
  }'
```

### Get all user measurements:
```bash
curl -X GET "http://localhost:8080/v1/measurements?limit=50&offset=0" \
  -H "user_id: user123"
```

### Get specific measurement:
```bash
curl -X GET "http://localhost:8080/v1/measurements/{id}" \
  -H "user_id: user123"
```

### Update measurement state:
```bash
curl -X PATCH "http://localhost:8080/v1/measurements/{id}" \
  -H "user_id: user123" \
  -H "Content-Type: application/json" \
  -d '{"state": "exercise"}'
```

### WebSocket connection:
```javascript
const ws = new WebSocket('ws://localhost:8080/ws/user123');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## WebSocket Messages

The WebSocket sends real-time updates when measurement status or state changes:

- `status_update` - When measurement status changes (processing → done/error)
- `state_update` - When measurement state changes (exercise/rest/daily)
- `results_update` - When analysis results are available
- `error_update` - When analysis encounters errors
