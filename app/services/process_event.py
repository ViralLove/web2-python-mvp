#process event

from supabase import Client
from flask import Blueprint, request, jsonify
from app.utils.ai_helper import vectorize_text
from app.utils.geocoding import get_coordinates
from app.db import supabase
import os

IS_DEMO = os.getenv("IS_DEMO")

process_event_bp = Blueprint('submit_event', __name__)

@process_event_bp.route('/submit-event', methods=['POST'])
def process_event():
    data = request.get_json()
    event = data.get("event")
    print(f"Processing event: {event}")
    if not event:
        return jsonify({"error": "Missing 'event' key in JSON"}), 400

    # Проверяем наличие organizer_name
    organizer_name = event["organizer"]["name"];
    print(f"Organizer name: {organizer_name}")
    if not organizer_name:
        return jsonify({"error": "Missing 'organizer_name' in JSON"}), 400

    # Поиск организатора по названию
    organizer_response = supabase.table("organizers").select("id").eq("name", organizer_name).execute()

    # Если организатор не найден, создаём нового
    if not organizer_response.data:
        print(f"Organizer {organizer_name} not found, creating new organizer...")
        new_organizer_data = {
            "name": organizer_name
        }

        # Добавляем description, если оно указано
        organizer_description = event["organizer"]["description"];
        if organizer_description:
            print(f"Organizer description: {organizer_description}")
            new_organizer_data["description"] = organizer_description

        new_organizer = supabase.table("organizers").insert(new_organizer_data).execute()

        if not new_organizer.data:
            return jsonify({"error": "Failed to insert new organizer"}), 500
        
        print(f"New organizer created: {new_organizer.data}")

        organizer_id = new_organizer.data[0]["id"]
    else:
        organizer_id = organizer_response.data[0]["id"]
    
    print(f"Organizer ID: {organizer_id}")
    # Получение координат
    lat, lon = None, None
    if event["location"]["type"] == "physical":
        print(f"Getting coordinates for {event['location']['details']}")
        lat, lon = get_coordinates(event["location"]["details"])

    # output coordinates
    print(f"Coordinates: {lat}, {lon}")

    event_description = event.get("description")
    
    event_data = {
        "name": event["name"],
        "is_demo": IS_DEMO,
        "description": event_description,
        "location_type": event["location"]["type"],
        "location_details": event["location"]["details"],
        "external_links": event.get("external_links", []),  # Массив ссылок на внешние ресурсы, по умолчанию пустой
        "online_access": event.get("online_access"),  # Ссылка для онлайн-доступа, по умолчанию None
        "organizer_id": organizer_id  # Привязка организатора
    }

    # Добавление координат, если они получены
    if lat is not None and lon is not None:
        event_data["location_coords"] = f"SRID=4326;POINT({lon} {lat})"
    
    # Вставляем данные в таблицу 'events'
    event_response = supabase.table("events").insert(event_data).execute()

    if not event_response.data:
        return jsonify({"error": "Failed to insert into 'events' table"}), 500
    
    # Получаем ID вставленного события
    event_id = event_response.data[0]["id"]

    # insert event description embedding into event_description_embeddings table
    if event_description:

        event_description_embedding = vectorize_text(event_description);
        print(f"Event description embedding: {event_description_embedding}")

        supabase.table("event_description_embeddings").insert({
            "event_id": event_id,
            "description_embedding": event_description_embedding
        }).execute()
    
    # event title embedding
    event_title_embedding = vectorize_text(event["name"])
    print(f"Event title embedding: {event_title_embedding}")

    supabase.table("event_title_embeddings").insert({
        "event_id": event_id,
        "title_embedding": event_title_embedding
    }).execute()

    # Вставляем расписание в таблицу 'event_schedules'
    for schedule in event["schedule"]:
        supabase.table("event_schedules").insert({
            "event_id": event_id,
            "start_time": schedule["start_time"],
            "end_time": schedule["end_time"]
        }).execute()

    # Вставляем возрастные группы в таблицу 'event_age_groups'
    for age_group in event["audience"]["age_groups"]:
        print(f"Processing age group: {age_group}")
        # Проверяем, существует ли возрастная группа в словаре
        dictionary_response = supabase.table("dictionary_age_groups").select("id").eq("age_group", age_group).execute()

        if dictionary_response.data:
            # Если возрастная группа уже существует, используем её ID
            age_group_id = dictionary_response.data[0]["id"]
            print(f"Age group {age_group} already exists in dictionary table dictionary_age_groups")
            print(f"Age group ID: {age_group_id}")
        else:
            # Если возрастной группы нет, создаём её в словаре
            new_age_group = supabase.table("dictionary_age_groups").insert({
                "age_group": age_group
            }).execute()

            if not new_age_group.data:
                raise Exception(f"Failed to insert age group '{age_group}' into dictionary.")
            
            # Получаем ID только что созданной возрастной группы
            age_group_id = new_age_group.data[0]["id"]
            print(f"Age group {age_group} created in dictionary table dictionary_age_groups")
            print(f"Age group ID: {age_group_id}")

            # get embedding for age group
            age_group_embedding = vectorize_text(age_group)
            print(f"Age group embedding: {age_group_embedding}")

            age_group_embedding_obj = {
                "age_group_id": age_group_id,
                "embedding": age_group_embedding
            }

            # insert embedding into age_group_embeddings table
            supabase.table("age_group_embeddings").insert(age_group_embedding_obj).execute()

        # Вставляем связь события с возрастной группой
        supabase.table("event_age_groups").insert({
            "event_id": event_id,
            "age_group_id": age_group_id
        }).execute()


    # Вставляем интересы в таблицу 'event_interests'
    for interest in event["audience"]["interests"]:
        # Проверяем, существует ли интерес в словаре
        dictionary_response = supabase.table("dictionary_interests").select("id").eq("interest", interest).execute()

        if dictionary_response.data:
            # Если интерес уже существует, используем его ID
            interest_id = dictionary_response.data[0]["id"]
        else:
            # Если интереса нет, создаём его в словаре
            new_interest = supabase.table("dictionary_interests").insert({
                "interest": interest
            }).execute()

            if not new_interest.data:
                raise Exception(f"Failed to insert interest '{interest}' into dictionary.")

            interest_id = new_interest.data[0]["id"]

            # get embedding for interest
            interest_embedding = vectorize_text(interest)
            print(f"Interest embedding: {interest_embedding}")

            interest_embedding_obj = {
                "interest_id": interest_id,
                "embedding": interest_embedding
            }

            # insert embedding into interest_embeddings table
            supabase.table("interest_embeddings").insert(interest_embedding_obj).execute()

        # Вставляем связь события с интересом
        supabase.table("event_interests").insert({
            "event_id": event_id,
            "interest_id": interest_id
        }).execute()


    # Вставляем языки в таблицу 'event_languages'
    for language in event["audience"]["languages"]:
        # Проверяем, существует ли язык в словаре
        dictionary_response = supabase.table("dictionary_languages").select("id").eq("language", language).execute()

        if dictionary_response.data:
            # Если язык уже существует, используем его ID
            language_id = dictionary_response.data[0]["id"]
        else:
            # Если языка нет, создаём его в словаре
            new_language = supabase.table("dictionary_languages").insert({
                "language": language
            }).execute()

            if not new_language.data:
                raise Exception(f"Failed to insert language '{language}' into dictionary.")

            # Получаем ID только что созданного языка
            language_id = new_language.data[0]["id"]

            # get embedding for language
            language_embedding = vectorize_text(language)
            print(f"Language embedding: {language_embedding}")

            language_embedding_obj = {
                "language_id": language_id,
                "embedding": language_embedding
            }

            # insert embedding into language_embeddings table
            supabase.table("language_embeddings").insert(language_embedding_obj).execute()

        # Вставляем связь события с языком
        supabase.table("event_languages").insert({
            "event_id": event_id,
            "language_id": language_id
        }).execute()


    return jsonify({"message": "Event added successfully"}), 201