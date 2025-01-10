ALTER TABLE events
ADD COLUMN IF NOT EXISTS external_links JSONB, -- Массив ссылок на соцсети/внешние сайты
ADD COLUMN IF NOT EXISTS online_access TEXT;  -- Ссылка для онлайн-доступа

-- MERGE для синхронизации данных между старой и новой версией события
INSERT INTO events (id, name, description, location_type, location_details, external_links, online_access)
VALUES
    (1, 'Йога для начинающих', 'Мастер-класс по йоге', 'online', 'Zoom link will be provided', '["https://facebook.com/event"]', 'https://zoom.us/j/1234567890')
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    location_type = EXCLUDED.location_type,
    location_details = EXCLUDED.location_details,
    external_links = EXCLUDED.external_links,
    online_access = EXCLUDED.online_access;



-- Главная таблица для событий
CREATE TABLE events (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор события
    name TEXT NOT NULL, -- Название события
    description TEXT, -- Описание события
    location_type TEXT, -- Тип местоположения (например, online/offline)
    location_details TEXT -- Подробности о местоположении (например, адрес или ссылка на Zoom)
);

-- Таблица для расписания событий
CREATE TABLE event_schedules (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор расписания
    event_id INT REFERENCES events (id) ON DELETE CASCADE, -- Внешний ключ на события
    start_time TIMESTAMP NOT NULL, -- Время начала события
    end_time TIMESTAMP NOT NULL -- Время окончания события
);

-- Таблица для аудитории событий (возрастные группы)
CREATE TABLE event_age_groups (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор
    event_id INT REFERENCES events (id) ON DELETE CASCADE, -- Внешний ключ на события
    age_group TEXT CHECK (age_group IN ('children', 'teens', 'adults', 'seniors')) -- Группа по возрасту
);

-- Таблица для интересов аудитории событий
CREATE TABLE event_interests (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор
    event_id INT REFERENCES events (id) ON DELETE CASCADE, -- Внешний ключ на события
    interest TEXT -- Интерес (например, спорт, искусство, йога и т.д.)
);

-- Таблица для языков аудитории событий
CREATE TABLE event_languages (
    id SERIAL PRIMARY KEY, -- Уникальный идентификатор
    event_id INT REFERENCES events (id) ON DELETE CASCADE, -- Внешний ключ на события
    language TEXT -- Язык аудитории (например, English, Russian и т.д.)
);
