import firebase_admin
from firebase_admin import credentials, auth
import os
from pathlib import Path

# Get the correct path to Firebase service account file
BASE_DIR = Path(__file__).resolve().parent
FIREBASE_KEY_PATH = BASE_DIR.parent / "stocksense-e7226-firebase-adminsdk-fbsvc-b8cae3c098.json"

# Initialize Firebase app only once
if not firebase_admin._apps:
    cred = credentials.Certificate(str(FIREBASE_KEY_PATH))
    firebase_admin.initialize_app(cred)


