-- ============================================================
-- Проверка БД после автотестов (ручной прогон в SQL IDE)
-- Файл: backend/db_verification_checks.sql
-- ============================================================
--
-- Перед запуском замените тестовые значения в запросах:
--   'student@example.com' -> email пользователя из теста регистрации
--   'Иван Иванов'         -> ожидаемое имя пользователя (если поле name есть)
--   1                     -> реальные ID (order_id/user_id/product_id/comment_id)
--
-- Примечание:
-- Запросы ниже ориентированы на типичную реляционную схему:
--   users, orders, order_items, comments
-- При необходимости адаптируйте имена таблиц/полей под свою БД.

/* ============================================================
   1) Регистрация пользователя
   ============================================================ */

-- 1.1 Проверка, что запись появилась в users
SELECT COUNT(*) AS users_count
FROM users
WHERE email = 'student@example.com';

-- 1.2 Проверка корректности ключевых полей
SELECT
    id,
    email,
    name,
    is_active,
    created_at
FROM users
WHERE email = 'student@example.com';

-- 1.3 (Опционально) Сравнение с ожидаемыми значениями
SELECT COUNT(*) AS users_expected_match
FROM users
WHERE email = 'student@example.com'
  AND name = 'Иван Иванов'
  AND is_active = TRUE;


/* ============================================================
   2) Оформление заказа
   ============================================================ */

-- 2.1 Проверка, что заказ появился в orders
SELECT COUNT(*) AS orders_count
FROM orders
WHERE id = 1
  AND user_id = 1;

-- 2.2 Проверка корректности полей заказа
SELECT
    id,
    user_id,
    status,
    total_amount,
    created_at
FROM orders
WHERE id = 1;

-- 2.3 Проверка дочерних строк заказа (order_items)
SELECT COUNT(*) AS order_items_count
FROM order_items
WHERE order_id = 1;

-- 2.4 Проверка корректности конкретной позиции заказа
SELECT
    order_id,
    product_id,
    quantity,
    unit_price
FROM order_items
WHERE order_id = 1
  AND product_id = 1;


/* ============================================================
   3) Добавление комментария (если есть comments)
   ============================================================ */

-- 3.1 Проверка появления комментария
SELECT COUNT(*) AS comments_count
FROM comments
WHERE id = 1
  AND user_id = 1;

-- 3.2 Проверка полей комментария
SELECT
    id,
    user_id,
    product_id,
    content,
    created_at
FROM comments
WHERE id = 1;


/* ============================================================
   4) Проверка каскадных связей
   ============================================================ */

-- ВНИМАНИЕ: выполнять на тестовой БД.
-- Ниже безопасный шаблон в транзакции: удаляем и откатываем изменения.
-- Для PostgreSQL:
BEGIN;

-- 4.1 Проверка каскада orders -> order_items
--     Если настроен ON DELETE CASCADE, после удаления orders
--     дочерние order_items должны исчезнуть.
DELETE FROM orders
WHERE id = 1;

SELECT COUNT(*) AS remaining_order_items_after_parent_delete
FROM order_items
WHERE order_id = 1;

-- 4.2 Проверка каскада users -> orders/comments (если предусмотрено)
DELETE FROM users
WHERE id = 1;

SELECT COUNT(*) AS remaining_orders_after_user_delete
FROM orders
WHERE user_id = 1;

SELECT COUNT(*) AS remaining_comments_after_user_delete
FROM comments
WHERE user_id = 1;

-- Откат, чтобы не портить тестовые данные
ROLLBACK;


/* ============================================================
   5) Проверка ограничений ссылочной целостности (FK)
   ============================================================ */

-- 5.1 orphan-проверка: order_items без родительского orders
SELECT oi.*
FROM order_items oi
LEFT JOIN orders o ON o.id = oi.order_id
WHERE o.id IS NULL;

-- 5.2 orphan-проверка: orders без существующего users
SELECT o.*
FROM orders o
LEFT JOIN users u ON u.id = o.user_id
WHERE u.id IS NULL;

-- 5.3 orphan-проверка: comments без существующего users
SELECT c.*
FROM comments c
LEFT JOIN users u ON u.id = c.user_id
WHERE u.id IS NULL;
