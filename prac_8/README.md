# ECG Measurements System

Микросервисная система для анализа ЭКГ данных с API Gateway, аутентификацией и real-time уведомлениями.

## Архитектура

```
Client → Nginx Gateway → Auth Service (JWT validation)
                      ↓
                   Chat Service (measurements)
                      ↓
                   ECG Analysis Service (processing)
```

## Сервисы

### 1. **Nginx API Gateway** (`nginx/`)
- Центральная точка входа для всех запросов
- Проверка JWT токенов через auth сервис
- Маршрутизация к соответствующим сервисам
- Rate limiting и CORS поддержка
- WebSocket проксирование

### 2. **Auth Service** (`auth_service/`)
- FastAPI сервис аутентификации
- Регистрация и авторизация пользователей
- JWT токены
- PostgreSQL для хранения пользователей

### 3. **Chat Service** (`chat_service/`)
- FastAPI сервис для работы с измерениями ЭКГ
- Загрузка файлов в MinIO
- Отправка сообщений в RabbitMQ
- WebSocket для real-time уведомлений
- PostgreSQL для хранения измерений

### 4. **ECG Analysis Service** (`ecg_analysis_service/`)
- Python сервис анализа ЭКГ данных
- Обработка сообщений из RabbitMQ
- Загрузка файлов из MinIO
- Анализ сигналов с помощью neurokit2
- Отправка результатов обратно в RabbitMQ

## Инфраструктура

- **PostgreSQL**: База данных для всех сервисов
- **MinIO**: Object storage для файлов ЭКГ
- **RabbitMQ**: Message broker для асинхронной обработки
- **Nginx**: API Gateway и reverse proxy

## Быстрый старт

### 1. Клонирование и запуск:

```bash
# Клонировать репозиторий
git clone <repository-url>
cd <project-directory>

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

### 2. Проверка работы:

```bash
# Health check
curl http://localhost/health

# Регистрация пользователя
curl -X POST http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123", "email": "user@example.com"}'

# Получение токена
curl -X POST http://localhost/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=password123"
```

### 3. Использование API:

```bash
# Создание измерения
curl -X POST http://localhost/v1/measurements \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@ecg.csv" \
  -F "fs=200" \
  -F "state=rest"

# Получение измерений пользователя
curl -X GET http://localhost/v1/measurements \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## API Endpoints

### Auth Service (`/auth/`)
- `POST /register` - Регистрация пользователя
- `POST /login` - Авторизация и получение токена
- `GET /verify` - Проверка токена
- `GET /me` - Информация о текущем пользователе

### Chat Service (`/v1/measurements`)
- `POST /v1/measurements` - Создание измерения из файла
- `POST /v1/measurements/json` - Создание измерения из JSON
- `GET /v1/measurements` - Получение всех измерений пользователя
- `GET /v1/measurements/{id}` - Получение конкретного измерения
- `PATCH /v1/measurements/{id}` - Обновление состояния измерения
- `WS /ws/{user_id}` - WebSocket для real-time уведомлений

## Переменные окружения

### Auth Service:
- `SECRET_KEY` - Секретный ключ для JWT
- `DATABASE_URL` - URL подключения к PostgreSQL

### Chat Service:
- `DATABASE_URL` - URL подключения к PostgreSQL
- `MINIO_ENDPOINT` - Endpoint MinIO сервера
- `MINIO_ACCESS_KEY` - Access key для MinIO
- `MINIO_SECRET_KEY` - Secret key для MinIO
- `RABBIT_URL` - URL подключения к RabbitMQ

### ECG Analysis Service:
- `RABBIT_URL` - URL подключения к RabbitMQ
- `MINIO_ENDPOINT` - Endpoint MinIO сервера
- `MINIO_ACCESS_KEY` - Access key для MinIO
- `MINIO_SECRET_KEY` - Secret key для MinIO

## Мониторинг

### Логи:
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f auth_service
docker-compose logs -f chat_service
docker-compose logs -f ecg_analysis_service
docker-compose logs -f nginx
```

### Health Checks:
```bash
# API Gateway
curl http://localhost/health

# Auth Service
curl http://localhost:8000/health

# Chat Service
curl http://localhost:8080/health
```

### Веб-интерфейсы:
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

## Разработка

### Локальная разработка:

```bash
# Установка зависимостей для auth_service
cd auth_service
pip install -r requirements.txt
uvicorn auth_service:app --reload

# Установка зависимостей для chat_service
cd chat_service
pip install -r requirements.txt
python main.py

# Установка зависимостей для ecg_analysis_service
cd ecg_analysis_service
pip install -r requirements.txt
python service.py
```

### Тестирование:

```bash
# Запуск тестов
cd auth_service && python -m pytest
cd chat_service && python -m pytest
cd ecg_analysis_service && python -m pytest
```

## Структура проекта

```
├── auth_service/           # Сервис аутентификации
│   ├── Dockerfile
│   ├── requirements.txt
│   └── auth_service.py
├── chat_service/          # Сервис измерений ЭКГ
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── models.py
│   ├── services.py
│   └── database.py
├── ecg_analysis_service/  # Сервис анализа ЭКГ
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── service.py
│   ├── modelt.py
│   └── ecg.csv
├── nginx/                 # API Gateway
│   ├── nginx.conf
│   ├── init.sql
│   └── Dockerfile
├── docker-compose.yml     # Оркестрация всех сервисов
└── README.md
```

## Troubleshooting

### Проблемы с подключением:
```bash
# Проверка сети
docker-compose exec nginx ping auth_service
docker-compose exec nginx ping chat_service

# Проверка портов
docker-compose port auth_service 8000
docker-compose port chat_service 8080
```

### Проблемы с базой данных:
```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U user -d postgres

# Проверка таблиц
docker-compose exec postgres psql -U user -d auth_db -c "\dt"
docker-compose exec postgres psql -U user -d chat_db -c "\dt"
```

### Проблемы с RabbitMQ:
```bash
# Проверка очередей
docker-compose exec rabbitmq rabbitmqctl list_queues

# Проверка подключений
docker-compose exec rabbitmq rabbitmqctl list_connections
```
