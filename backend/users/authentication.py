from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from django.contrib.auth import get_user_model
import os
import firebase_utils  

User = get_user_model()

class FirebaseAuthentication(BaseAuthentication):
    def authenticate(self, request):
        # Skip Firebase authentication in test environments
        is_testing = (
            os.getenv('DJANGO_SETTINGS_MODULE', '').endswith('test') or
            'test' in os.getenv('DATABASE_URL', '') or
            os.getenv('TESTING', '').lower() == 'true'
        )
        
        if is_testing:
            # In test environment, skip authentication or use a test user
            return None
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        id_token = auth_header.split(" ")[1]
        try:
            # Check if Firebase is properly initialized
            if firebase_utils.firebase_config is None:
                raise AuthenticationFailed("Firebase not configured")
                
            decoded = auth.verify_id_token(id_token)
        except Exception as e:
            raise AuthenticationFailed(f"Invalid Firebase token: {str(e)}")

        uid = decoded["uid"]
        try:
            user = User.objects.get(firebase_uid=uid)
        except User.DoesNotExist:
            raise AuthenticationFailed("No such user")
        
        return (user, None)



