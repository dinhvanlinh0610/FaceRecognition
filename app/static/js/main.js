// API endpoints
const API_BASE_URL = '/api/v1';
const ENDPOINTS = {
    USERS: `${API_BASE_URL}/web/users`,
    SEARCH: `${API_BASE_URL}/web/users/search`
};

// Utility functions
function showMessage(element, message, isError = false) {
    element.innerHTML = `
        <div class="${isError ? 'error-message' : 'success-message'}">
            ${message}
        </div>
    `;
}

function clearMessage(element) {
    element.innerHTML = '';
}

function showImagePreview(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewElement.innerHTML = `<img src="${e.target.result}" class="preview-image">`;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Add user form handling
document.getElementById('addUserForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultDiv = document.getElementById('addResult');
    clearMessage(resultDiv);

    const formData = new FormData();
    formData.append('name', document.getElementById('userName').value);
    formData.append('image_path', document.getElementById('userImage').files[0]);

    try {
        const response = await fetch(ENDPOINTS.USERS, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            showMessage(resultDiv, `
                <p>Thêm người dùng thành công!</p>
                <p>ID: ${data.user_id}</p>
                <p>Tên: ${data.name}</p>
            `);
            document.getElementById('addUserForm').reset();
            document.getElementById('addResult').querySelector('.preview-image')?.remove();
        } else {
            showMessage(resultDiv, data.detail || 'Có lỗi xảy ra', true);
        }
    } catch (error) {
        showMessage(resultDiv, 'Có lỗi xảy ra khi kết nối đến server', true);
    }
});

// Search form handling
document.getElementById('searchForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const resultDiv = document.getElementById('searchResult');
    clearMessage(resultDiv);

    const formData = new FormData();
    formData.append('image_path', document.getElementById('searchImage').files[0]);

    try {
        const response = await fetch(ENDPOINTS.SEARCH, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            if (data.message) {
                showMessage(resultDiv, data.message);
            } else {
                showMessage(resultDiv, `
                    <p>Tìm thấy người dùng:</p>
                    <p>ID: ${data.user_id}</p>
                    <p>Tên: ${data.name}</p>
                    <p>Độ chính xác: ${(data.score * 100).toFixed(2)}%</p>
                `);
            }
        } else {
            showMessage(resultDiv, data.detail || 'Có lỗi xảy ra', true);
        }
    } catch (error) {
        showMessage(resultDiv, 'Có lỗi xảy ra khi kết nối đến server', true);
    }
});

// List users handling
async function loadUserList() {
    const tbody = document.getElementById('userListBody');
    tbody.innerHTML = '<tr><td colspan="3" class="text-center">Đang tải...</td></tr>';

    try {
        const response = await fetch(ENDPOINTS.USERS);
        const users = await response.json();

        if (response.ok) {
            tbody.innerHTML = users.map(user => `
                <tr>
                    <td>${user.user_id}</td>
                    <td>${user.name}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteUser('${user.user_id}')">
                            Xóa
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="3" class="text-center text-danger">${users.detail || 'Có lỗi xảy ra'}</td></tr>`;
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Có lỗi xảy ra khi kết nối đến server</td></tr>';
    }
}

async function deleteUser(userId) {
    if (!confirm('Bạn có chắc chắn muốn xóa người dùng này?')) {
        return;
    }

    try {
        const response = await fetch(`${ENDPOINTS.USERS}/${userId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            loadUserList();
        } else {
            const data = await response.json();
            alert(data.detail || 'Có lỗi xảy ra khi xóa người dùng');
        }
    } catch (error) {
        alert('Có lỗi xảy ra khi kết nối đến server');
    }
}

// Image preview handling
document.getElementById('userImage').addEventListener('change', function() {
    showImagePreview(this, document.getElementById('addResult'));
});

document.getElementById('searchImage').addEventListener('change', function() {
    showImagePreview(this, document.getElementById('searchResult'));
});

// Refresh list button
document.getElementById('refreshList').addEventListener('click', loadUserList);

// Load initial user list
loadUserList();

// Camera variables
let stream = null;
let video = null;
let canvas = null;
let context = null;

// Real-time variables
let isRealTimeRunning = false;
let realTimeInterval = null;
let faceBoxes = [];
let isProcessing = false;
let lastFrameTime = 0;
const TARGET_FPS = 30;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Initialize camera elements
function initCameraElements() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    if (canvas) {
        context = canvas.getContext('2d');
    }
}

// Camera functions
async function startCamera() {
    try {
        // Kiểm tra các phần tử HTML
        if (!video || !canvas || !context) {
            initCameraElements();
            if (!video || !canvas || !context) {
                throw new Error('Không tìm thấy các phần tử camera cần thiết');
            }
        }

        // Yêu cầu quyền truy cập camera
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 }
            } 
        });
        
        // Hiển thị video
        video.srcObject = stream;
        video.style.display = 'block';
        
        // Kích hoạt các nút
        const startBtn = document.getElementById('startCamera');
        const stopBtn = document.getElementById('stopCamera');
        const captureBtn = document.getElementById('capture');
        const startRealTimeBtn = document.getElementById('startRealTime');
        const stopRealTimeBtn = document.getElementById('stopRealTime');
        
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        if (captureBtn) captureBtn.disabled = false;
        if (startRealTimeBtn) {
            startRealTimeBtn.disabled = false;
            startRealTimeBtn.style.display = 'inline-block';
            startRealTimeBtn.style.visibility = 'visible';
        }
        if (stopRealTimeBtn) {
            stopRealTimeBtn.disabled = true;
            stopRealTimeBtn.style.display = 'inline-block';
            stopRealTimeBtn.style.visibility = 'visible';
        }
        
        // Hiển thị thông báo thành công
        const resultDiv = document.getElementById('cameraResult');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4>✅ Camera đã được bật</h4>
                    <p>Bạn có thể chụp ảnh hoặc bật chế độ real-time</p>
                </div>
            `;
        }
        
        // Xử lý khi video bắt đầu phát
        video.onloadedmetadata = () => {
            video.play();
        };
        
    } catch (err) {
        console.error('Camera error:', err);
        const resultDiv = document.getElementById('cameraResult');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h4>❌ Lỗi khi bật camera</h4>
                    <p>${err.message}</p>
                    <p>Vui lòng kiểm tra:</p>
                    <ul>
                        <li>Camera đã được kết nối</li>
                        <li>Bạn đã cho phép trang web truy cập camera</li>
                        <li>Không có ứng dụng nào khác đang sử dụng camera</li>
                    </ul>
                </div>
            `;
        }
    }
}

function stopCamera() {
    if (stream) {
        // Dừng tất cả các track
        stream.getTracks().forEach(track => track.stop());
        if (video) {
            video.srcObject = null;
            video.style.display = 'none';
        }
        
        // Vô hiệu hóa các nút
        const startBtn = document.getElementById('startCamera');
        const stopBtn = document.getElementById('stopCamera');
        const captureBtn = document.getElementById('capture');
        const startRealTimeBtn = document.getElementById('startRealTime');
        const stopRealTimeBtn = document.getElementById('stopRealTime');
        
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (captureBtn) captureBtn.disabled = true;
        if (startRealTimeBtn) startRealTimeBtn.disabled = true;
        if (stopRealTimeBtn) stopRealTimeBtn.disabled = true;
        
        // Dừng real-time nếu đang chạy
        if (isRealTimeRunning) {
            stopRealTime();
        }
        
        // Hiển thị thông báo
        const resultDiv = document.getElementById('cameraResult');
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="alert alert-info">
                    <h4>ℹ️ Camera đã được tắt</h4>
                </div>
            `;
        }
    }
}

async function captureImage() {
    if (!stream) return;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);
    
    const imageData = canvas.toDataURL('image/jpeg');
    const formData = new FormData();
    formData.append('image_path', dataURLtoFile(imageData, 'capture.jpg'));
    
    try {
        const response = await fetch('/api/v1/users/search', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        if (response.ok) {
            const resultDiv = document.getElementById('cameraResult');
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <h4>✅ Tìm thấy người dùng:</h4>
                    <p>ID: ${result.user_id}</p>
                    <p>Tên: ${result.name}</p>
                    <p>Độ chính xác: ${(result.score * 100).toFixed(2)}%</p>
                </div>
            `;
        } else {
            const resultDiv = document.getElementById('cameraResult');
            resultDiv.innerHTML = `
                <div class="alert alert-danger">
                    <h4>❌ Không tìm thấy người dùng</h4>
                    <p>${result.detail || 'Không có kết quả phù hợp'}</p>
                </div>
            `;
        }
    } catch (err) {
        const resultDiv = document.getElementById('cameraResult');
        resultDiv.innerHTML = `
            <div class="alert alert-danger">
                <h4>❌ Lỗi khi tìm kiếm</h4>
                <p>${err.message}</p>
            </div>
        `;
    }
}

function dataURLtoFile(dataurl, filename) {
    const arr = dataurl.split(',');
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
        u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
}

// Hàm vẽ khung khuôn mặt và tên
function drawFaceBoxes(faces) {
    if (!context || !canvas || !video) return;
    
    // Cập nhật kích thước canvas để khớp với video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Clear canvas trước khi vẽ
    context.clearRect(0, 0, canvas.width, canvas.height);
    
    // Vẽ video frame
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Vẽ các facebox
    faces.forEach(face => {
        // Kiểm tra và chuyển đổi tọa độ nếu cần
        const x = face.x || face.left || 0;
        const y = face.y || face.top || 0;
        const width = face.width || (face.right - face.left) || 0;
        const height = face.height || (face.bottom - face.top) || 0;
        const name = face.name || 'Unknown';
        const score = face.score || face.confidence || 0;
        
        console.log('Drawing face:', { x, y, width, height, name, score }); // Debug log
        
        // Vẽ box
        context.strokeStyle = '#00FF00';
        context.lineWidth = 2;
        context.strokeRect(x, y, width, height);
        
        // Vẽ label background
        context.fillStyle = '#00FF00';
        context.fillRect(x, y - 20, width, 20);
        
        // Vẽ text
        context.fillStyle = '#000000';
        context.font = '12px Arial';
        context.fillText(`${name} (${(score * 100).toFixed(1)}%)`, x + 5, y - 5);
    });
}

async function processRealTime() {
    if (isProcessing) return;
    
    const now = performance.now();
    if (now - lastFrameTime < 1000 / TARGET_FPS) {
        return;
    }
    lastFrameTime = now;
    
    isProcessing = true;
    let retries = 0;
    
    while (retries < MAX_RETRIES) {
        try {
            if (!video || !canvas || !context) {
                throw new Error('Camera elements not initialized');
            }
            
            // Đảm bảo canvas có kích thước phù hợp
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // Capture frame
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            const imageData = canvas.toDataURL('image/jpeg');
            
            // Send to API
            const formData = new FormData();
            const blob = await fetch(imageData).then(r => r.blob());
            formData.append('image_path', blob, 'frame.jpg');
            
            const response = await fetch(ENDPOINTS.SEARCH, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('API response:', data); // Debug log
            
            if (data.faces && Array.isArray(data.faces)) {
                console.log('Drawing faces:', data.faces); // Debug log
                drawFaceBoxes(data.faces);
            } else if (data.face) {
                // Nếu API trả về một face duy nhất
                console.log('Drawing single face:', data.face); // Debug log
                drawFaceBoxes([data.face]);
            }
            
            break;
        } catch (error) {
            console.error('Real-time processing error:', error);
            retries++;
            
            if (retries === MAX_RETRIES) {
                console.error('Max retries reached, stopping real-time processing');
                stopRealTime();
                return;
            }
            
            await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        }
    }
    
    isProcessing = false;
}

async function startRealTime() {
    if (isRealTimeRunning) return;
    
    try {
        if (!video || !canvas || !context) {
            initCameraElements();
            if (!video || !canvas || !context) {
                throw new Error('Không tìm thấy các phần tử camera cần thiết');
            }
        }
        
        // Thêm class realtime để hiển thị canvas
        const container = document.querySelector('.camera-container');
        if (container) {
            container.classList.add('realtime');
        }
        
        isRealTimeRunning = true;
        realTimeInterval = setInterval(processRealTime, 1000 / TARGET_FPS);
        
        // Update UI
        const startBtn = document.getElementById('startRealTime');
        const stopBtn = document.getElementById('stopRealTime');
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        
    } catch (error) {
        console.error('Failed to start real-time:', error);
        isRealTimeRunning = false;
    }
}

function stopRealTime() {
    if (!isRealTimeRunning) return;
    
    isRealTimeRunning = false;
    if (realTimeInterval) {
        clearInterval(realTimeInterval);
        realTimeInterval = null;
    }
    
    // Xóa class realtime để ẩn canvas
    const container = document.querySelector('.camera-container');
    if (container) {
        container.classList.remove('realtime');
    }
    
    // Clear canvas
    if (context && canvas) {
        context.clearRect(0, 0, canvas.width, canvas.height);
    }
    
    // Update UI
    const startBtn = document.getElementById('startRealTime');
    const stopBtn = document.getElementById('stopRealTime');
    if (startBtn) startBtn.disabled = false;
    if (stopBtn) stopBtn.disabled = true;
    
    // Hiển thị thông báo
    const resultDiv = document.getElementById('cameraResult');
    if (resultDiv) {
        resultDiv.innerHTML = `
            <div class="alert alert-info">
                <h4>ℹ️ Đã tắt chế độ real-time</h4>
                <p>Bạn có thể bật lại chế độ real-time hoặc chụp ảnh</p>
            </div>
        `;
    }
}

// Gắn sự kiện cho các nút camera
document.addEventListener('DOMContentLoaded', () => {
    // Khởi tạo các phần tử camera
    initCameraElements();
    
    // Gắn sự kiện cho các nút
    const startBtn = document.getElementById('startCamera');
    const stopBtn = document.getElementById('stopCamera');
    const captureBtn = document.getElementById('capture');
    const startRealTimeBtn = document.getElementById('startRealTime');
    const stopRealTimeBtn = document.getElementById('stopRealTime');
    
    if (startBtn) startBtn.addEventListener('click', startCamera);
    if (stopBtn) stopBtn.addEventListener('click', stopCamera);
    if (captureBtn) captureBtn.addEventListener('click', captureImage);
    if (startRealTimeBtn) startRealTimeBtn.addEventListener('click', startRealTime);
    if (stopRealTimeBtn) stopRealTimeBtn.addEventListener('click', stopRealTime);
}); 