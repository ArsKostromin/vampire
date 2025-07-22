-- Создание ролей и ограничение прав для PostgreSQL

-- 1. Создать роль server_admin с паролем (замените пароль на свой)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'server_admin') THEN
        CREATE ROLE server_admin LOGIN PASSWORD 'Qg43w234';
    END IF;
END$$;

-- 2. Создать роль api_user с паролем (замените пароль на свой)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'api_user') THEN
        CREATE ROLE api_user LOGIN PASSWORD 'Qg43w234';
    END IF;
END$$;

-- 3. Дать server_admin все права на все таблицы
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO server_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO server_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO server_admin;

-- 4. Дать api_user только SELECT, INSERT, UPDATE на таблицу users
REVOKE ALL ON TABLE users FROM api_user;
GRANT SELECT, INSERT, UPDATE ON TABLE users TO api_user;

-- 5. Запретить api_user удалять, изменять структуру и выполнять опасные операции
REVOKE DELETE, TRUNCATE, REFERENCES, TRIGGER ON TABLE users FROM api_user;
REVOKE CREATE ON SCHEMA public FROM api_user;

-- 6. (Опционально) Ограничить подключение server_admin только с localhost (делается в pg_hba.conf на сервере)
-- host    all    server_admin    127.0.0.1/32    md5 