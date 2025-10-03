import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv

load_dotenv()

# Required Firebase environment variables
required_env_vars = [
    'FIREBASE_PROJECT_ID',
    'FIREBASE_PRIVATE_KEY_ID', 
    'FIREBASE_PRIVATE_KEY',
    'FIREBASE_CLIENT_EMAIL',
    'FIREBASE_CLIENT_ID',
    'FIREBASE_CLIENT_X509_CERT_URL'
]

# Check if all required environment variables are present
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

# Allow tests to run without Firebase if we're in a test environment
is_testing = (
    os.getenv('DJANGO_SETTINGS_MODULE', '').endswith('test') or
    'test' in os.getenv('DATABASE_URL', '') or
    os.getenv('TESTING', '').lower() == 'true'
)

if missing_vars and not is_testing:
    raise EnvironmentError(f"Missing required Firebase environment variables: {', '.join(missing_vars)}")

# Skip Firebase initialization if we're in testing mode and variables are missing
if missing_vars and is_testing:
    print("Skipping Firebase initialization in test environment - Firebase variables not set")
    firebase_config = None
    FIREBASE_STORAGE_BUCKET = None
else:
    # Get Firebase configuration from environment variables ONLY
    firebase_config = {
        "type": os.getenv('FIREBASE_TYPE', 'service_account'),
        "project_id": os.getenv('FIREBASE_PROJECT_ID'),
        "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        "private_key": os.getenv('FIREBASE_PRIVATE_KEY'),
        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
        "client_id": os.getenv('FIREBASE_CLIENT_ID'),
        "auth_uri": os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
        "token_uri": os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
        "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
        "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL'),
        "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
    }

    FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET', 'stocksense-e7226.appspot.com')

# Initialize Firebase app only once using ONLY environment variables
if not firebase_admin._apps and firebase_config is not None:
    try:
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            'projectId': firebase_config['project_id'],
            'storageBucket': FIREBASE_STORAGE_BUCKET
        })
        print("✅ Firebase initialized successfully using environment variables")
    except Exception as e:
        if not is_testing:
            raise Exception(f"Failed to initialize Firebase using environment variables: {str(e)}")
        else:
            print(f"⚠️  Firebase initialization failed in test environment: {str(e)}")
elif firebase_config is None:
    print("⚠️  Firebase not initialized - running in test mode")


