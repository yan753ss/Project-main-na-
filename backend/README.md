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
  -v email="'student@example.com'" \
  -v expected_name="'Иван Иванов'" \
  -v order_id=1 \
  -v user_id=1 \
  -v product_id=1 \
  -v comment_id=1 \
  -f - < ./db_verification_checks.sql
```

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

### 7.1 Что нужно перед запуском

1. Установить Python-зависимости:

```bash
cd ..
python3 -m pip install -r tests/selenium/requirements.txt
```

2. Убедиться, что в системе установлен браузер (`google-chrome`, `chromium` или `firefox`).
3. Для офлайн-среды установить локальный драйвер (`chromedriver` или `geckodriver`) и, при необходимости,
   задать путь через переменные `CHROMEDRIVER` / `GECKODRIVER`.

По умолчанию тесты сначала ищут локальный драйвер, и только потом пытаются скачать его через `webdriver-manager`.

### 7.2 Запуск всех Selenium тестов

```bash
cd ..
python3 -m pytest -q tests/selenium
```

### 7.3 Запуск одного сценария (пример)

```bash
cd ..
python3 -m pytest -q tests/selenium/test_e2e_flows.py -k login
```

Если браузер не установлен, тесты будут помечены как `skipped` (это ожидаемо).

Если команда `pytest` не найдена, запускайте именно через модуль Python:
`python3 -m pytest ...` (как в примерах выше).

Если интернета нет и появляется ошибка `Could not reach host`, это означает, что
`webdriver-manager` не смог скачать драйвер — используйте локальный `chromedriver`/`geckodriver`.
Если ошибка содержит `cannot find Chrome binary`, значит в системе нет самого браузера (нужен `google-chrome`/`chromium`/`firefox`), а не только драйвера.


