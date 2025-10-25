"""
Pydantic Schemas for API data validation.
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

class AgentCreate(BaseModel):
    name: str
    description: str
    capabilities: List[str]
    endpoint: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str
