
function showLoading() {
    document.querySelector('#loading').style.display = 'block';
}

function hideLoading() {
    document.querySelector('#loading').style.display = 'none';
}

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
    document.querySelector('.showing-text').textContent = `Hiển thị ${candidates.length} trong số ${candidates.length} ứng viên`;
}

function updateStatsCards(stats) {
    document.querySelector('#total-candidates').textContent = stats.total_candidates;
    document.querySelector('#approved-candidates').textContent = stats.approved_candidates;
    document.querySelector('#under-review-candidates').textContent = stats.under_review_candidates;
    document.querySelector('#average-score').textContent = stats.average_score.toFixed(2);
}

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
        
        document.querySelector('#candidate-modal').style.display = 'block';
    } catch (error) {
        console.error('Lỗi khi xem chi tiết:', error);
        alert('Không thể tải chi tiết ứng viên.');
    }
}

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

async function fetchJobRequirements() {
    try {
        const response = await fetch('/api/dashboard/job-requirements');
        if (!response.ok) throw new Error('Không thể tải job requirements');
        const jobReqs = await response.json();
        const select = document.querySelector('#job-requirement-select');
        select.innerHTML = '<option value="">Chọn Job Requirement</option>';
        jobReqs.forEach(jr => {
            const option = document.createElement('option');
            option.value = jr.id;
            option.textContent = jr.job_title;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Lỗi khi lấy job requirements:', error);
        alert('Không thể tải job requirements.');
    }
}

async function fetchMatchResults(jobId) {
    showLoading();
    try {
        const response = await fetch(`/api/dashboard/match-results/${jobId}`);
        if (!response.ok) throw new Error('Không thể tải kết quả matching');
        const data = await response.json();
        const matchResults = document.querySelector('#match-results');
        matchResults.innerHTML = '<h3 class="text-lg font-semibold text-gray-800 mb-2">Top Matching Candidates</h3>';
        if (data.matches.length === 0) {
            matchResults.innerHTML += '<p class="text-gray-600">Không tìm thấy ứng viên phù hợp.</p>';
        } else {
            matchResults.innerHTML += `
                <ul class="list-disc pl-5 space-y-2">
                    ${data.matches.map(match => `
                        <li>
                            <strong>${match.candidate.full_name}</strong> (${match.candidate.email}) - 
                            Score: ${match.match_score}% 
                            (Skills: ${match.skill_match}%, Experience: ${match.experience_match}%, Education: ${match.education_match}%)
                            <button onclick="viewCandidate(${match.candidate.id})" class="ml-2 text-blue-500 hover:underline">View</button>
                        </li>
                    `).join('')}
                </ul>
            `;
        }
    } catch (error) {
        console.error('Lỗi khi lấy kết quả matching:', error);
        alert('Không thể tải kết quả matching.');
    } finally {
        hideLoading();
    }
}

async function createJobRequirement(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const jobData = {
        job_title: formData.get('job_title'),
        required_skills: formData.get('required_skills').split(',').map(s => s.trim()).filter(s => s),
        preferred_skills: formData.get('preferred_skills').split(',').map(s => s.trim()).filter(s => s),
        min_experience_years: parseInt(formData.get('min_experience_years') || 0),
        education_requirements: {
            level: formData.get('education_level'),
            major: ''
        }
    };

    try {
        const response = await fetch('/api/requirements', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(jobData)
        });
        if (!response.ok) throw new Error('Tạo job requirement thất bại');
        alert('Tạo job requirement thành công!');
        document.querySelector('#create-job-modal').style.display = 'none';
        form.reset();
        fetchJobRequirements();
    } catch (error) {
        console.error('Lỗi khi tạo job requirement:', error);
        alert('Tạo job requirement thất bại.');
    }
}

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

document.querySelector('#create-job-form').addEventListener('submit', createJobRequirement);

document.querySelector('#refresh-button').addEventListener('click', () => {
    fetchCandidates();
    fetchDashboardStats();
    fetchJobRequirements();
});

document.querySelector('#upload-resume-button').addEventListener('click', () => {
    document.querySelector('#upload-modal').style.display = 'flex';
});

document.querySelector('#create-job-button').addEventListener('click', () => {
    document.querySelector('#create-job-modal').style.display = 'flex';
});

document.querySelector('#create-job-cancel').addEventListener('click', () => {
    document.querySelector('#create-job-modal').style.display = 'none';
    document.querySelector('#create-job-form').reset();
});

document.querySelector('#upload-cancel').addEventListener('click', () => {
    document.querySelector('#upload-modal').style.display = 'none';
});

document.querySelector('#candidate-modal .modal-close').addEventListener('click', () => {
    document.querySelector('#candidate-modal').style.display = 'none';
});

document.querySelector('#match-button').addEventListener('click', () => {
    const jobId = document.querySelector('#job-requirement-select').value;
    if (jobId) fetchMatchResults(jobId);
    else alert('Vui lòng chọn một Job Requirement.');
});

document.addEventListener('DOMContentLoaded', () => {
    fetchCandidates();
    fetchDashboardStats();
    fetchJobRequirements();
});

document.querySelector('#create-job-button').addEventListener('click', () => {
    document.querySelector('#job-modal').style.display = 'block';
});

document.querySelector('#job-modal .modal-close').addEventListener('click', () => {
    document.querySelector('#job-modal').style.display = 'none';
});

document.querySelector('#job-cancel').addEventListener('click', () => {
    document.querySelector('#job-modal').style.display = 'none';
});

document.querySelector('#job-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    showLoading();
    try {
        const form = event.target;
        const jobTitle = form.job_title.value;
        const requiredSkills = form.required_skills.value.split(',').map(s => s.trim()).filter(s => s);
        const preferredSkills = form.preferred_skills.value.split(',').map(s => s.trim()).filter(s => s);
        const minExperienceYears = parseInt(form.min_experience_years.value);
        let educationRequirements;
        try {
            educationRequirements = JSON.parse(form.education_requirements.value);
        } catch (e) {
            throw new Error('Invalid JSON format for education requirements');
        }

        const response = await fetch('/api/jobs/requirements', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                job_title: jobTitle,
                required_skills: requiredSkills,
                preferred_skills: preferredSkills,
                min_experience_years: minExperienceYears,
                education_requirements: educationRequirements,
            }),
        });

        if (!response.ok) {
            throw new Error('Failed to create job requirement');
        }

        alert('Job requirement created successfully');
        document.querySelector('#job-modal').style.display = 'none';
        form.reset();
    } catch (error) {
        console.error('Error creating job:', error);
        alert(`Failed to create job: ${error.message}`);
    } finally {
        hideLoading();
    }
});