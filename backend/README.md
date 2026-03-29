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

## 6) Быстрый запуск автопроверки PostgreSQL

Схема БД инициализируется автоматически из файла:

`backend/postgres/init_schema.sql`

### 6.1 Поднять PostgreSQL

```bash
docker compose --env-file .env up -d postgres
```

### 6.2 Автоматически прогнать SQL-проверки

```bash
docker compose exec -T postgres psql \
  -U ${POSTGRES_USER:-shop_user} \
  -d ${POSTGRES_DB:-shop_db} \
  -f - < ./db_verification_checks.sql
```

Важно: перед запуском замените тестовые значения прямо в `db_verification_checks.sql`
(`student@example.com`, `Иван Иванов`, `1`) на ваши реальные данные из прогона.

### 6.3 Ручная проверка в SQL IDE

Подключение:
- host: `localhost`
- port: `5432`
- db: `shop_db`
- user: `shop_user`
- password: `shop_pass`

Далее открыть `backend/db_verification_checks.sql`, подставить параметры
и выполнить запросы по блокам.

## 7) Selenium WebDriver (POM) тесты

Подготовлены Page Object Model и e2e сценарии:

- `tests/selenium/pages/home_page.py`
- `tests/selenium/pages/login_page.py`
- `tests/selenium/pages/profile_page.py`
- `tests/selenium/test_e2e_flows.py`

### Установка зависимостей

```bash
python3 -m pip install -r tests/selenium/requirements.txt
```

### Запуск тестов

```bash
pytest -q tests/selenium
```
