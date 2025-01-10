-- Создаем таблицу organizers
CREATE TABLE organizers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE, -- Название организатора (уникальное)
    description TEXT,          -- Описание организатора (опционально)
    created_at TIMESTAMP DEFAULT NOW(), -- Дата создания
    updated_at TIMESTAMP DEFAULT NOW() -- Дата обновления
);

-- Создаем таблицу events
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,                     -- Название события
    description TEXT NOT NULL,              -- Описание события
    location_type TEXT NOT NULL,            -- Тип местоположения (online, physical, hybrid)
    location_details TEXT,                  -- Детали местоположения (адрес или платформа)
    external_links JSONB,                   -- Внешние ссылки (массив JSON)
    online_access TEXT,                     -- Ссылка на онлайн-доступ (опционально)
    organizer_id INT REFERENCES organizers(id) ON DELETE SET NULL, -- Связь с организатором
    created_at TIMESTAMP DEFAULT NOW(),     -- Дата создания
    updated_at TIMESTAMP DEFAULT NOW()      -- Дата обновления
);

-- Пересоздание таблицы event_schedules с необязательным end_time
CREATE TABLE event_schedules (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE, -- Связь с событием
    start_time TIMESTAMP NOT NULL,      -- Время начала
    end_time TIMESTAMP,                 -- Время окончания (опционально)
    created_at TIMESTAMP DEFAULT NOW()  -- Дата создания
);

-- Создаем таблицу dictionary_age_groups
CREATE TABLE dictionary_age_groups (
    id SERIAL PRIMARY KEY,
    age_group TEXT NOT NULL UNIQUE,     -- Возрастная группа
    created_at TIMESTAMP DEFAULT NOW()  -- Дата создания
);

-- Создаем таблицу event_age_groups
CREATE TABLE event_age_groups (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,       -- Связь с событием
    age_group_id INT REFERENCES dictionary_age_groups(id) ON DELETE CASCADE, -- Связь с возрастной группой
    created_at TIMESTAMP DEFAULT NOW()                          -- Дата создания
);

-- Создаем таблицу dictionary_interests
CREATE TABLE dictionary_interests (
    id SERIAL PRIMARY KEY,
    interest TEXT NOT NULL UNIQUE,      -- Интерес
    created_at TIMESTAMP DEFAULT NOW()  -- Дата создания
);

-- Создаем таблицу event_interests
CREATE TABLE event_interests (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,       -- Связь с событием
    interest_id INT REFERENCES dictionary_interests(id) ON DELETE CASCADE, -- Связь с интересом
    created_at TIMESTAMP DEFAULT NOW()                          -- Дата создания
);

-- Создаем таблицу dictionary_languages
CREATE TABLE dictionary_languages (
    id SERIAL PRIMARY KEY,
    language TEXT NOT NULL UNIQUE,      -- Язык
    created_at TIMESTAMP DEFAULT NOW()  -- Дата создания
);

-- Создаем таблицу event_languages
CREATE TABLE event_languages (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,       -- Связь с событием
    language_id INT REFERENCES dictionary_languages(id) ON DELETE CASCADE, -- Связь с языком
    created_at TIMESTAMP DEFAULT NOW()                          -- Дата создания
);

-- Создаем индексы для оптимизации запросов
CREATE INDEX idx_event_schedules_event_id ON event_schedules (event_id);
CREATE INDEX idx_event_age_groups_event_id ON event_age_groups (event_id);
CREATE INDEX idx_event_interests_event_id ON event_interests (event_id);
CREATE INDEX idx_event_languages_event_id ON event_languages (event_id);

-- Эмбеддинги для интересов
CREATE TABLE interest_embeddings (
    id SERIAL PRIMARY KEY,
    interest_id INT REFERENCES dictionary_interests(id) ON DELETE CASCADE, -- Ссылка на словарь
    embedding VECTOR(768) NOT NULL, -- Эмбеддинг интереса
    created_at TIMESTAMP DEFAULT NOW()
);

-- Эмбеддинги для возрастных групп
CREATE TABLE age_group_embeddings (
    id SERIAL PRIMARY KEY,
    age_group_id INT REFERENCES dictionary_age_groups(id) ON DELETE CASCADE, -- Ссылка на словарь
    embedding VECTOR(768) NOT NULL, -- Эмбеддинг возрастной группы
    created_at TIMESTAMP DEFAULT NOW()
);

-- Эмбеддинги для языков
CREATE TABLE language_embeddings (
    id SERIAL PRIMARY KEY,
    language_id INT REFERENCES dictionary_languages(id) ON DELETE CASCADE, -- Ссылка на словарь
    embedding VECTOR(768) NOT NULL, -- Эмбеддинг языка
    created_at TIMESTAMP DEFAULT NOW()
);

-- Эмбеддинги для названия события
CREATE TABLE event_title_embeddings (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    title_embedding VECTOR(768) NOT NULL, -- Эмбеддинг
    created_at TIMESTAMP DEFAULT NOW()
);

-- Эмбеддинги для описания события
CREATE TABLE event_description_embeddings (
    id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    description_embedding VECTOR(768) NOT NULL, -- Эмбеддинг
    created_at TIMESTAMP DEFAULT NOW()
);