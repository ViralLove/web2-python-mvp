import jwt
import datetime
import os
# Your Supabase secret
jwt_secret = os.getenv('SUPABASE_JWT_SECRET')

# Create JWT token
payload = {
    "sub": "user_id",  # Unique user identifier (can be any)
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),  # Token expiration time
    "aud": "authenticated",  # Token audience, check Supabase settings
}
token = jwt.encode(payload, jwt_secret, algorithm="HS256")

print("EVT: Your JWT secret:", jwt_secret)
print("EVT: Your JWT token:", token)
