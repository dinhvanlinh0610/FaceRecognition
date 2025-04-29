from pydantic import BaseModel
from typing import List

class UserBase(BaseModel):
    name: str

class UserCreate(UserBase):
    image_path: str

class UserSearch(BaseModel):
    image_path: str

class User(UserBase):
    user_id: str
    face_encoding: List[float]

    class Config:
        from_attributes = True 