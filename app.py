from flask import Flask, request, jsonify
from supabase import create_client, Client
import requests
from opencage.geocoder import OpenCageGeocode
import jwt
import datetime

# Настройки Supabase (замени своими значениями)
SUPABASE_URL = "https://fvsmeqeggqlxseneinbc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ2c21lcWVnZ3FseHNlbmVpbmJjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNjY3NzUxMCwiZXhwIjoyMDUyMjUzNTEwfQ.6Lw4Ms-6f46mmXzcObDIPyZYa26Tb6inMyFcPMqY2V0"

SUPABASE_FUNCTION_URL = "https://fvsmeqeggqlxseneinbc.functions.supabase.co/vectorize"
SUPABASE_JWT_SECRET = "zx5hoiz3f1l0f+q1uxSl5cHUHEebAhUCFn7OM4g9ymwopDCEv4YtWymNWVLuy+o8JYV0UfTsaBTQDRhIoxTAZQ=="


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

SCHEMA_NAME = "public"

NOMINATUM_URL = "https://nominatim.openstreetmap.org/search"

OPENCAGE_API_KEY = "24157cbea4534cba954c14a715392e47"

DEFAULT_CITY = "Tallinn"
DEFAULT_COUNTRY = "Estonia"

app = Flask(__name__)

#create a very simple GET endpoint "test" that returns "Hello, World!"
@app.route('/test', methods=['GET'])
def test():
    return "Hello, World!"

@app.route('/add-event', methods=['POST'])
def add_event():
    try:
        print("Adding event...")
        # Получаем JSON из запроса
        data = request.json
        print(f"Received data: {data}")
        if not data:
            return jsonify({"error": "No JSON provided"}), 400

        event = data.get("event")
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/get-event/<int:event_id>', methods=['GET'])
def get_event(event_id):
    try:
        # Вызываем пользовательскую функцию Supabase
        response = supabase.rpc("get_event_details", {"event_id": event_id}).execute()

        # Проверяем результат
        if not response.data:
            return jsonify({"error": "Event not found"}), 404

        # Возвращаем данные
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def get_coordinates(address):

    # if address doesn't contain Tallinn or Estonia then add to it "Tallinn, Estonia". Make sure Tallinn and/or Estonia are not displayed twice 
    if DEFAULT_CITY not in address and DEFAULT_COUNTRY not in address:
        address = f"{address}, {DEFAULT_CITY}, {DEFAULT_COUNTRY}"

    # if address doesn't contain "Tallinn" then add to it "Tallinn"
    if DEFAULT_CITY not in address:
        address = f"{address}, {DEFAULT_CITY}"

    # if address doesn't contain "Estonia" then add to it "Estonia"
    if DEFAULT_COUNTRY not in address:
        address = f"{address}, {DEFAULT_COUNTRY}"


    # Check if address is already registered in dictionary and return coordinates
    dictionary_response = supabase.table("address_directory").select("*").eq("address", address).execute()
    if dictionary_response.data:
        # print address retrieved from dictionary with all parameters printed one by one
        print(f"Address {address} already registered in dictionary table address_directory")
        print(f"Address retrieved from dictionary: {dictionary_response.data[0]}")
        print(f"Latitude: {dictionary_response.data[0]['latitude']}")
        print(f"Longitude: {dictionary_response.data[0]['longitude']}")

        return dictionary_response.data[0]["latitude"], dictionary_response.data[0]["longitude"]

    # Otherwise return getNominatumCoordinates(address)
    return getOpenCageCoordinates(address)

def getOpenCageCoordinates(address):
    geocoder = OpenCageGeocode(key=OPENCAGE_API_KEY)
    results = geocoder.geocode(address)
    if results:
        return results[0]['geometry']['lat'], results[0]['geometry']['lng']
    return None, None

# Глобальная переменная для токена
cached_token = None
cached_token_expiration = None

def get_cached_jwt():

    print(f"Getting cached JWT...")
    global cached_token, cached_token_expiration

    # Проверяем, есть ли токен в кэше и он ещё действителен
    if cached_token and cached_token_expiration > datetime.datetime.utcnow():
        print(f"Cached JWT found: {cached_token}")
        return cached_token

    # Создаём новый токен
    payload = {
        "sub": "user_id",  # Уникальный ID пользователя
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Время жизни токена
        "aud": "authenticated",  # Аудитория
    }
    cached_token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
    cached_token_expiration = payload["exp"]

    print(f"New token created: {cached_token}")
    print(f"Token expiration: {cached_token_expiration}")

    return cached_token

def vectorize_text(text: str):
    print(f"Vectorizing text: {text}")
    headers = {
        "Authorization": f"Bearer {get_cached_jwt()}",
        "Content-Type": "application/json",
    }
    print(f"Headers: {headers}")
    payload = {"input": text}
    print(f"Payload: {payload}")

    try:
        response = requests.post(SUPABASE_FUNCTION_URL, json=payload, headers=headers)
        
        # Проверка успешности запроса
        if response.status_code == 200:
            embeddings = response.json().get("embedding")
            
            return embeddings
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            print(f"Response headers: {response.headers}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def getNominatumCoordinates(address):
    # if not, get coordinates from nominatum
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "Estonians888/1.0 (zeya.metsapuu@gmail.com)"
    }
    try:
        response = requests.get(NOMINATUM_URL, params=params, headers=headers)
        print(f"Response status: {response.status_code}, Response content: {response.text}")
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            # insert address into dictionary table address_directory
            supabase.table("address_directory").insert({
                "address": address,
                "latitude": data["lat"],
                "longitude": data["lon"],
                "city": DEFAULT_CITY,
                "country": DEFAULT_COUNTRY
            }).execute()
            return float(data["lat"]), float(data["lon"])
        return None, None
    except Exception as e:
        print(f"Error getting coordinates: {e}")
        return None, None

if __name__ == '__main__':
    app.run(debug=True, port=5000)
