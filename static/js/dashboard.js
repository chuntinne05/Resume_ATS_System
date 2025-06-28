// static/js/dashboard.js

// Hiển thị loading
function showLoading() {
    document.querySelector('#loading').style.display = 'block';
}

// Ẩn loading
function hideLoading() {
    document.querySelector('#loading').style.display = 'none';
}

// Lấy danh sách ứng viên từ API
async function fetchCandidates() {
    showLoading();
    try {
        const response = await fetch('/api/candidates');
        if (!response.ok) {
            throw new Error('Không thể tải danh sách ứng viên');
        }
        const candidates = await response.json();
        updateCandidateTable(candidates);
    } catch (error) {
        console.error('Lỗi khi lấy danh sách ứng viên:', error);
        alert('Không thể tải danh sách ứng viên. Vui lòng thử lại.');
    } finally {
        hideLoading();
    }
}

// Lấy thống kê dashboard từ API
async function fetchDashboardStats() {
    try {
        const response = await fetch('/api/dashboard/stats');
        if (!response.ok) {
            throw new Error('Không thể tải thống kê');
        }
        const stats = await response.json();
        updateStatsCards(stats);
    } catch (error) {
        console.error('Lỗi khi lấy thống kê:', error);
    }
}

// Cập nhật bảng ứng viên
function updateCandidateTable(candidates) {
    const tableBody = document.querySelector('#candidate-table-body');
    tableBody.innerHTML = ''; // Xóa các hàng hiện có
    candidates.forEach(candidate => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${candidate.full_name}</td>
            <td>${candidate.email}</td>
            <td>${candidate.overall_score}</td>
            <td>${candidate.experience_level}</td>
            <td>${candidate.status}</td>
            <td>${new Date(candidate.created_at).toLocaleDateString()}</td>
            <td>
                <button onclick="viewCandidate(${candidate.id})">Xem</button>
                <button onclick="deleteCandidate(${candidate.id})">Xóa</button>
            </td>
        `;
        tableBody.appendChild(row);
    });
    // Cập nhật số lượng hiển thị (nếu cần)
    document.querySelector('.showing-text').textContent = `Hiển thị ${candidates.length} trong số ${candidates.length} ứng viên`;
}

// Cập nhật thẻ thống kê
function updateStatsCards(stats) {
    document.querySelector('#total-candidates').textContent = stats.total_candidates;
    document.querySelector('#approved-candidates').textContent = stats.approved_candidates;
    document.querySelector('#under-review-candidates').textContent = stats.under_review_candidates;
    document.querySelector('#average-score').textContent = stats.average_score.toFixed(2);
}

// Tìm kiếm và lọc ứng viên
async function searchCandidates() {
    const searchTerm = document.querySelector('#search-input').value;
    const status = document.querySelector('#status-filter').value;
    const experienceLevel = document.querySelector('#experience-filter').value;
    const minScore = document.querySelector('#min-score-input').value;

    let query = `/api/candidates?`;
    if (searchTerm) query += `search=${encodeURIComponent(searchTerm)}&`;
    if (status && status !== 'All Status') query += `status=${status}&`;
    if (experienceLevel && experienceLevel !== 'All Levels') query += `experience_level=${experienceLevel}&`;
    if (minScore) query += `min_score=${minScore}&`;

    showLoading();
    try {
        const response = await fetch(query);
        if (!response.ok) {
            throw new Error('Tìm kiếm thất bại');
        }
        const candidates = await response.json();
        updateCandidateTable(candidates);
    } catch (error) {
        console.error('Lỗi khi tìm kiếm:', error);
        alert('Tìm kiếm thất bại. Vui lòng thử lại.');
    } finally {
        hideLoading();
    }
}

async function updateStatus(candidateId, newStatus) {
    const upperStatus = newStatus.toUpperCase();
    try {
        const response = await fetch(`/api/candidates/${candidateId}/status?status=${upperStatus}`, {
            method: 'PUT'
        });
        if (!response.ok) {
            throw new Error('Cập nhật trạng thái thất bại');
        }
        alert('Cập nhật trạng thái thành công');
    } catch (error) {
        console.error('Lỗi khi cập nhật trạng thái:', error);
        alert('Cập nhật trạng thái thất bại.');
    }
}

async function viewCandidate(candidateId) {
    try {
        const response = await fetch(`/api/candidates/${candidateId}`);
        if (!response.ok) {
            throw new Error('Không thể tải chi tiết ứng viên');
        }
        const candidate = await response.json();
        
        document.querySelector('#candidate-name').textContent = candidate.full_name;
        document.querySelector('#candidate-email').textContent = candidate.email || 'N/A';
        document.querySelector('#candidate-phone').textContent = candidate.phone || 'N/A';
        document.querySelector('#candidate-address').textContent = candidate.address || 'N/A';
        document.querySelector('#candidate-score').textContent = candidate.overall_score;
        document.querySelector('#candidate-classification').textContent = candidate.classification || 'N/A';
        
        // Cập nhật danh sách kỹ năng
        const skillsList = document.querySelector('#skills-list');
        skillsList.innerHTML = '';
        if (candidate.skills && candidate.skills.length > 0) {
            candidate.skills.forEach(skill => {
                const li = document.createElement('li');
                li.textContent = `${skill.skill_name} (${skill.proficiency_level})`;
                skillsList.appendChild(li);
            });
        } else {
            skillsList.innerHTML = '<li>No skills found</li>';
        }
        
        // Cập nhật danh sách kinh nghiệm
        const experienceList = document.querySelector('#experience-list');
        experienceList.innerHTML = '';
        if (candidate.experience && candidate.experience.length > 0) {
            candidate.experience.forEach(exp => {
                const li = document.createElement('li');
                li.textContent = `${exp.job_title} tại ${exp.company} (${exp.start_date} - ${exp.end_date || 'Hiện tại'})`;
                experienceList.appendChild(li);
            });
        } else {
            experienceList.innerHTML = '<li>No experience found</li>';
        }
        
        // Cập nhật danh sách học vấn
        const educationList = document.querySelector('#education-list');
        educationList.innerHTML = '';
        if (candidate.education && candidate.education.length > 0) {
            candidate.education.forEach(edu => {
                const li = document.createElement('li');
                li.textContent = `${edu.degree} chuyên ngành ${edu.major} tại ${edu.institution} (${edu.graduation_year})`;
                educationList.appendChild(li);
            });
        } else {
            educationList.innerHTML = '<li>No education found</li>';
        }
        
        // Hiển thị modal
        document.querySelector('#candidate-modal').style.display = 'block';
    } catch (error) {
        console.error('Lỗi khi xem chi tiết:', error);
        alert('Không thể tải chi tiết ứng viên.');
    }
}

// Xóa ứng viên
async function deleteCandidate(candidateId) {
    if (confirm('Bạn có chắc muốn xóa ứng viên này không?')) {
        try {
            const response = await fetch(`/api/candidates/${candidateId}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                throw new Error('Xóa thất bại');
            }
            fetchCandidates(); // Làm mới danh sách
        } catch (error) {
            console.error('Lỗi khi xóa:', error);
            alert('Xóa ứng viên thất bại.');
        }
    }
}

async function checkBatchStatus(batchId) {
    try {
        const response = await fetch(`/api/batches/${batchId}/status`);
        if (!response.ok) {
            throw new Error('Không thể kiểm tra trạng thái batch');
        }
        const batch = await response.json();
        if (batch.status === 'COMPLETED' || batch.status === 'FAILED') {
            fetchCandidates();
            fetchDashboardStats();
        } else {
            setTimeout(() => checkBatchStatus(batchId), 2000);
        }
    } catch (error) {
        console.error('Lỗi khi kiểm tra trạng thái batch:', error);
    }
}

// Xử lý tải lên resume
document.querySelector('#upload-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            throw new Error('Tải lên thất bại');
        }
        const result = await response.json();
        alert('Tải lên thành công. Quá trình xử lý có thể mất thời gian.');
        document.querySelector('#upload-modal').style.display = 'none';
        event.target.reset();
        
        // Bắt đầu kiểm tra trạng thái batch
        checkBatchStatus(result.batch_id);
    } catch (error) {
        console.error('Lỗi khi tải lên:', error);
        alert('Tải lên thất bại. Vui lòng thử lại.');
    }
});

// Khởi tạo dashboard khi trang tải
document.addEventListener('DOMContentLoaded', () => {
    fetchCandidates();
    fetchDashboardStats();
});

// Nút làm mới
document.querySelector('#refresh-button').addEventListener('click', () => {
    fetchCandidates();
    fetchDashboardStats();
});

// Đóng modal khi nhấn nút Close
document.querySelector('#candidate-modal .modal-close').addEventListener('click', () => {
    document.querySelector('#candidate-modal').style.display = 'none';
});

// Đóng modal tải lên khi nhấn Cancel
document.querySelector('#upload-cancel').addEventListener('click', () => {
    document.querySelector('#upload-modal').style.display = 'none';
});

