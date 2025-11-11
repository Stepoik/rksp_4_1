import os
import json
import tempfile
from dotenv import load_dotenv
from minio import Minio
import pika
import pandas as pd

from config import ConfigClient
from model import DEFAULT_MODEL, infer_ecg_1d

from openai import OpenAI

load_dotenv()

CONFIG = ConfigClient()
# RabbitMQ settings
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@localhost:5672/%2F")
REQUEST_QUEUE = os.getenv("REQUEST_QUEUE", "ecg_requests")
RESPONSE_QUEUE = os.getenv("RESPONSE_QUEUE", "ecg_responses")

# MinIO settings
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# LLM settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = CONFIG.get("LLM_MODEL", "gpt-4o-mini")  # можно поменять на свой
LLM_ENABLED = bool(OPENAI_API_KEY and OpenAI)


def download_from_minio(bucket: str, object_name: str) -> str:
    client = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=False)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    client.fget_object(bucket, object_name, tmp.name)
    return tmp.name


def build_llm_prompt(features: dict, meta: dict) -> dict:
    """Готовим system+user для чата: без диагнозов, с безопасной интерпретацией."""
    # meta может включать phase/симптомы и т.п., если ты их передаёшь в сообщении
    phase = (meta or {}).get("phase") or (meta or {}).get("context", {}).get("phase", "unknown")
    fs = (meta or {}).get("fs")
    duration = (meta or {}).get("duration_sec")

    system = (
        "Ты медицинский ассистент. Объясняй кратко и понятно.\n"
        "Не ставь диагнозов и не назначай лечение. Всегда добавляй дисклеймер.\n"
        "Если запись делалась во время тренировки, объясни, что высокий пульс и низкая HRV могут быть нормой нагрузки.\n"
        "Если уверенность низкая, предложи повторить запись 30–60 секунд в покое."
    )

    user = {
        "context": {
            "phase": phase,
            "fs": fs,
            "duration_sec": duration
        },
        "model_findings": features
    }

    return {
        "system": system,
        "user": json.dumps(user, ensure_ascii=False)
    }


def run_llm(features: dict, meta: dict) -> str:
    """Вызов OpenAI чата. Возвращает текст интерпретации или бросает исключение."""
    if not LLM_ENABLED:
        raise RuntimeError("LLM disabled: OPENAI_API_KEY или пакет openai не настроены")

    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENAI_API_KEY)

    p = build_llm_prompt(features, meta)
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": p["system"]},
            {"role": "user", "content": p["user"]},
        ],
    )
    return resp.choices[0].message.content.strip()


def on_request(ch, method, props, body):
    try:
        msg = json.loads(body)
        bucket = msg["bucket"]
        # в твоём первом сервисе могло быть object_key; во втором — object_name,
        # поэтому поддержим оба ключа, чтобы не споткнуться
        object_name = msg.get("object_name") or msg.get("object_key")
        measurement_id = msg["measurement_id"]
        print(f"Processing {object_name}")
        fs = int(msg.get("fs", 200))

        local_path = download_from_minio(bucket, object_name)
        df = pd.read_csv(local_path)
        # предполагаем колонку 'ECG'
        if "ECG" not in df.columns:
            raise ValueError("В CSV не найдена колонка 'ECG'")
        signal = df["ECG"].values

        feats = infer_ecg_1d(model=DEFAULT_MODEL, x_1d=signal, fs_src=fs)
        # feats ожидается как словарь с вероятностями/метриками. Если возвращается не dict — завернём
        if not isinstance(feats, dict):
            feats = {"result": feats}

        # мета для LLM (то, что пришло в сообщении)
        meta = {
            "phase": (msg.get("context") or {}).get("phase"),
            "fs": fs,
            "duration_sec": msg.get("duration_sec"),
        }

        llm_summary = None
        if LLM_ENABLED:
            try:
                llm_summary = run_llm(features=feats, meta=meta)
            except Exception as e:
                llm_summary = f"LLM error: {e}"
        response = {
            "status": "ok",
            "features": feats,
            "llm_summary": llm_summary,
            "measurement_id": measurement_id
        }

    except Exception as e:
        response = {"status": "error", "error": str(e), "measurement_id": msg.get("measurement_id") if 'msg' in locals() else None}

    print(f"Processed {response}")
    ch.basic_publish(
        exchange="",
        routing_key=RESPONSE_QUEUE,
        properties=pika.BasicProperties(correlation_id=props.correlation_id),
        body=json.dumps(response, ensure_ascii=False),
    )
    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    params = pika.URLParameters(RABBIT_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=REQUEST_QUEUE, durable=True)
    channel.queue_declare(queue=RESPONSE_QUEUE, durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=REQUEST_QUEUE, on_message_callback=on_request)

    print(" [x] Awaiting ECG analysis requests")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()


if __name__ == "__main__":
    main()
