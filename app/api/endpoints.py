from fastapi import APIRouter, UploadFile, File, Form
from app.models.user import User, UserCreate, UserSearch
from app.services.face_service import FaceService
from typing import List
import os
import uuid

router = APIRouter()
face_service = FaceService()

# Tạo thư mục tạm để lưu ảnh
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/users/", response_model=User)
async def create_user(
    name: str = Form(...),
    image_path: UploadFile = File(...)
):
    # Lưu file tạm
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_path.filename}")
    with open(file_path, "wb") as buffer:
        content = await image_path.read()
        buffer.write(content)
    
    try:
        # Tạo user
        user_data = UserCreate(name=name, image_path=file_path)
        return await face_service.create_user(user_data)
    finally:
        # Xóa file tạm
        if os.path.exists(file_path):
            os.remove(file_path)

@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    return await face_service.delete_user(user_id)

@router.post("/users/search")
async def search_user(image_path: UploadFile = File(...)):
    # Lưu file tạm
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_path.filename}")
    with open(file_path, "wb") as buffer:
        content = await image_path.read()
        buffer.write(content)
    
    try:
        # Tìm kiếm user
        search_data = UserSearch(image_path=file_path)
        return await face_service.search_user(search_data)
    finally:
        # Xóa file tạm
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/users/", response_model=List[User])
async def list_users():
    return await face_service.list_users() 