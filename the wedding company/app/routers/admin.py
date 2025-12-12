from bson import ObjectId
from fastapi import APIRouter, HTTPException, status

from ..auth import create_access_token, verify_password
from ..db import get_database
from ..schemas import AdminLoginRequest, TokenResponse


router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/login", response_model=TokenResponse)
async def admin_login(payload: AdminLoginRequest):
    """Admin login endpoint.

    Validates credentials and returns a JWT containing admin and organization identifiers.
    """

    db = await get_database()
    admins_coll = db["admins"]
    orgs_coll = db["organizations"]

    admin = await admins_coll.find_one({"email": payload.email})
    if not admin or not verify_password(payload.password, admin["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Admin is not associated with any organization")

    org = await orgs_coll.find_one({"_id": ObjectId(org_id)})
    if not org:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not found for admin")

    token_data = {
        "sub": str(admin["_id"]),
        "org_id": str(org["_id"]),
        "org_name": org["name"],
    }
    access_token = create_access_token(token_data)

    return TokenResponse(access_token=access_token)
