import os
import numpy as np
import face_recognition
from fastapi import HTTPException
from typing import List, Tuple

def get_average_face_encoding(image_path: str, face_location: Tuple[int, int, int, int] = None) -> list[float]:
    """Lấy encoding trung bình từ tất cả ảnh trong thư mục hoặc từ một khuôn mặt cụ thể"""
    encodings = []
    
    if os.path.isdir(image_path):
        for filename in os.listdir(image_path):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                image = face_recognition.load_image_file(os.path.join(image_path, filename))
                face_encodings = face_recognition.face_encodings(image)
                if face_encodings:
                    encodings.append(face_encodings[0])
    else:
        image = face_recognition.load_image_file(image_path)
        if face_location:
            # Lấy encoding từ khuôn mặt cụ thể
            face_encodings = face_recognition.face_encodings(image, [face_location])
        else:
            # Lấy encoding từ khuôn mặt đầu tiên
            face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            encodings.append(face_encodings[0])
    
    if not encodings:
        raise HTTPException(status_code=400, detail="Không tìm thấy khuôn mặt trong ảnh")
    
    return list(np.mean(encodings, axis=0))

def detect_faces(image_path: str) -> List[Tuple[int, int, int, int]]:
    """Phát hiện tất cả khuôn mặt trong ảnh và trả về vị trí của chúng"""
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        return face_locations
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi phát hiện khuôn mặt: {str(e)}") 