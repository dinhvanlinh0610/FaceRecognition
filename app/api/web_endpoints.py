from fastapi import APIRouter, UploadFile, File, Form
from app.models.user import User, UserCreate, UserSearch
from app.services.face_service import FaceService
from typing import List, Dict, Any
import os
import uuid

router = APIRouter()
face_service = FaceService()

# Tạo thư mục tạm để lưu ảnh
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/web/users/", response_model=User)
async def web_create_user(
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

@router.post("/web/users/search")
async def web_search_user(image_path: UploadFile = File(...)):
    # Lưu file tạm
    file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{image_path.filename}")
    with open(file_path, "wb") as buffer:
        content = await image_path.read()
        buffer.write(content)
    
    try:
        # Tìm kiếm faces
        faces = await face_service.search_faces(file_path)
        
        if not faces:
            return {"message": "Không tìm thấy khuôn mặt"}
        
        # Format kết quả
        return {
            "faces": [{
                "top": face["bbox"][0],
                "right": face["bbox"][1],
                "bottom": face["bbox"][2],
                "left": face["bbox"][3],
                "name": face["name"],
                "score": face["score"]
            } for face in faces]
        }
    finally:
        # Xóa file tạm
        if os.path.exists(file_path):
            os.remove(file_path)

@router.get("/web/users/", response_model=List[User])
async def web_list_users():
    return await face_service.list_users()

@router.delete("/web/users/{user_id}")
async def web_delete_user(user_id: str):
    return await face_service.delete_user(user_id) 