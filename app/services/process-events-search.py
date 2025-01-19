import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from utils.ai_helper import vectorize_text
import os

DATABASE_URL = os.getenv("DATABASE_URL")

def build_query(criteria):
    """
    Формирует динамический SQL-запрос на основе входных критериев поиска,
    включая возрастные категории, языки и эмбеддинги описаний событий.
    """
    query = """
        SELECT 
            e.id,
            e.name,
            e.description,
            s.start_time,
            s.end_time,
            e.location_coords,
            o.name AS organizer_name,
            1 - (ie.embedding <=> %s) AS interest_similarity,
            1 - (ade.description_embedding <=> %s) AS description_similarity,
            e.location_type,
            e.location_details,
            e.external_links,
            e.online_access,
            e.created_at AS event_created_at,
            e.updated_at AS event_updated_at
        FROM events e
        JOIN event_schedules s ON e.id = s.event_id
        LEFT JOIN organizers o ON e.organizer_id = o.id
        LEFT JOIN event_interests ei ON e.id = ei.event_id
        LEFT JOIN interest_embeddings ie ON ei.interest_id = ie.interest_id
        LEFT JOIN event_age_groups eag ON e.id = eag.event_id
        LEFT JOIN dictionary_age_groups dag ON eag.age_group_id = dag.id
        LEFT JOIN age_group_embeddings age_emb ON dag.id = age_emb.age_group_id
        LEFT JOIN event_languages el ON e.id = el.event_id
        LEFT JOIN dictionary_languages dl ON el.language_id = dl.id
        LEFT JOIN language_embeddings lang_emb ON dl.id = lang_emb.language_id
        LEFT JOIN event_description_embeddings ade ON e.id = ade.event_id
        WHERE TRUE
    """
    params = []

    # Фильтрация по организатору
    if criteria.get("organizer"):
        query += " AND o.name ILIKE %s"
        params.append(f"%{criteria['organizer']}%")

    # Фильтрация по диапазону дат
    query, params = appendDateRange(criteria.get("date_range"), query, params)

    # Фильтрация по конкретным датам
    query, params = appendSpecificDates(criteria.get("specific_dates"), query, params)

    # Фильтрация по дням недели
    query, params = appendWeeklySchedule(criteria.get("weekly_schedule"), query, params)

    # Фильтрация по локациям
    query, params = appendLocations(criteria.get("locations"), query, params)

    # Фильтрация для только онлайн событий
    if criteria.get("online_only"):
        query += " AND e.location_type = 'online'"

    # Сортировка
    sort_field = criteria.get("sort", {}).get("field", "start_time")
    sort_order = criteria.get("sort", {}).get("order", "asc")
    query += f" ORDER BY {sort_field} {sort_order}"

    # Пагинация
    page = criteria.get("pagination", {}).get("page", 1)
    page_size = criteria.get("pagination", {}).get("page_size", 20)
    offset = (page - 1) * page_size
    query += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])

    return query, params

def appendLocations(locations, query, params):
    if not locations:
        return query, params

    location_conditions = []
    for location in locations:
        longitude = location.get("longitude")
        latitude = location.get("latitude")
        radius_km = location.get("radius_km")

        # Проверка на наличие всех необходимых данных
        if longitude is not None and latitude is not None and radius_km is not None:
            location_conditions.append("""
                ST_DWithin(
                    e.location_coords,
                    ST_SetSRID(ST_Point(%s, %s), 4326),
                    %s
                )
            """)
            params.extend([longitude, latitude, radius_km * 1000])

    if location_conditions:
        query += " AND (" + " OR ".join(location_conditions) + ")"

    return query, params


def appendDateRange(date_range, query, params):
    if not date_range:
        return query, params

    # Добавляем условие диапазона дат
    query += " AND s.start_time >= %s AND s.end_time <= %s"
    params.extend([date_range["start_date"], date_range["end_date"]])

    return query, params


def appendSpecificDates(specific_dates, query, params):
    if not specific_dates:
        return query, params

    # Создаем условия для каждой конкретной даты
    date_conditions = []
    for date_obj in specific_dates:
        date = date_obj["date"]
        start_time = date_obj["time_range"]["start"]
        end_time = date_obj["time_range"]["end"]
        
        # Формируем условие SQL
        date_conditions.append(
            "(DATE(s.start_time) = %s AND EXTRACT(HOUR FROM s.start_time) BETWEEN %s AND %s)"
        )
        
        # Добавляем параметры
        params.extend([date, start_time.split(":")[0], end_time.split(":")[0]])

    # Добавляем условия в запрос
    if date_conditions:
        query += " AND (" + " OR ".join(date_conditions) + ")"

    return query, params

def appendWeeklySchedule(weekly_schedule, query, params):
    if not weekly_schedule:
        return query, params

    # Создаем условия для каждого дня недели
    weekly_conditions = []
    for schedule in weekly_schedule:
        day_of_week = schedule["day_of_week"]
        start_hour = schedule["time_range"]["start"].split(":")[0]
        end_hour = schedule["time_range"]["end"].split(":")[0]
        
        # Формируем условие SQL
        weekly_conditions.append(
            "(EXTRACT(DOW FROM s.start_time) = %s AND EXTRACT(HOUR FROM s.start_time) BETWEEN %s AND %s)"
        )
        
        # Добавляем параметры
        params.extend([day_of_week, start_hour, end_hour])

    # Добавляем условия в запрос
    if weekly_conditions:
        query += " AND (" + " OR ".join(weekly_conditions) + ")"

    return query, params


def appendDescriptionEmbeddings(keywords, query, params, vectorize_text):
    if not keywords:
        return query, params

    # Преобразование ключевых слов в эмбеддинги
    keyword_embeddings = [vectorize_text(keyword) for keyword in keywords]

    # Добавление условий для каждого эмбеддинга ключевого слова
    description_conditions = []
    for embedding in keyword_embeddings:
        description_conditions.append("1 - (ade.description_embedding <=> %s) > 0.7")
        params.append(embedding)

    # Объединяем все условия в запрос
    if description_conditions:
        query += " AND (" + " OR ".join(description_conditions) + ")"

    return query, params


def appendInterestsEmbeddings(interests, query, params):
    if not interests:
        return query, params

    # Векторизация интересов
    user_embeddings = [vectorize_text(interest) for interest in interests]

    # Добавление условий для каждого интереса
    interest_conditions = []
    for user_embedding in user_embeddings:
        # Добавляем условие для косинусного расстояния с порогом схожести
        interest_conditions.append("1 - (ie.embedding <=> %s) > 0.7")
        params.append(user_embedding)

    # Объединяем все условия для интересов в логике WHERE
    if interest_conditions:
        query += " AND (" + " OR ".join(interest_conditions) + ")"

    return query, params

def appendLanguagesEmbeddings(languages, query, params):

    if not languages:
        return query, params
    
    # Векторизация языков
    user_embeddings = [vectorize_text(language) for language in languages]

    # Добавление условий для каждого языка
    language_conditions = []
    for user_embedding in user_embeddings:
        language_conditions.append("1 - (lang_emb.embedding <=> %s) > 0.7")
        params.append(user_embedding)

    # Объединяем все условия для языков в логике WHERE
    if language_conditions:
        query += " AND (" + " OR ".join(language_conditions) + ")"

    return query, params

def appendAgeGroupsEmbeddings(age_groups, query, params):
    if not age_groups:
        return query, params
    
    # Векторизация возрастных групп
    user_embeddings = [vectorize_text(age_group) for age_group in age_groups]

    # Добавление условий для каждой возрастной группы
    age_group_conditions = []
    for user_embedding in user_embeddings:
        age_group_conditions.append("1 - (age_emb.embedding <=> %s) > 0.7")
        params.append(user_embedding)

    # Объединяем все условия для возрастных групп в логике WHERE
    if age_group_conditions:
        query += " AND (" + " OR ".join(age_group_conditions) + ")"

    return query, params


def execute_query(criteria):
    """
    Выполняет SQL-запрос с использованием построенного запроса и критериев.
    """
    query, params = build_query(criteria)

    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            results = cur.fetchall()
        return results
    finally:
        conn.close()