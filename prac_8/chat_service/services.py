import asyncio
import threading

from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import MeasurementDB, State, Status, Measurement
from typing import Optional, List, Dict
import json
import uuid
import os
from minio import Minio
import pika
from datetime import datetime
from websocket_manager import websocket_manager


class MinIOService:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.bucket = os.getenv("ECG_BUCKET", "ecg-bucket")

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False
        )

        # Create bucket if it doesn't exist
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload_file(self, object_name: str, file_content: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload file to MinIO and return URL"""
        from io import BytesIO

        file_stream = BytesIO(file_content)
        self.client.put_object(
            self.bucket,
            object_name,
            file_stream,
            length=len(file_content),
            content_type=content_type
        )

        return f"{self.endpoint}/{self.bucket}/{object_name}"


class RabbitMQService:
    def __init__(self):
        self.connection_uri = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost:5672/%2F")
        self.request_queue = os.getenv("REQUEST_QUEUE", "ecg_requests")
        self.response_queue = os.getenv("RESPONSE_QUEUE", "ecg_responses")

    def publish_analysis_message(self, message: dict):
        """Publish message to RabbitMQ for ECG analysis"""
        connection = pika.BlockingConnection(pika.URLParameters(self.connection_uri))
        channel = connection.channel()

        channel.queue_declare(queue=self.request_queue, durable=True)

        message_json = json.dumps(message)
        channel.basic_publish(
            exchange='',
            routing_key=self.request_queue,
            body=message_json,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )

        connection.close()

    def start_response_consumer(self, on_response):
        """
        Запускает блокирующий consumer ecg_responses и передаёт сообщения в on_response(ch, method, props, body)
        Вызови это из отдельного потока.
        """
        params = pika.URLParameters(self.connection_uri)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=self.response_queue, durable=True)
        channel.basic_qos(prefetch_count=1)

        def _cb(ch, method, props, body):
            try:
                on_response(ch, method, props, body)
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=self.response_queue, on_message_callback=_cb)
        channel.start_consuming()


class MeasurementService:
    def __init__(self, db: Session):
        self.db = db
        self.minio_service = MinIOService()
        self.rabbitmq_service = RabbitMQService()

    async def create_measurement_from_file(
            self,
            measurement_id: str,
            filename: str,
            file_content: bytes,
            fs: int,
            state: State,
            meta: Optional[str] = None,
            user_id: str = "anonymous"
    ) -> Measurement:
        """Create measurement from uploaded file"""

        # Determine file format
        file_format = "unknown"
        if filename:
            if filename.endswith(".csv"):
                file_format = "csv"
            elif filename.endswith(".npy"):
                file_format = "npy"
            elif filename.endswith(".json"):
                file_format = "json"

        # Upload file to MinIO
        object_name = f"{measurement_id}_{filename or 'file'}"
        ecg_file_url = self.minio_service.upload_file(object_name, file_content)

        # Create measurement in database
        measurement_db = MeasurementDB(
            id=measurement_id,
            status=Status.processing,
            state=state,
            fs=fs,
            format=file_format,
            ecg_file_url=ecg_file_url,
            user_id=user_id
        )

        self.db.add(measurement_db)
        self.db.commit()
        self.db.refresh(measurement_db)

        # Send message to RabbitMQ for analysis
        analysis_message = {
            "measurement_id": measurement_id,
            "bucket": self.minio_service.bucket,
            "object_name": object_name,
            "fs": fs
        }
        self.rabbitmq_service.publish_analysis_message(analysis_message)

        # Notify via WebSocket
        await websocket_manager.broadcast_status_update(user_id, measurement_id, Status.processing)

        return self._db_to_api_model(measurement_db)

    async def create_measurement_from_json(
            self,
            measurement_id: str,
            ecg_data: List[float],
            fs: int,
            state: State,
            user_id: str = "anonymous"
    ) -> Measurement:
        """Create measurement from JSON ECG data"""

        # Create measurement in database (no file upload)
        measurement_db = MeasurementDB(
            id=measurement_id,
            status=Status.processing,
            state=state,
            fs=fs,
            format="json",
            user_id=user_id
        )

        self.db.add(measurement_db)
        self.db.commit()
        self.db.refresh(measurement_db)

        # For JSON data, we might process it differently
        # For now, just create the measurement record

        # Notify via WebSocket
        await websocket_manager.broadcast_status_update(user_id, measurement_id, Status.processing)

        return self._db_to_api_model(measurement_db)

    def get_measurement(self, measurement_id: str, user_id: str = None) -> Optional[Measurement]:
        """Get measurement by ID with optional user validation"""
        query = self.db.query(MeasurementDB).filter(MeasurementDB.id == measurement_id)

        if user_id:
            query = query.filter(MeasurementDB.user_id == user_id)

        measurement_db = query.first()

        if not measurement_db:
            return None

        return self._db_to_api_model(measurement_db)

    def get_user_measurements(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Measurement]:
        """Get all measurements for a specific user"""
        measurements_db = self.db.query(MeasurementDB).filter(
            MeasurementDB.user_id == user_id
        ).order_by(MeasurementDB.created_at.desc()).offset(offset).limit(limit).all()

        return [self._db_to_api_model(m) for m in measurements_db]

    async def update_state(self, measurement_id: str, state: State) -> Optional[Measurement]:
        """Update measurement state"""
        measurement_db = self.db.query(MeasurementDB).filter(
            MeasurementDB.id == measurement_id
        ).first()

        if not measurement_db:
            return None

        measurement_db.state = state
        measurement_db.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(measurement_db)

        # Notify via WebSocket
        await websocket_manager.broadcast_state_update(measurement_db.user_id, measurement_id, state)

        return self._db_to_api_model(measurement_db)

    async def update_results(self, measurement_id: str, results: Dict[str, float]) -> Optional[Measurement]:
        """Update measurement with analysis results"""
        measurement_db = self.db.query(MeasurementDB).filter(
            MeasurementDB.id == measurement_id
        ).first()

        if not measurement_db:
            return None

        measurement_db.results = json.dumps(results)
        measurement_db.status = Status.done
        measurement_db.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(measurement_db)

        # Notify via WebSocket
        await websocket_manager.broadcast_results_update(measurement_db.user_id, measurement_id, results)

        return self._db_to_api_model(measurement_db)

    async def update_errors(self, measurement_id: str, errors: List[str]) -> Optional[Measurement]:
        """Update measurement with errors"""
        measurement_db = self.db.query(MeasurementDB).filter(
            MeasurementDB.id == measurement_id
        ).first()

        if not measurement_db:
            return None

        measurement_db.errors = json.dumps(errors)
        measurement_db.status = Status.error
        measurement_db.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(measurement_db)

        # Notify via WebSocket
        await websocket_manager.broadcast_error_update(measurement_db.user_id, measurement_id, errors)

        return self._db_to_api_model(measurement_db)

    def _db_to_api_model(self, measurement_db: MeasurementDB) -> Measurement:
        """Convert database model to API model"""
        results = None
        if measurement_db.results:
            try:
                results = json.loads(measurement_db.results)
            except json.JSONDecodeError:
                results = None

        errors = None
        if measurement_db.errors:
            try:
                errors = json.loads(measurement_db.errors)
            except json.JSONDecodeError:
                errors = None

        return Measurement(
            id=measurement_db.id,
            status=measurement_db.status,
            state=measurement_db.state,
            fs=measurement_db.fs,
            format=measurement_db.format,
            duration_sec=measurement_db.duration_sec,
            created_at=measurement_db.created_at,
            updated_at=measurement_db.updated_at,
            results=results,
            errors=errors,
            llm_answer=measurement_db.llm_answer
        )

    def start_rabbit_listener(self):
        """Стартуем фоновый поток, слушающий ecg_responses"""

        def _handle_response(ch, method, props, body: bytes):
            print("Handle answer")
            try:
                resp = json.loads(body.decode("utf-8"))
            except Exception as e:
                # невалидный json — игнор/лог
                return

            # measurement_id берём из correlation_id; если нет — из тела
            measurement_id = props.correlation_id or resp.get("measurement_id")
            if not measurement_id:
                return

            if resp.get("status") == "ok":
                results = resp.get("features", {})
                llm_answer = resp.get("llm_summary")
                # обновляем БД
                m = self.db.query(MeasurementDB).filter(MeasurementDB.id == measurement_id).first()
                if m and llm_answer:
                    m.results = json.dumps(results)
                    m.status = Status.done
                    m.updated_at = datetime.now()
                    m.llm_answer = llm_answer
                    self.db.commit()
                    self.db.refresh(m)
                    # пушим WS, если есть event loop
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            websocket_manager.broadcast_results_update(m.user_id, measurement_id, results)
                        )
                    except RuntimeError:
                        # нет активного цикла — пропускаем или логируем
                        pass
            else:
                err = resp.get("error", "unknown error")
                m = self.db.query(MeasurementDB).filter(MeasurementDB.id == measurement_id).first()
                if m:
                    m.errors = json.dumps([err])
                    m.status = Status.error
                    m.updated_at = datetime.utcnow()
                    self.db.commit()
                    self.db.refresh(m)
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            websocket_manager.broadcast_error_update(m.user_id, measurement_id, [err])
                        )
                    except RuntimeError:
                        pass

        # запустить блокирующий consumer в отдельном демоне
        t = threading.Thread(
            target=self.rabbitmq_service.start_response_consumer,
            args=(_handle_response,),
            daemon=True,
        )
        t.start()