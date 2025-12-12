from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import get_current_admin
from ..db import get_database
from ..models import (
    create_organization_with_admin,
    delete_organization_and_admin,
    get_org_by_name,
    update_organization_and_admin,
)
from ..schemas import (
    Message,
    OrganizationCreate,
    OrganizationDelete,
    OrganizationResponse,
    OrganizationUpdate,
)


router = APIRouter(prefix="/org", tags=["organizations"])


@router.post("/create", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate):
    """Create a new organization and its admin, along with a dynamic collection."""
    try:
        org_doc = await create_organization_with_admin(
            organization_name=payload.organization_name,
            email=payload.email,
            password=payload.password,
        )
    except ValueError as exc:  # organization already exists
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return OrganizationResponse(
        id=str(org_doc["_id"]),
        organization_name=org_doc["name"],
        collection_name=org_doc["collection_name"],
        created_at=org_doc["created_at"],
        updated_at=org_doc["updated_at"],
    )


@router.get("/get", response_model=OrganizationResponse)
async def get_organization(organization_name: str):
    """Get organization metadata by name."""
    org_doc = await get_org_by_name(organization_name)
    if not org_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return OrganizationResponse(
        id=str(org_doc["_id"]),
        organization_name=org_doc["name"],
        collection_name=org_doc["collection_name"],
        created_at=org_doc["created_at"],
        updated_at=org_doc["updated_at"],
    )


@router.put("/update", response_model=OrganizationResponse)
async def update_organization(
    payload: OrganizationUpdate,
    current_admin=Depends(get_current_admin),
):
    """Update organization name (with collection migration) and/or admin credentials.

    The assignment spec lists organization_name, email, password as inputs. Here we treat
    organization_name as the *new* organization name for the authenticated admin's organization.
    """

    db = await get_database()
    orgs_coll = db["organizations"]

    org_doc = await orgs_coll.find_one({"_id": ObjectId(current_admin.organization_id)})
    if not org_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    try:
        updated_org = await update_organization_and_admin(
            current_org=org_doc,
            new_org_name=payload.organization_name,
            new_email=payload.email,
            new_password=payload.password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return OrganizationResponse(
        id=str(updated_org["_id"]),
        organization_name=updated_org["name"],
        collection_name=updated_org["collection_name"],
        created_at=updated_org["created_at"],
        updated_at=updated_org["updated_at"],
    )


@router.delete("/delete", response_model=Message)
async def delete_organization(
    payload: OrganizationDelete,
    current_admin=Depends(get_current_admin),
):
    """Delete the authenticated admin's organization and its dynamic collection.

    Only allows deletion of the organization that matches the authenticated admin and
    the provided organization_name.
    """

    db = await get_database()
    orgs_coll = db["organizations"]

    org_doc = await orgs_coll.find_one({"_id": ObjectId(current_admin.organization_id)})
    if not org_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if payload.organization_name != org_doc["name"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own organization with matching name.",
        )

    await delete_organization_and_admin(org_doc)
    return Message(message="Organization deleted successfully")
