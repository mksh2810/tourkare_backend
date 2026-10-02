
import json
from typing import Annotated

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


# Makes Swagger display the Authorize button
bearer_scheme = HTTPBearer(auto_error=False)


def initialize_firebase():
    """Initialize Firebase Admin using the JSON environment variable."""

    if firebase_admin._apps:
        return

    if not settings.firebase_service_account_json:
        raise RuntimeError(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not configured"
        )

    try:
        service_account_info = json.loads(
            settings.firebase_service_account_json
        )

        credential = credentials.Certificate(
            service_account_info
        )

        firebase_admin.initialize_app(credential)

    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            "Invalid Firebase service account JSON"
        ) from exc


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> dict:
    """Verify the Firebase ID token from Flutter."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    token = credentials.credentials

    try:
        return auth.verify_id_token(
            token,
            check_revoked=True,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired Firebase ID token",
        ) from exc