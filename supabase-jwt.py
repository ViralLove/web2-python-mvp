import jwt
import datetime

# Ваш секрет из Supabase
jwt_secret = "zx5hoiz3f1l0f+q1uxSl5cHUHEebAhUCFn7OM4g9ymwopDCEv4YtWymNWVLuy+o8JYV0UfTsaBTQDRhIoxTAZQ=="

# Создание токена
payload = {
    "sub": "user_id",  # Уникальный идентификатор пользователя (может быть любой)
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Время жизни токена
    "aud": "authenticated",  # Аудитория токена, проверьте настройки Supabase
}
token = jwt.encode(payload, jwt_secret, algorithm="HS256")

print("Ваш токен JWT:", token)
