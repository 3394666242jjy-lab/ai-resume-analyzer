/**
 * AI 简历分析系统前端逻辑
 */

// API 基础地址配置
// 优先级: window.API_BASE > localStorage > 自动推断
function getApiBase() {
    // 1. 全局变量覆盖（部署时注入）
    if (window.API_BASE) return window.API_BASE;

    // 2. localStorage 用户自定义
    const saved = localStorage.getItem('api_base');
    if (saved) return saved;

    // 3. 根据域名自动推断
    const host = window.location.host;
    if (host.includes('localhost') || host.includes('127.0.0.1')) {
        return 'http://localhost:8000/api/v1';
    }
    // GitHub Pages 或其他静态托管，默认使用相对路径
    // 部署时请修改此处或在 localStorage 中设置 api_base
    return '/api/v1';
}

const API_BASE = getApiBase();

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileNameEl = document.getElementById('fileName');
const btnRemove = document.getElementById('btnRemove');
const jobDescription = document.getElementById('jobDescription');
const btnAnalyze = document.getElementById('btnAnalyze');
const progressBar = document.getElementById('progressBar');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultSection = document.getElementById('resultSection');
const toast = document.getElementById('toast');

// 状态
let currentFile = null;

// ========== 事件监听 ==========

uploadArea.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
});

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
});

btnRemove.addEventListener('click', (e) => {
    e.stopPropagation();
    currentFile = null;
    fileInput.value = '';
    fileInfo.style.display = 'none';
    uploadArea.style.display = 'block';
    updateAnalyzeButton();
});

jobDescription.addEventListener('input', updateAnalyzeButton);

btnAnalyze.addEventListener('click', startAnalyze);

// ========== 功能函数 ==========

function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showToast('仅支持 PDF 格式文件', 'error');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        showToast('文件大小超过 10MB 限制', 'error');
        return;
    }
    currentFile = file;
    fileNameEl.textContent = file.name;
    fileInfo.style.display = 'flex';
    uploadArea.style.display = 'none';
    updateAnalyzeButton();
}

function updateAnalyzeButton() {
    const hasFile = currentFile !== null;
    const hasJob = jobDescription.value.trim().length >= 10;
    btnAnalyze.disabled = !(hasFile && hasJob);
}

function setProgress(percent, text) {
    progressBar.style.display = 'block';
    progressFill.style.width = percent + '%';
    if (text) progressText.textContent = text;
}

function hideProgress() {
    progressBar.style.display = 'none';
    progressFill.style.width = '0%';
}

function showToast(message, type = 'info') {
    toast.textContent = message;
    toast.className = 'toast ' + type;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

async function startAnalyze() {
    if (!currentFile || !jobDescription.value.trim()) return;

    btnAnalyze.disabled = true;
    const btnText = btnAnalyze.querySelector('.btn-text');
    const btnLoading = btnAnalyze.querySelector('.btn-loading');
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    resultSection.style.display = 'none';

    try {
        setProgress(10, '正在上传简历...');

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('job_description', jobDescription.value.trim());

        setProgress(30, '正在解析 PDF...');

        const response = await fetch(`${API_BASE}/resume/upload-and-match`, {
            method: 'POST',
            body: formData,
        });

        setProgress(80, '正在分析匹配度...');

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${response.status})`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || '分析失败');
        }

        setProgress(100, '分析完成！');
        setTimeout(() => {
            hideProgress();
            renderResults(data);
            showToast('分析完成！', 'success');
        }, 500);

    } catch (error) {
        hideProgress();
        showToast(error.message || '分析过程中出现错误', 'error');
        console.error(error);
    } finally {
        btnAnalyze.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

function renderResults(data) {
    const resumeInfo = data.resume_info || {};
    const matchScore = data.match_score || {};

    const overall = Math.round(matchScore.overall_score || 0);
    const skill = Math.round(matchScore.skill_match_rate || 0);
    const exp = Math.round(matchScore.experience_match_rate || 0);
    const edu = Math.round(matchScore.education_match_rate || 0);

    document.getElementById('overallScore').textContent = overall;
    document.getElementById('skillScore').textContent = skill + '%';
    document.getElementById('expScore').textContent = exp + '%';
    document.getElementById('eduScore').textContent = edu + '%';

    const circle = document.getElementById('scoreCircle');
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (overall / 100) * circumference;
    circle.style.strokeDashoffset = offset;

    let color = '#ef4444';
    if (overall >= 60) color = '#f59e0b';
    if (overall >= 80) color = '#10b981';
    circle.style.stroke = color;
    document.getElementById('overallScore').style.color = color;

    setTimeout(() => {
        document.getElementById('skillBar').style.width = skill + '%';
        document.getElementById('expBar').style.width = exp + '%';
        document.getElementById('eduBar').style.width = edu + '%';
    }, 100);

    document.getElementById('analysisText').textContent = matchScore.analysis || '';

    const matchedContainer = document.getElementById('matchedKeywords');
    const missingContainer = document.getElementById('missingKeywords');
    matchedContainer.innerHTML = '';
    missingContainer.innerHTML = '';

    (matchScore.matched_keywords || []).forEach(kw => {
        const tag = document.createElement('span');
        tag.className = 'keyword-tag matched';
        tag.textContent = kw;
        matchedContainer.appendChild(tag);
    });

    (matchScore.missing_keywords || []).forEach(kw => {
        const tag = document.createElement('span');
        tag.className = 'keyword-tag missing';
        tag.textContent = kw;
        missingContainer.appendChild(tag);
    });

    renderBasicInfo(resumeInfo.basic_info || {});
    renderJobIntention(resumeInfo.job_intention || {});
    renderEducation(resumeInfo.education_background || []);
    renderWorkExperience(resumeInfo.work_experience || []);
    renderProjectExperience(resumeInfo.project_experience || []);
    renderSkills(resumeInfo.skills || []);

    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function renderBasicInfo(info) {
    const container = document.getElementById('basicInfo');
    const fields = [
        { key: 'name', label: '姓名' },
        { key: 'phone', label: '电话' },
        { key: 'email', label: '邮箱' },
        { key: 'address', label: '地址' },
    ];
    container.innerHTML = fields.map(f => `
        <div class="info-item">
            <span class="info-label">${f.label}</span>
            <span class="info-value ${info[f.key] ? '' : 'empty'}">${info[f.key] || '未提取'}</span>
        </div>
    `).join('');
}

function renderJobIntention(info) {
    const container = document.getElementById('jobIntention');
    const fields = [
        { key: 'position', label: '求职岗位' },
        { key: 'expected_salary', label: '期望薪资' },
        { key: 'expected_city', label: '期望城市' },
    ];
    container.innerHTML = fields.map(f => `
        <div class="info-item">
            <span class="info-label">${f.label}</span>
            <span class="info-value ${info[f.key] ? '' : 'empty'}">${info[f.key] || '未提取'}</span>
        </div>
    `).join('');
}

function renderEducation(list) {
    const container = document.getElementById('educationBg');
    if (!list.length) {
        container.innerHTML = '<div class="info-value empty">未提取到教育背景</div>';
        return;
    }
    container.innerHTML = list.map(item => `
        <div class="info-list-item">
            <div class="item-title">${item.school || '未知学校'} · ${item.degree || '未知学历'}</div>
            <div class="item-subtitle">${item.major || ''} ${item.duration ? '| ' + item.duration : ''}</div>
        </div>
    `).join('');
}

function renderWorkExperience(list) {
    const container = document.getElementById('workExp');
    if (!list.length) {
        container.innerHTML = '<div class="info-value empty">未提取到工作经历</div>';
        return;
    }
    container.innerHTML = list.map(item => `
        <div class="info-list-item">
            <div class="item-title">${item.company || '未知公司'} · ${item.position || '未知职位'}</div>
            <div class="item-subtitle">${item.duration || ''}</div>
            <div class="item-desc">${item.description || ''}</div>
        </div>
    `).join('');
}

function renderProjectExperience(list) {
    const container = document.getElementById('projectExp');
    if (!list.length) {
        container.innerHTML = '<div class="info-value empty">未提取到项目经历</div>';
        return;
    }
    container.innerHTML = list.map(item => `
        <div class="info-list-item">
            <div class="item-title">${item.name || '未知项目'} · ${item.role || '未知角色'}</div>
            <div class="item-subtitle">${item.duration || ''}</div>
            <div class="item-desc">${item.description || ''}</div>
        </div>
    `).join('');
}

function renderSkills(list) {
    const container = document.getElementById('skillsList');
    if (!list.length) {
        container.innerHTML = '<div class="info-value empty">未提取到技能</div>';
        return;
    }
    container.innerHTML = list.map(skill => `
        <span class="skill-tag">${skill}</span>
    `).join('');
}

console.log('AI 简历分析系统已加载，API_BASE:', API_BASE);
