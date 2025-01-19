import requests
import jwt
import datetime
import os

SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET')
SUPABASE_FUNCTION_URL = os.getenv('SUPABASE_FUNCTION_URL')

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
