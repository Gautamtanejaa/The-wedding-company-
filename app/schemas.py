from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class OrganizationBase(BaseModel):
    organization_name: str = Field(..., min_length=1)


class OrganizationCreate(OrganizationBase):
    email: EmailStr
    password: str = Field(..., min_length=6)


class OrganizationResponse(BaseModel):
    id: str
    organization_name: str
    collection_name: str
    created_at: datetime
    updated_at: datetime


class OrganizationGetQuery(BaseModel):
    organization_name: str


class OrganizationUpdate(BaseModel):
    # New desired name for the organization (optional)
    organization_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)


class OrganizationDelete(BaseModel):
    organization_name: str


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminInToken(BaseModel):
    admin_id: str
    organization_id: str
    organization_name: str


class Message(BaseModel):
    message: str
