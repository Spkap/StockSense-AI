from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from firebase_admin import auth
import firebase_utils


User = get_user_model()

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    # Explicitly allow any user to access this endpoint
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        id_token = request.data.get("idToken")
        if not id_token:
            return Response({"detail": "idToken required"}, status=400)

        try:
            decoded = auth.verify_id_token(id_token)
        except Exception as e:
            return Response({"detail": "Invalid token", "error": str(e)}, status=401)

        uid = decoded["uid"]
        email = decoded.get("email")
        name = decoded.get("name", "")
        picture = decoded.get("picture", "")
        email_verified = decoded.get("email_verified", False)

        user, _ = User.objects.get_or_create(
            firebase_uid=uid,
            defaults={
                "username": email or uid,
                "email": email or "",
                "first_name": name.split(" ")[0] if name else "",
                "last_name": " ".join(name.split(" ")[1:]) if name else "",
                "picture": picture,
                "email_verified": email_verified,
            },
        )

        return Response({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "uid": uid,
                "email": email,
                "name": name,
                "picture": picture,
                "email_verified": email_verified
            }
        })





