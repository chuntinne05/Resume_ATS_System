// Xử lý sự kiện khi trang tải xong
document.addEventListener('DOMContentLoaded', function() {
    // Xử lý form tải lên resume
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const formData = new FormData(uploadForm);
            const statusDiv = document.getElementById('uploadStatus');
            statusDiv.innerText = 'Đang tải lên...';

            try {
                const response = await fetch('http://localhost:8000/api/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    statusDiv.innerText = 'Tải lên thành công! Batch ID: ' + result.batch_id;
                } else {
                    throw new Error(result.detail || 'Lỗi không xác định');
                }
            } catch (error) {
                statusDiv.innerText = 'Tải lên thất bại: ' + error.message;
                statusDiv.classList.add('error');
            }
        });
    }

    // Tải danh sách ứng viên
    if (document.getElementById('candidatesList')) {
        loadCandidates();
    }
});

// Hàm tải danh sách ứng viên
async function loadCandidates() {
    try {
        const response = await fetch('http://localhost:8000/api/candidates');
        const candidates = await response.json();
        const candidatesList = document.getElementById('candidatesList');
        candidatesList.innerHTML = '';

        candidates.forEach(candidate => {
            const card = document.createElement('div');
            card.className = 'candidate-card';
            card.innerHTML = `
                <h3>${candidate.full_name}</h3>
                <p>Email: ${candidate.email || 'Không có'}</p>
                <p>Phone: ${candidate.phone || 'Không có'}</p>
                <p>Phân loại: ${candidate.classification}</p>
                <p>Điểm số: ${candidate.overall_score}</p>
            `;
            candidatesList.appendChild(card);
        });
    } catch (error) {
        console.error('Lỗi khi tải danh sách ứng viên:', error);
        document.getElementById('candidatesList').innerText = 'Không thể tải danh sách ứng viên.';
    }
}