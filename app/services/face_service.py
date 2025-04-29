from app.utils.face_utils import get_average_face_encoding, detect_faces
from app.services.qdrant_service import QdrantService
from app.models.user import User, UserCreate, UserSearch
from fastapi import HTTPException
from typing import List, Dict, Any

class FaceService:
    def __init__(self):
        self.qdrant_service = QdrantService()

    async def create_user(self, user_data: UserCreate) -> User:
        try:
            face_encoding = get_average_face_encoding(user_data.image_path)
            user_id = self.qdrant_service.add_user(user_data.name, face_encoding)
            return User(
                user_id=user_id,
                name=user_data.name,
                face_encoding=face_encoding
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def delete_user(self, user_id: str) -> dict:
        success = self.qdrant_service.delete_user(user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Không tìm thấy user")
        return {"message": "User đã được xóa thành công"}

    async def search_user(self, user_search: UserSearch) -> dict:
        try:
            face_encoding = get_average_face_encoding(user_search.image_path)
            result = self.qdrant_service.search_user(face_encoding)
            
            if not result:
                return {"message": "Không tìm thấy user phù hợp"}
            
            return result
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def search_faces(self, image_path: str) -> List[Dict[str, Any]]:
        try:
            # Phát hiện khuôn mặt trong ảnh
            face_locations = detect_faces(image_path)
            if not face_locations:
                return []

            faces = []
            for face_location in face_locations:
                # Lấy encoding của khuôn mặt
                face_encoding = get_average_face_encoding(image_path, face_location)
                
                # Tìm kiếm user phù hợp
                result = self.qdrant_service.search_user(face_encoding)
                
                if result:
                    faces.append({
                        "bbox": face_location,
                        "name": result["name"],
                        "score": result["score"]
                    })
                else:
                    faces.append({
                        "bbox": face_location,
                        "name": "Unknown",
                        "score": 0.0
                    })
            
            return faces
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def list_users(self) -> list[User]:
        try:
            users_data = self.qdrant_service.list_users()
            return [
                User(
                    user_id=user["user_id"],
                    name=user["name"],
                    face_encoding=user["face_encoding"]
                )
                for user in users_data
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) 