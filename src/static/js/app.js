// 全局变量
let detectionHistory = [];
const API_BASE = '';

// DOM元素
const textInput = document.getElementById('text-input');
const charCount = document.getElementById('char-count');
const detectionForm = document.getElementById('detection-form');
const detectBtn = document.getElementById('detect-btn');
const clearBtn = document.getElementById('clear-btn');
const resultsArea = document.getElementById('results-area');
const statsCard = document.getElementById('stats-card');
const statsArea = document.getElementById('stats-area');
const historyArea = document.getElementById('history-area');
const clearHistoryBtn = document.getElementById('clear-history-btn');
const healthStatus = document.getElementById('health-status');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    loadHistoryFromStorage();
    checkHealthStatus();
    
    // 定期检查健康状态
    setInterval(checkHealthStatus, 30000); // 每30秒检查一次
});

// 初始化应用
function initializeApp() {
    
    // 字符计数
    textInput.addEventListener('input', updateCharCount);
    
    // 表单提交
    detectionForm.addEventListener('submit', handleDetection);
    
    // 清空按钮
    clearBtn.addEventListener('click', clearForm);
    
    // 清空历史按钮
    clearHistoryBtn.addEventListener('click', clearHistory);
    
    // 初始化字符计数
    updateCharCount();
}

// 更新字符计数
function updateCharCount() {
    const count = textInput.value.length;
    charCount.textContent = count;
    
    // 字符数颜色提示
    charCount.className = '';
    if (count > 8000) {
        charCount.classList.add('char-count-danger');
    } else if (count > 6000) {
        charCount.classList.add('char-count-warning');
    }
}

// 检查健康状态
async function checkHealthStatus() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/health/`);
        const data = await response.json();
        
        const indicator = healthStatus.querySelector('.health-indicator');
        if (data.status === 'healthy') {
            indicator.textContent = '运行正常';
            indicator.className = 'health-indicator health-status-healthy';
        } else {
            indicator.textContent = '服务异常';
            indicator.className = 'health-indicator health-status-unhealthy';
        }
    } catch (error) {
        const indicator = healthStatus.querySelector('.health-indicator');
        indicator.textContent = '连接失败';
        indicator.className = 'health-indicator health-status-unhealthy';
    }
}

// 处理检测请求
async function handleDetection(event) {
    event.preventDefault();
    
    const text = textInput.value.trim();
    if (!text) {
        showError('请输入要检测的文本');
        return;
    }
    
    // 获取配置
    const config = getDetectionConfig();
    
    // 构建请求数据
    const requestData = {
        text: text,
        config: config
    };
    
    try {
        // 显示加载状态
        showLoading(true);
        
        // 发送检测请求
        const response = await fetch(`${API_BASE}/api/v1/detect/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const result = await response.json();
        
        // 显示结果
        displayResults(result);
        
        // 保存到历史
        saveToHistory(text, result, config);
        
        // 显示统计
        displayStats(result);
        
    } catch (error) {
        console.error('检测请求失败:', error);
        showError(`检测失败: ${error.message}`);
    } finally {
        // 确保隐藏加载状态
        showLoading(false);
    }
}

// 获取检测配置
function getDetectionConfig() {
    const detectionMode = document.getElementById('detection-mode').value;
    const strictnessLevel = document.getElementById('strictness-level').value;
    const returnPositions = document.getElementById('return-positions').checked;
    const returnSuggestions = document.getElementById('return-suggestions').checked;
    
    // 获取选中的分类
    const categories = [];
    document.querySelectorAll('.category-check:checked').forEach(checkbox => {
        categories.push(checkbox.value);
    });
    
    return {
        detection_mode: detectionMode,
        strictness_level: strictnessLevel,
        categories: categories,
        return_positions: returnPositions,
        return_suggestions: returnSuggestions,
        custom_threshold: 0.8
    };
}

// 显示检测结果
function displayResults(result) {
    const isSensitive = result.is_sensitive;
    const riskLevel = result.risk_level;
    const results = result.results || [];
    const summary = result.summary || {};
    
    let html = '';
    
    // 结果摘要
    html += `
        <div class="result-summary ${isSensitive ? 'sensitive' : 'safe'} fade-in">
            <div class="d-flex justify-content-between align-items-center mb-2">
                <h6 class="mb-0">
                    <i class="bi bi-${isSensitive ? 'exclamation-triangle-fill' : 'check-circle-fill'}"></i>
                    ${isSensitive ? '检测到敏感内容' : '内容安全'}
                </h6>
                <span class="risk-level ${riskLevel}">${getRiskLevelText(riskLevel)}</span>
            </div>
            <div class="row">
                <div class="col-6">
                    <small class="text-muted">检测时间</small><br>
                    <strong>${result.detection_time_ms}ms</strong>
                </div>
                <div class="col-6">
                    <small class="text-muted">风险评分</small><br>
                    <strong>${(result.overall_score * 100).toFixed(1)}%</strong>
                </div>
            </div>
        </div>
    `;
    
    // 敏感词详情
    if (results.length > 0) {
        html += '<div class="mb-3"><h6>检测详情</h6></div>';
        
        results.forEach((item, index) => {
            const confidencePercent = (item.confidence * 100).toFixed(1);
            const confidenceClass = getConfidenceClass(item.confidence);
            
            html += `
                <div class="sensitive-word-item fade-in" style="animation-delay: ${index * 0.1}s">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <div>
                            <strong>${escapeHtml(item.matched_word)}</strong>
                            <span class="category-badge category-${item.category}">
                                ${getCategoryText(item.category)}
                            </span>
                        </div>
                        <small class="text-muted">${item.detection_method.toUpperCase()}</small>
                    </div>
                    
                    <div class="mb-2">
                        <small class="text-muted">置信度: ${confidencePercent}%</small>
                        <div class="confidence-bar">
                            <div class="confidence-fill ${confidenceClass}" 
                                 style="width: ${confidencePercent}%"></div>
                        </div>
                    </div>
                    
                    ${item.positions && item.positions.length > 0 ? `
                        <small class="text-muted">
                            位置: ${item.positions.map(p => `${p.start}-${p.end}`).join(', ')}
                        </small>
                    ` : ''}
                    
                    ${item.suggestion ? `
                        <div class="mt-2">
                            <small class="text-muted">建议替换为: </small>
                            <code>${escapeHtml(item.suggestion)}</code>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }
    
    resultsArea.innerHTML = html;
}

// 显示统计信息
function displayStats(result) {
    const summary = result.summary || {};
    
    const html = `
        <div class="stats-item">
            <span>匹配总数</span>
            <span class="stats-value">${summary.total_matches || 0}</span>
        </div>
        <div class="stats-item">
            <span>检测类别</span>
            <span class="stats-value">${(summary.categories_found || []).length}</span>
        </div>
        <div class="stats-item">
            <span>检测模式</span>
            <span class="stats-value">${result.detection_mode_used?.toUpperCase() || 'N/A'}</span>
        </div>
        <div class="stats-item">
            <span>总体评分</span>
            <span class="stats-value">${(result.overall_score * 100).toFixed(1)}%</span>
        </div>
    `;
    
    statsArea.innerHTML = html;
    statsCard.style.display = 'block';
}

// 保存到历史记录
function saveToHistory(text, result, config) {
    const historyItem = {
        id: Date.now(),
        timestamp: new Date().toLocaleString('zh-CN'),
        text: text.substring(0, 100) + (text.length > 100 ? '...' : ''),
        fullText: text,
        result: result,
        config: config
    };
    
    detectionHistory.unshift(historyItem);
    
    // 限制历史记录数量
    if (detectionHistory.length > 50) {
        detectionHistory = detectionHistory.slice(0, 50);
    }
    
    // 保存到本地存储
    localStorage.setItem('veritext_history', JSON.stringify(detectionHistory));
    
    // 更新历史显示
    updateHistoryDisplay();
}

// 更新历史记录显示
function updateHistoryDisplay() {
    if (detectionHistory.length === 0) {
        historyArea.innerHTML = '<div class="text-center text-muted"><p>暂无检测历史</p></div>';
        return;
    }
    
    let html = '';
    detectionHistory.forEach((item, index) => {
        const isSensitive = item.result.is_sensitive;
        const riskLevel = item.result.risk_level;
        
        html += `
            <div class="history-item fade-in" style="animation-delay: ${index * 0.05}s">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div class="flex-grow-1">
                        <div class="d-flex align-items-center mb-1">
                            <i class="bi bi-${isSensitive ? 'exclamation-triangle-fill text-danger' : 'check-circle-fill text-success'} me-2"></i>
                            <span class="risk-level ${riskLevel} me-2">${getRiskLevelText(riskLevel)}</span>
                            <small class="text-muted">${item.timestamp}</small>
                        </div>
                        <div class="history-text">${escapeHtml(item.text)}</div>
                    </div>
                    <div class="ms-2">
                        <button class="btn btn-sm btn-outline-primary" onclick="rerunDetection(${item.id})">
                            <i class="bi bi-arrow-repeat"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteHistoryItem(${item.id})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
                <div class="history-meta">
                    匹配: ${item.result.summary?.total_matches || 0} | 
                    耗时: ${item.result.detection_time_ms}ms | 
                    模式: ${item.config.detection_mode}
                </div>
            </div>
        `;
    });
    
    historyArea.innerHTML = html;
}

// 从本地存储加载历史记录
function loadHistoryFromStorage() {
    try {
        const stored = localStorage.getItem('veritext_history');
        if (stored) {
            detectionHistory = JSON.parse(stored);
            updateHistoryDisplay();
        }
    } catch (error) {
        console.error('加载历史记录失败:', error);
    }
}

// 重新运行检测
function rerunDetection(historyId) {
    const item = detectionHistory.find(h => h.id === historyId);
    if (item) {
        textInput.value = item.fullText;
        updateCharCount();
        
        // 恢复配置
        document.getElementById('detection-mode').value = item.config.detection_mode;
        document.getElementById('strictness-level').value = item.config.strictness_level;
        document.getElementById('return-positions').checked = item.config.return_positions;
        document.getElementById('return-suggestions').checked = item.config.return_suggestions;
        
        // 恢复分类选择
        document.querySelectorAll('.category-check').forEach(checkbox => {
            checkbox.checked = item.config.categories.includes(checkbox.value);
        });
        
        // 滚动到顶部
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

// 删除历史记录项
function deleteHistoryItem(historyId) {
    detectionHistory = detectionHistory.filter(h => h.id !== historyId);
    localStorage.setItem('veritext_history', JSON.stringify(detectionHistory));
    updateHistoryDisplay();
}

// 清空表单
function clearForm() {
    textInput.value = '';
    updateCharCount();
    resultsArea.innerHTML = `
        <div class="text-center text-muted">
            <i class="bi bi-info-circle fs-1"></i>
            <p class="mt-2">请输入文本并点击"开始检测"</p>
        </div>
    `;
    statsCard.style.display = 'none';
    
    // 确保Modal处于正确状态
    const modalElement = document.getElementById('loading-modal');
    if (modalElement && modalElement.classList.contains('show')) {
        console.log('Clearing form with visible modal, forcing cleanup');
        // 强制清理Modal状态
        modalElement.classList.remove('show', 'fade');
        modalElement.style.display = 'none';
        modalElement.setAttribute('aria-hidden', 'true');
        modalElement.removeAttribute('aria-modal');
        
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
        document.body.style.paddingRight = '';
        
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
    }
}

// 清空历史记录
function clearHistory() {
    if (confirm('确定要清空所有历史记录吗？此操作不可撤销。')) {
        detectionHistory = [];
        localStorage.removeItem('veritext_history');
        updateHistoryDisplay();
    }
}

// 显示/隐藏加载状态 - 智能Modal管理解决方案
function showLoading(show) {
    console.log(`[${new Date().toISOString()}] showLoading called with:`, show);
    
    if (show) {
        detectBtn.disabled = true;
        detectBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>检测中...';
        
        // 显示modal
        const modalElement = document.getElementById('loading-modal');
        if (modalElement) {
            const modal = new bootstrap.Modal(modalElement, {
                backdrop: 'static',
                keyboard: false
            });
            modal.show();
            
            // 记录显示时间
            window.modalShowTime = Date.now();
            console.log(`[${new Date().toISOString()}] Modal shown at:`, window.modalShowTime);
        }
    } else {
        detectBtn.disabled = false;
        detectBtn.innerHTML = '<i class="bi bi-search"></i> 开始检测';
        
        // 智能隐藏策略：
        // 1. 如果API很快(<200ms)，设置较短延迟(300ms)以保证用户能看到loading效果
        // 2. 如果API较慢(>200ms)，立即隐藏
        const elapsed = Date.now() - (window.modalShowTime || 0);
        const isQuickResponse = elapsed < 200;
        const hideDelay = isQuickResponse ? Math.max(0, 300 - elapsed) : 0;
        
        console.log(`[${new Date().toISOString()}] API elapsed: ${elapsed}ms, hide delay: ${hideDelay}ms`);
        
        setTimeout(() => {
            console.log(`[${new Date().toISOString()}] Hiding modal now`);
            
            const modalElement = document.getElementById('loading-modal');
            if (modalElement) {
                // 使用Bootstrap的hide方法
                const modal = bootstrap.Modal.getInstance(modalElement);
                if (modal) {
                    modal.hide();
                } else {
                    // 如果没有实例，直接清理DOM状态
                    modalElement.classList.remove('show');
                    modalElement.style.display = 'none';
                    modalElement.setAttribute('aria-hidden', 'true');
                    modalElement.removeAttribute('aria-modal');
                    
                    document.body.classList.remove('modal-open');
                    document.body.style.overflow = '';
                    document.body.style.paddingRight = '';
                    
                    const backdrops = document.querySelectorAll('.modal-backdrop');
                    backdrops.forEach(backdrop => backdrop.remove());
                }
                
                console.log(`[${new Date().toISOString()}] Modal hidden successfully`);
            }
        }, hideDelay);
    }
}

// 显示错误信息
function showError(message) {
    resultsArea.innerHTML = `
        <div class="error-message fade-in">
            <i class="bi bi-exclamation-triangle-fill me-2"></i>
            ${escapeHtml(message)}
        </div>
    `;
}

// 工具函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getRiskLevelText(level) {
    const levels = {
        'low': '低风险',
        'medium': '中风险',
        'high': '高风险',
        'critical': '严重'
    };
    return levels[level] || level;
}

function getCategoryText(category) {
    const categories = {
        'political': '政治',
        'pornographic': '色情',
        'violent': '暴力',
        'spam': '广告',
        'privacy': '隐私'
    };
    return categories[category] || category;
}

function getConfidenceClass(confidence) {
    if (confidence >= 0.8) return 'confidence-high';
    if (confidence >= 0.5) return 'confidence-medium';
    return 'confidence-low';
}

// 键盘快捷键
document.addEventListener('keydown', function(event) {
    // Ctrl+Enter 提交检测
    if (event.ctrlKey && event.key === 'Enter') {
        event.preventDefault();
        if (!detectBtn.disabled) {
            detectBtn.click();
        }
    }
    
    // Ctrl+L 清空表单
    if (event.ctrlKey && event.key.toLowerCase() === 'l') {
        event.preventDefault();
        clearForm();
    }
});
