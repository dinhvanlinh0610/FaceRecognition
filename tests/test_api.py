import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
import shutil
import uuid

client = TestClient(app)

# Tạo thư mục test tạm thời
TEST_IMAGES_DIR = "test_images"
TEST_USER_DIR = os.path.join(TEST_IMAGES_DIR, "test_user")

@pytest.fixture(scope="module")
def setup_test_environment():
    # Tạo thư mục test
    os.makedirs(TEST_USER_DIR, exist_ok=True)
    
    # Copy một số ảnh test vào thư mục
    # Lưu ý: Bạn cần có một số ảnh test trong thư mục test_images
    yield
    
    # Dọn dẹp sau khi test
    shutil.rmtree(TEST_IMAGES_DIR)

def test_create_user(setup_test_environment):
    # Test tạo user mới
    response = client.post(
        "/api/v1/users/",
        json={
            "name": "Test User",
            "image_path": TEST_USER_DIR
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "name" in data
    assert "face_encoding" in data
    return data["user_id"]

def test_list_users():
    # Test lấy danh sách users
    response = client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_search_user(setup_test_environment):
    # Test tìm kiếm user
    response = client.post(
        "/api/v1/users/search",
        json={
            "image_path": TEST_USER_DIR
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "name" in data
    assert "score" in data

def test_delete_user(setup_test_environment):
    # Test xóa user
    # Lấy user_id từ test_create_user
    user_id = test_create_user(setup_test_environment)
    
    response = client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User đã được xóa thành công"

def test_invalid_image_path():
    # Test với đường dẫn ảnh không hợp lệ
    response = client.post(
        "/api/v1/users/",
        json={
            "name": "Test User",
            "image_path": "invalid/path"
        }
    )
    assert response.status_code == 400

def test_invalid_user_id():
    # Test với user_id không tồn tại
    invalid_id = str(uuid.uuid4())
    response = client.delete(f"/api/v1/users/{invalid_id}")
    assert response.status_code == 404 