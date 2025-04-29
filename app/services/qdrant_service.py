from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config import config
import uuid
import os
import time
from grpc import StatusCode
import sys

class QdrantService:
    def __init__(self):
        try:
            print("\n" + "="*80)
            print("🔄 Đang kết nối đến Qdrant server...")
            print(f"   - Host: {config.QDRANT_HOST}")
            print(f"   - Port: {config.QDRANT_PORT}")
            print("="*80 + "\n")
            
            self.client = QdrantClient(
                host=config.QDRANT_HOST,
                port=config.QDRANT_PORT,
                prefer_grpc=False,
                timeout=5.0
            )
            self.collection_name = config.QDRANT_COLLECTION
            self._ensure_collection()
        except Exception as e:
            print("\n" + "="*80)
            print("❌ LỖI: Không thể kết nối đến Qdrant server")
            print("="*80)
            print("Vui lòng thực hiện các bước sau:")
            print("1. Kiểm tra xem Qdrant container đã chạy chưa bằng lệnh:")
            print("   docker ps")
            print("2. Nếu chưa, khởi động Qdrant server bằng lệnh:")
            print("   docker run -p 6333:6333 qdrant/qdrant")
            print("3. Đợi khoảng 10 giây để server khởi động hoàn tất")
            print("4. Chạy lại chương trình")
            print("="*80 + "\n")
            sys.exit(1)

    def _ensure_collection(self):
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                print("\n" + "="*80)
                print("🔄 Đang kiểm tra collection...")
                print("="*80 + "\n")
                
                # Kiểm tra kết nối đến server
                self.client.get_collections()
                
                # Tạo collection nếu chưa tồn tại
                collections = self.client.get_collections().collections
                collection_names = [collection.name for collection in collections]
                
                if self.collection_name not in collection_names:
                    print(f"🔄 Đang tạo collection '{self.collection_name}'...")
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=models.VectorParams(size=128, distance=models.Distance.COSINE),
                    )
                    print(f"✅ Collection '{self.collection_name}' đã được tạo thành công")
                else:
                    print(f"ℹ️ Collection '{self.collection_name}' đã tồn tại")
                return
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⚠️ Lỗi kết nối đến Qdrant server (lần thử {attempt + 1}/{max_retries}):")
                    print(f"   - Lỗi: {str(e)}")
                    print(f"   - Đang thử lại sau {retry_delay} giây...")
                    time.sleep(retry_delay)
                else:
                    print("\n" + "="*80)
                    print("❌ LỖI: Không thể kết nối đến Qdrant server sau nhiều lần thử")
                    print("="*80)
                    print("Vui lòng thực hiện các bước sau:")
                    print("1. Kiểm tra xem Qdrant container đã chạy chưa bằng lệnh:")
                    print("   docker ps")
                    print("2. Nếu chưa, khởi động Qdrant server bằng lệnh:")
                    print("   docker run -p 6333:6333 qdrant/qdrant")
                    print("3. Đợi khoảng 10 giây để server khởi động hoàn tất")
                    print("4. Chạy lại chương trình")
                    print("="*80 + "\n")
                    sys.exit(1)

    def add_user(self, name: str, face_encoding: list[float]) -> str:
        user_id = str(uuid.uuid4())
        try:
            print("\n" + "="*80)
            print(f"🔄 Đang thêm user {name}...")
            print(f"   - ID: {user_id}")
            print(f"   - Vector size: {len(face_encoding)}")
            print("="*80 + "\n")
            
            # Kiểm tra kết nối trước khi thêm
            try:
                self.client.get_collections()
            except Exception as e:
                print(f"❌ Lỗi kết nối đến Qdrant: {str(e)}")
                raise
            
            # Thêm user
            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[
                        models.PointStruct(
                            id=user_id,
                            vector=face_encoding,
                            payload={"name": name}
                        )
                    ]
                )
            except Exception as e:
                print(f"❌ Lỗi khi upsert user: {str(e)}")
                raise
            
            # Kiểm tra xem user đã được thêm chưa
            try:
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=face_encoding,
                    limit=1
                )
            except Exception as e:
                print(f"❌ Lỗi khi tìm kiếm user: {str(e)}")
                raise
            
            if search_result and search_result[0].id == user_id:
                print(f"✅ Đã thêm user {name} thành công với ID: {user_id}")
                print(f"   - Collection: {self.collection_name}")
                print(f"   - Vector size: {len(face_encoding)}")
                print(f"   - Score: {search_result[0].score}")
            else:
                print(f"⚠️ Không thể xác nhận user {name} đã được thêm")
            
            return user_id
        except Exception as e:
            print(f"❌ Lỗi khi thêm user: {str(e)}")
            raise e

    def delete_user(self, user_id: str) -> bool:
        try:
            print("\n" + "="*80)
            print(f"🔄 Đang xóa user với ID: {user_id}...")
            print("="*80 + "\n")
            
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[user_id]
                )
            )
            
            # Kiểm tra xem user đã bị xóa chưa
            try:
                self.client.retrieve(
                    collection_name=self.collection_name,
                    ids=[user_id]
                )
                print(f"⚠️ Không thể xác nhận user đã bị xóa")
                return False
            except Exception:
                print(f"✅ Đã xóa user với ID: {user_id} thành công")
                return True
        except Exception as e:
            print(f"❌ Lỗi khi xóa user: {str(e)}")
            return False

    def search_user(self, face_encoding: list[float]) -> dict:
        try:
            print("\n" + "="*80)
            print("🔄 Đang tìm kiếm user...")
            print("="*80 + "\n")
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=face_encoding,
                limit=1
            )
            
            if not search_result:
                print("ℹ️ Không tìm thấy user phù hợp")
                return None
            
            best_match = search_result[0]
            print(f"✅ Tìm thấy user phù hợp:")
            print(f"   - ID: {best_match.id}")
            print(f"   - Tên: {best_match.payload['name']}")
            print(f"   - Độ chính xác: {best_match.score}")
            return {
                "user_id": best_match.id,
                "name": best_match.payload["name"],
                "score": best_match.score
            }
        except Exception as e:
            print(f"❌ Lỗi khi tìm kiếm user: {str(e)}")
            raise e

    def list_users(self) -> list[dict]:
        try:
            print("\n" + "="*80)
            print("🔄 Đang lấy danh sách users...")
            print("="*80 + "\n")
            
            # Lấy tất cả points từ collection
            points = self.client.scroll(
                collection_name=self.collection_name,
                limit=100,
                with_payload=True,
                with_vectors=True
            )[0]
            
            if not points:
                print("ℹ️ Không có user nào trong collection")
                return []
            
            users = []
            for point in points:
                try:
                    user = {
                        "user_id": str(point.id),
                        "name": point.payload.get("name", "Unknown"),
                        "face_encoding": point.vector
                    }
                    users.append(user)
                except Exception as e:
                    print(f"⚠️ Lỗi khi xử lý point {point.id}: {str(e)}")
                    continue
            
            print(f"✅ Đã lấy danh sách {len(users)} users")
            for user in users:
                print(f"   - {user['name']} (ID: {user['user_id']})")
            return users
        except Exception as e:
            print(f"❌ Lỗi khi lấy danh sách users: {str(e)}")
            raise e 