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

По умолчанию `product` запускается в режиме `PRODUCT_STORAGE=mongodb`.
Если MongoDB недоступна, `product_service` автоматически переключается
на fallback in-memory режим на уровне приложения.

В `docker-compose.yml` также добавлен PostgreSQL:
- host: `localhost`
- port: `5432`
- db: `shop_db`
- user: `shop_user`
- password: `shop_pass`

`order_service` по умолчанию также использует MongoDB
(`ORDER_STORAGE=mongodb`, коллекция `orders`) и переключается
на fallback in-memory только если MongoDB недоступна.

## 3) Проверка

- User: `http://localhost:8000/health`
- Product: `http://localhost:8001/health`
- Order: `http://localhost:8002/health`
- Notification: `http://localhost:8003/health`
- RabbitMQ UI: `http://localhost:15672` (`guest/guest`)
- PostgreSQL: `localhost:5432` (`shop_user/shop_pass`, DB `shop_db`)

## 4) Остановка

```bash
docker compose down
```

## 5) SQL-проверки БД для отчета

Готовые проверочные SQL-запросы сохранены в файле:

`backend/db_verification_checks.sql`

Используйте их после автотестов в SQL IDE (DBeaver/DataGrip/phpMyAdmin),
подставив свои значения параметров (`:email`, `:order_id`, `:user_id` и т.д.).
