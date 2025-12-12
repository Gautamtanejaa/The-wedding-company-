from datetime import datetime
import re
from typing import Optional

from bson import ObjectId

from .auth import hash_password
from .db import get_database


def slugify(name: str) -> str:
    """Very simple slugify: lowercases and replaces non-alphanumerics with underscores."""
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


async def get_org_by_name(organization_name: str) -> Optional[dict]:
    db = await get_database()
    orgs = db["organizations"]
    slug = slugify(organization_name)
    return await orgs.find_one({"slug": slug})


async def create_organization_with_admin(organization_name: str, email: str, password: str) -> dict:
    db = await get_database()
    orgs = db["organizations"]
    admins = db["admins"]

    slug = slugify(organization_name)
    existing = await orgs.find_one({"slug": slug})
    if existing:
        raise ValueError("Organization with this name already exists")

    now = datetime.utcnow()
    collection_name = f"org_{slug}"

    # Create admin user
    admin_doc = {
        "email": email,
        "password_hash": hash_password(password),
        "created_at": now,
    }
    admin_result = await admins.insert_one(admin_doc)

    # Create organization metadata
    org_doc = {
        "name": organization_name,
        "slug": slug,
        "collection_name": collection_name,
        "created_at": now,
        "updated_at": now,
        "admin_id": admin_result.inserted_id,
    }
    org_result = await orgs.insert_one(org_doc)

    # Link admin to org
    await admins.update_one(
        {"_id": admin_result.inserted_id},
        {"$set": {"organization_id": org_result.inserted_id}},
    }

    # Create the dynamic collection (empty but explicitly created)
    await db.create_collection(collection_name)

    org_doc["_id"] = org_result.inserted_id
    return org_doc


async def update_organization_and_admin(
    current_org: dict,
    new_org_name: Optional[str] = None,
    new_email: Optional[str] = None,
    new_password: Optional[str] = None,
) -> dict:
    db = await get_database()
    orgs = db["organizations"]
    admins = db["admins"]

    update_fields: dict = {}
    old_collection_name = current_org["collection_name"]

    if new_org_name and new_org_name != current_org["name"]:
        new_slug = slugify(new_org_name)
        existing = await orgs.find_one({"slug": new_slug})
        if existing and existing["_id"] != current_org["_id"]:
            raise ValueError("Organization name already in use")

        new_collection_name = f"org_{new_slug}"

        # Create new collection and sync data
        old_collection = db[old_collection_name]
        new_collection = db[new_collection_name]

        async for doc in old_collection.find({}):
            _id = doc.pop("_id", None)
            await new_collection.insert_one(doc)

        # Drop old collection
        await db.drop_collection(old_collection_name)

        update_fields.update({
            "name": new_org_name,
            "slug": new_slug,
            "collection_name": new_collection_name,
        })

    if new_email or new_password:
        admin_id = current_org["admin_id"]
        admin_update: dict = {}
        if new_email:
            admin_update["email"] = new_email
        if new_password:
            admin_update["password_hash"] = hash_password(new_password)
        if admin_update:
            await admins.update_one({"_id": admin_id}, {"$set": admin_update})

    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()
        await orgs.update_one({"_id": current_org["_id"]}, {"$set": update_fields})
        current_org.update(update_fields)

    return current_org


async def delete_organization_and_admin(org: dict) -> None:
    db = await get_database()
    orgs = db["organizations"]
    admins = db["admins"]

    await orgs.delete_one({"_id": org["_id"]})
    await admins.delete_one({"_id": org["admin_id"]})

    # Drop org-specific collection
    await db.drop_collection(org["collection_name"])
