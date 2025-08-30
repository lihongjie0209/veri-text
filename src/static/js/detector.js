/**
 * 敏感词检测前端JavaScript
 * 简洁版本 - 只专注于检测功能
 */

// 全局变量
let isDetecting = false;

// 页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeDetector();
});

// 初始化检测器
function initializeDetector() {
    const form = document.getElementById('detectionForm');
    const textInput = document.getElementById('textInput');
    const exampleButtons = document.querySelectorAll('.example-btn');
    
    // 表单提交事件
    form.addEventListener('submit', handleDetection);
    
    // 字符计数
    textInput.addEventListener('input', updateCharCount);
    
    // 示例按钮事件
    exampleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const exampleText = this.dataset.text;
            textInput.value = exampleText;
            updateCharCount();
            
            // 清除之前的检测结果
            const resultContainer = document.getElementById('resultContainer');
            if (resultContainer) {
                resultContainer.style.display = 'none';
            }
        });
    });
    
    // 初始化字符计数
    updateCharCount();
}

// 更新字符计数
function updateCharCount() {
    const textInput = document.getElementById('textInput');
    const charCount = document.getElementById('charCount');
    const currentLength = textInput.value.length;
    
    charCount.textContent = currentLength;
    
    // 字符数接近限制时改变颜色
    if (currentLength > 9000) {
        charCount.className = 'text-danger fw-bold';
    } else if (currentLength > 8000) {
        charCount.className = 'text-warning fw-bold';
    } else {
        charCount.className = '';
    }
}

// 处理检测请求
async function handleDetection(event) {
    event.preventDefault();
    
    if (isDetecting) return;
    
    const textInput = document.getElementById('textInput');
    const text = textInput.value.trim();
    
    if (!text) {
        showAlert('请输入要检测的文本内容', 'warning');
        return;
    }
    
    try {
        setDetectingState(true);
        
        // 构建检测请求
        const detectionMode = document.getElementById('detectionMode').value;
        const returnPositions = document.getElementById('returnPositions').checked;
        const returnSuggestions = document.getElementById('returnSuggestions').checked;
        
        const requestData = {
            text: text,
            config: {
                detection_mode: detectionMode,
                return_positions: returnPositions,
                return_suggestions: returnSuggestions
            }
        };
        
        // 发送检测请求
        const response = await fetch('/api/v1/detect/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success !== false) {
            displayDetectionResults(data);
        } else {
            throw new Error(data.message || '检测请求失败');
        }
        
    } catch (error) {
        console.error('检测失败:', error);
        showAlert('检测失败: ' + error.message, 'danger');
    } finally {
        setDetectingState(false);
    }
}

// 设置检测状态
function setDetectingState(detecting) {
    isDetecting = detecting;
    const submitBtn = document.querySelector('#detectionForm button[type="submit"]');
    
    if (detecting) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>检测中...';
    } else {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="bi bi-search"></i> 开始检测';
    }
}

// 显示检测结果
function displayDetectionResults(data) {
    const resultContainer = document.getElementById('resultContainer');
    const resultContent = document.getElementById('resultContent');
    
    // 总体结果状态
    const isSensitive = data.is_sensitive;
    const riskLevel = data.risk_level;
    const overallScore = data.overall_score;
    const detectionTime = data.detection_time_ms;
    
    let html = '';
    
    // 检测总结
    html += `
        <div class="alert ${isSensitive ? 'alert-danger' : 'alert-success'} mb-4">
            <div class="d-flex align-items-center">
                <div class="me-3">
                    <i class="bi ${isSensitive ? 'bi-shield-exclamation' : 'bi-shield-check'} fs-2"></i>
                </div>
                <div class="flex-grow-1">
                    <h5 class="alert-heading mb-2">
                        ${isSensitive ? '⚠️ 发现敏感内容' : '✅ 未发现敏感内容'}
                    </h5>
                    <div class="row">
                        <div class="col-md-3">
                            <strong>风险等级:</strong> 
                            <span class="badge ${getRiskLevelClass(riskLevel)}">${getRiskLevelText(riskLevel)}</span>
                        </div>
                        <div class="col-md-3">
                            <strong>敏感度:</strong> 
                            <span class="badge bg-info">${(overallScore * 100).toFixed(1)}%</span>
                        </div>
                        <div class="col-md-3">
                            <strong>检测耗时:</strong> 
                            <span class="badge bg-secondary">${detectionTime}ms</span>
                        </div>
                        <div class="col-md-3">
                            <strong>检测模式:</strong> 
                            <span class="badge bg-primary">${getDetectionModeText(data.detection_mode_used)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 敏感内容详情
    if (isSensitive && data.results && data.results.length > 0) {
        html += `
            <div class="mb-4">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-list-ul"></i> 敏感内容详情 
                    <span class="badge bg-danger">${data.results.length} 项</span>
                </h6>
        `;
        
        data.results.forEach((result, index) => {
            const categoryClass = getCategoryClass(result.category);
            html += `
                <div class="result-item ${categoryClass}">
                    <div class="row align-items-center">
                        <div class="col-md-3">
                            <strong class="text-danger">"${escapeHtml(result.matched_word)}"</strong>
                        </div>
                        <div class="col-md-2">
                            <span class="badge ${getCategoryBadgeClass(result.category)}">${result.category}</span>
                        </div>
                        <div class="col-md-2">
                            <span class="badge bg-warning text-dark">${(result.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div class="col-md-2">
                            <small class="text-muted">${result.match_type}</small>
                        </div>
                        <div class="col-md-3">
                            ${result.positions && result.positions.length > 0 ? 
                                `<small class="text-muted">位置: ${result.positions.map(p => `${p.start}-${p.end}`).join(', ')}</small>` 
                                : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    // 检测统计
    if (data.summary) {
        html += `
            <div class="stats-card">
                <h6 class="fw-bold mb-3">
                    <i class="bi bi-bar-chart"></i> 检测统计
                </h6>
                <div class="row">
                    <div class="col-md-4">
                        <div class="text-center">
                            <div class="fs-3 fw-bold">${data.summary.total_matches}</div>
                            <small>总匹配数</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center">
                            <div class="fs-3 fw-bold">${data.summary.categories_found.length}</div>
                            <small>涉及分类</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="text-center">
                            <div class="fs-3 fw-bold">${data.summary.highest_risk_category || '-'}</div>
                            <small>最高风险分类</small>
                        </div>
                    </div>
                </div>
                ${data.summary.categories_found.length > 0 ? `
                    <div class="mt-3">
                        <strong>涉及分类:</strong> 
                        ${data.summary.categories_found.map(cat => 
                            `<span class="badge bg-light text-dark me-1">${cat}</span>`
                        ).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    resultContent.innerHTML = html;
    resultContainer.style.display = 'block';
    
    // 滚动到结果区域
    resultContainer.scrollIntoView({ behavior: 'smooth' });
}

// 工具函数
function getRiskLevelClass(level) {
    const classes = {
        'low': 'bg-success',
        'medium': 'bg-warning text-dark',
        'high': 'bg-danger',
        'critical': 'bg-dark'
    };
    return classes[level] || 'bg-secondary';
}

function getRiskLevelText(level) {
    const texts = {
        'low': '低风险',
        'medium': '中等风险', 
        'high': '高风险',
        'critical': '极高风险'
    };
    return texts[level] || level;
}

function getDetectionModeText(mode) {
    const modes = {
        'rule': '规则检测'
    };
    return modes[mode] || mode;
}

function getCategoryClass(category) {
    if (category.includes('政治')) return 'category-political';
    if (category.includes('色情')) return 'category-pornographic';
    if (category.includes('暴力')) return 'category-violent';
    if (category.includes('垃圾') || category.includes('spam')) return 'category-spam';
    if (category.includes('网络') || category.includes('安全')) return 'category-cybersecurity';
    return '';
}

function getCategoryBadgeClass(category) {
    if (category.includes('政治')) return 'bg-danger';
    if (category.includes('色情')) return 'bg-warning text-dark';
    if (category.includes('暴力')) return 'bg-dark';
    if (category.includes('垃圾') || category.includes('spam')) return 'bg-secondary';
    if (category.includes('网络') || category.includes('安全')) return 'bg-info';
    return 'bg-secondary';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showAlert(message, type = 'info') {
    // 创建alert元素
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 400px;';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // 插入到页面
    document.body.appendChild(alert);
    
    // 自动隐藏
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}
