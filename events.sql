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
