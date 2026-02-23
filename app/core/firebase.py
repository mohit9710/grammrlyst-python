import firebase_admin
from firebase_admin import credentials, auth, storage
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

cred_path = BASE_DIR / "resources" / "gymcraft-b8f60.json"

cred = credentials.Certificate(str(cred_path))

# init only once
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'gymcraft-b8f60.firebasestorage.app'
    })

# IMPORTANT → export auth
firebase_auth = auth
firebase_storage = storage.bucket()