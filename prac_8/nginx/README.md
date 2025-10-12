# API Gateway with Nginx

Nginx конфигурация как API Gateway с интеграцией auth сервиса для проверки токенов.

## Функции

- **Аутентификация**: Проверка JWT токенов через auth сервис
- **Маршрутизация**: Проксирование запросов к соответствующим сервисам
- **Rate Limiting**: Ограничение количества запросов
- **CORS**: Поддержка кросс-доменных запросов
- **WebSocket**: Поддержка WebSocket соединений
- **Health Checks**: Проверка состояния сервисов

## Архитектура

```
Client → Nginx Gateway → Auth Service (verify token)
                      ↓
                   Chat Service / ECG Analysis Service
```

## Маршруты

### Публичные (без аутентификации):
- `/auth/*` → Auth Service (регистрация, логин)

### Защищенные (с аутентификацией):
- `/v1/measurements/*` → Chat Service
- `/v1/analysis/*` → ECG Analysis Service
- `/ws/*` → WebSocket соединения

## Запуск

1. Запустите все сервисы:
```bash
docker-compose up -d
```

2. Проверьте статус:
```bash
docker-compose ps
```

3. Проверьте логи:
```bash
docker-compose logs nginx
```

## Использование

### Регистрация пользователя:
```bash
curl -X POST http://localhost/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123", "email": "user@example.com"}'
```

### Получение токена:
```bash
curl -X POST http://localhost/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=password123"
```

### Использование API с токеном:
```bash
curl -X GET http://localhost/v1/measurements \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### WebSocket соединение:
```javascript
const ws = new WebSocket('ws://localhost/ws/user123?token=YOUR_JWT_TOKEN');
```

## Конфигурация

### Переменные окружения:
- `SECRET_KEY` - Секретный ключ для JWT
- `DATABASE_URL` - URL подключения к PostgreSQL
- `MINIO_*` - Настройки MinIO
- `RABBIT_URL` - URL подключения к RabbitMQ

### Rate Limiting:
- Auth endpoints: 5 запросов/сек
- API endpoints: 10 запросов/сек
- Burst: 10-20 запросов

### Timeouts:
- Connect: 5-10 секунд
- Send/Read: 60-300 секунд
- WebSocket: 24 часа

## Мониторинг

### Health Check:
```bash
curl http://localhost/health
```

### Метрики:
```bash
curl http://localhost/metrics
```

### Логи:
```bash
docker-compose logs -f nginx
```

## Безопасность

- JWT токены проверяются через auth сервис
- Rate limiting защищает от DDoS
- CORS настроен для кросс-доменных запросов
- Security headers добавлены
- Внутренние endpoints недоступны извне

## Troubleshooting

### Проверка подключения к сервисам:
```bash
docker-compose exec nginx nslookup auth_service
docker-compose exec nginx nslookup chat_service
```

### Проверка auth сервиса:
```bash
curl http://localhost/auth/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Проверка WebSocket:
```bash
wscat -c ws://localhost/ws/test?token=YOUR_TOKEN
```
