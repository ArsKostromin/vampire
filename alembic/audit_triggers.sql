-- 1. Функция для логирования изменений в users
CREATE OR REPLACE FUNCTION log_user_changes() RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log(table_name, operation, user_id, username, new_record)
        VALUES ('users', 'INSERT', NEW.id, NEW.name, row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log(table_name, operation, user_id, username, old_record, new_record)
        VALUES ('users', 'UPDATE', NEW.id, NEW.name, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- 2. Триггеры на users
DROP TRIGGER IF EXISTS trg_log_user_insert ON users;
CREATE TRIGGER trg_log_user_insert
AFTER INSERT ON users
FOR EACH ROW EXECUTE FUNCTION log_user_changes();

DROP TRIGGER IF EXISTS trg_log_user_update ON users;
CREATE TRIGGER trg_log_user_update
AFTER UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION log_user_changes();

-- 3. (Опционально) Функция для логирования попыток авторизации
CREATE OR REPLACE FUNCTION log_auth_attempt(_username TEXT, _success BOOLEAN, _extra TEXT DEFAULT NULL) RETURNS void AS $$
BEGIN
    INSERT INTO audit_log(table_name, operation, username, event_time, extra)
    VALUES ('users', 'LOGIN_ATTEMPT', _username, now(),
        CASE WHEN _success THEN 'success' ELSE 'fail' END || COALESCE(' ' || _extra, ''));
END;
$$ LANGUAGE plpgsql;

-- Пример вызова для логирования попытки авторизации:
-- SELECT log_auth_attempt('user1', true, 'ip=1.2.3.4'); 