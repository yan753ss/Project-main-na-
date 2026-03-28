# Backend запуск

## 1) Подготовка переменных окружения

```bash
cd backend
cp .env.example .env
```

При необходимости отредактируйте `.env`.

## 2) Запуск всех сервисов

```bash
docker compose --env-file .env up --build
```

## 3) Проверка

- User: `http://localhost:8000/health`
- Product: `http://localhost:8001/health`
- Order: `http://localhost:8002/health`
- Notification: `http://localhost:8003/health`
- RabbitMQ UI: `http://localhost:15672` (`guest/guest`)

## 4) Остановка

```bash
docker compose down
```
