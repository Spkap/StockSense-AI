from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from django.contrib.auth import get_user_model

User = get_user_model()

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        id_token = auth_header.split(" ")[1]
        try:
            decoded = auth.verify_id_token(id_token)
        except Exception:
            raise AuthenticationFailed("Invalid Firebase token")

        uid = decoded["uid"]
        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            raise AuthenticationFailed("No such user")
        
        return (user, None)



