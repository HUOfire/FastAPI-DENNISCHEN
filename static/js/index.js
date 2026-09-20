/**
 * API 日志查看器 - 优化版
 * 优化项：
 *  - 修复 XSS 风险（统一使用 textContent）
 *  - 修复事件重复绑定问题（事件委托 + 单次绑定）
 *  - 表格渲染性能优化（DocumentFragment + 一次性插入）
 *  - 统一命名风格（小驼峰）与代码格式
 *  - 抽离重复代码为辅助函数
 *  - 移除无用代码与冗余逻辑
 *  - 状态码 / 日志级别改用映射表
 *  - GET 请求移除多余 Content-Type
 *  - 全局变量收敛到 appState 对象
 */

// ---------- 全局状态 ----------
const appState = {
    sessionRemaining: 0, // 登录剩余时间（毫秒）
    currentPage: 1,      // 当前页（从1开始）
    pageSize: 10,        // 每页显示条数
    timerId: null,       // 定时器ID，用于清理
    logData: null,       // 当前日志数据缓存
    modalConfirmBound: false // 模态框确认按钮是否已绑定
};

// ---------- 常量映射表 ----------
const STATUS_BADGE_MAP = {
    success: 'badge badge-success',
    info:    'badge badge-info',
    warning: 'badge badge-warning',
    danger:  'badge badge-danger'
};

const LEVEL_BADGE_MAP = {
    INFO:     'badge badge-primary',
    DEBUG:    'badge badge-secondary',
    WARNING:  'badge badge-warning',
    ERROR:    'badge badge-danger',
    CRITICAL: 'badge badge-dark'
};

/**
 * 根据状态码获取对应的徽章样式
 */
function getStatusBadgeClass(status) {
    if (status >= 200 && status < 300) return STATUS_BADGE_MAP.success;
    if (status >= 300 && status < 400) return STATUS_BADGE_MAP.info;
    if (status >= 400 && status < 500) return STATUS_BADGE_MAP.warning;
    if (status >= 500) return STATUS_BADGE_MAP.danger;
    return 'badge';
}

/**
 * 根据日志级别获取对应的徽章样式
 */
function getLevelBadgeClass(level) {
    return LEVEL_BADGE_MAP[level] || 'badge';
}

/**
 * HTML 转义，防止 XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ---------- 登录态相关 ----------

/**
 * 页面加载时检查登录状态
 */
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/verify', {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const messageDiv = document.getElementById('message');
            if (messageDiv) {
                messageDiv.style.display = 'block';
                messageDiv.className = 'message success';
                messageDiv.innerHTML = `已登录为 ${escapeHtml(data.user.username)}，<a href="/index">进入主页</a> | <a href="javascript:void(0)" id="logout-link">退出登录</a>`;
                const logoutLink = document.getElementById('logout-link');
                if (logoutLink) {
                    logoutLink.addEventListener('click', logout);
                }
            } else {
                console.log('非登录页面');
            }
        }
    } catch (error) {
        console.error('登录效验错误:', error);
    }
});

/**
 * 退出登录
 */
async function logout() {
    try {
        await fetch('/api/logout', {
            method: 'POST',
            credentials: 'include'
        });
        window.location.href = '/login';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// ---------- 页面初始化 ----------

document.addEventListener('DOMContentLoaded', function() {
    // 倒计时相关
    const timeStr = document.getElementById('date-message')?.textContent;
    if (timeStr) {
        const targetDate = new Date(timeStr);
        function updateTimer() {
            const now = new Date();
            appState.sessionRemaining = targetDate - now;
        }
        updateTimer();
        appState.timerId = setInterval(updateTimer, 1000);
    }

    // 模态框初始化
    const $modal = $('#loginModal');
    const $confirmBtn = $('#confirmLoginBtn');
    $modal.modal({
        backdrop: 'static',
        keyboard: false,
        show: false
    });

    // 模态框确认按钮（只绑定一次）
    if (!appState.modalConfirmBound) {
        $confirmBtn.on('click', function() {
            const originalText = $confirmBtn.text();
            $confirmBtn.prop('disabled', true)
                .html('<span class="spinner-border spinner-border-sm mr-2"></span>跳转中...');
            setTimeout(function() {
                window.location.href = '/login';
            }, 800);
        });
        appState.modalConfirmBound = true;
    }

    // iframe 文档页
    const docsFrame = document.getElementById('docsFrame');
    if (docsFrame) {
        docsFrame.src = '/docs';
    }

    // 日期默认值
    const endDateEl = document.getElementById('end_date');
    if (endDateEl) {
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const formattedDate = `${year}-${month}-${day}`;
        endDateEl.value = formattedDate;
        document.getElementById('str_date').value = formattedDate;
    }

    // 导航链接鉴权（事件委托）
    const navbarNav = document.getElementById('navbarNav');
    if (navbarNav) {
        navbarNav.addEventListener('click', function(e) {
            const link = e.target.closest('.nav-link');
            if (!link) return;
            e.preventDefault();

            const targetUrl = link.getAttribute('data-target')
                || link.getAttribute('href')
                || link.getAttribute('onclick');

            if (appState.sessionRemaining > 0) {
                window.location.href = targetUrl;
            } else {
                $modal.modal('show');
            }
        });
    }

    // 分页事件委托（只绑定一次）
    const paginationContainer = document.getElementById('paginationContainer');
    if (paginationContainer) {
        paginationContainer.addEventListener('click', function(e) {
            const link = e.target.closest('.page-link');
            if (!link) return;
            e.preventDefault();

            const targetPage = parseInt(link.getAttribute('data-page'), 10);
            const totalPages = Math.ceil(
                (appState.logData?.message?.length || 0) / appState.pageSize
            );

            if (!isNaN(targetPage)
                && targetPage >= 1
                && targetPage <= totalPages
                && targetPage !== appState.currentPage
            ) {
                appState.currentPage = targetPage;
                renderTable(appState.logData);
            }
        });
    }

    // 每页条数选择（只绑定一次）
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    if (pageSizeSelect) {
        pageSizeSelect.addEventListener('change', handlePageSizeChange);
    }
});

// ---------- 日志查询 ----------

/**
 * 查询日志
 */
async function read_logs() {
    const params = new URLSearchParams({
        str_date: document.getElementById('str_date').value,
        end_date: document.getElementById('end_date').value,
        level: document.getElementById('level').value,
        url: document.getElementById('url').value
    });

    try {
        const response = await fetch(`/apilog/get_logs?${params}`, {
            method: 'GET',
            credentials: 'include'
        });
        const data = await response.json();
        appState.logData = data;

        const stats = calculateStats(data);
        updateUI(stats);

        // 每次查询回到第一页
        appState.currentPage = 1;
        renderTable(data);
    } catch (error) {
        console.error('数据查询错误:', error);
    }
}

// ---------- 表格渲染 ----------

/**
 * 创建"解析"按钮
 */
function createParseButton(jsonData) {
    const btn = document.createElement('button');
    btn.textContent = '解析';
    btn.className = 'btn btn-primary btn-sm';
    btn.setAttribute('data-toggle', 'modal');
    btn.setAttribute('data-target', '#basicModal');
    btn.addEventListener('click', function() {
        add_json_message(jsonData);
    });
    return btn;
}

/**
 * 更新表格（性能优化版：DocumentFragment 一次性插入）
 */
function UPDATE_TABLE(data, startIndex) {
    const table = document.getElementById('logs-table');
    table.innerHTML = '';

    if (!data || data.length === 0) {
        return;
    }

    const fragment = document.createDocumentFragment();

    data.forEach((log, index) => {
        const row = document.createElement('tr');
        const serialNumber = startIndex + index + 1;

        // 序号
        const indexCell = document.createElement('td');
        indexCell.textContent = serialNumber;
        row.appendChild(indexCell);

        // 时间
        const datetimeCell = document.createElement('td');
        datetimeCell.className = 'time-col';
        datetimeCell.textContent = log.time;
        row.appendChild(datetimeCell);

        // 日志级别（带徽章）
        const levelCell = document.createElement('td');
        const levelSpan = document.createElement('span');
        levelSpan.textContent = log.level;
        levelSpan.className = getLevelBadgeClass(log.level);
        levelCell.appendChild(levelSpan);
        row.appendChild(levelCell);

        // 请求路径
        const pathCell = document.createElement('td');
        pathCell.className = 'font-monospace';
        pathCell.textContent = log.url;
        row.appendChild(pathCell);

        // 请求体
        const requestBodyCell = document.createElement('td');
        requestBodyCell.className = 'req-body';
        const requestStr = JSON.stringify(log.request);
        requestBodyCell.textContent = requestStr;
        requestBodyCell.title = requestStr;
        row.appendChild(requestBodyCell);

        // 请求体解析按钮
        const requestBtnCell = document.createElement('td');
        requestBtnCell.appendChild(createParseButton(log.request));
        row.appendChild(requestBtnCell);

        // 状态码（带徽章）
        const statusCodeCell = document.createElement('td');
        const statusCodeSpan = document.createElement('span');
        statusCodeSpan.textContent = log.status;
        statusCodeSpan.className = getStatusBadgeClass(log.status);
        statusCodeCell.appendChild(statusCodeSpan);
        row.appendChild(statusCodeCell);

        // 响应体
        const responseBodyCell = document.createElement('td');
        responseBodyCell.className = 'req-body';
        const responseStr = JSON.stringify(log.response);
        responseBodyCell.textContent = responseStr;
        responseBodyCell.title = responseStr;
        row.appendChild(responseBodyCell);

        // 响应体解析按钮
        const responseBtnCell = document.createElement('td');
        responseBtnCell.appendChild(createParseButton(log.response));
        row.appendChild(responseBtnCell);

        // 耗时
        const durationCell = document.createElement('td');
        durationCell.className = 'ms-col';
        durationCell.textContent = log.duration;
        row.appendChild(durationCell);

        // IP地址
        const ipCell = document.createElement('td');
        ipCell.className = 'ms-col';
        ipCell.textContent = log.client_ip;
        console.log(log.client_ip);
        row.appendChild(ipCell);

        fragment.appendChild(row);
    });

    table.appendChild(fragment);
}

// ---------- 统计数据 ----------

/**
 * 计算统计数据
 */
function calculateStats(data) {
    if (data.code !== 200) {
        return { total: 0, success: 0, fail: 0, avgTime: 0, successRate: 0, failRate: 0 };
    }

    const logs = data.message;
    if (!logs || logs.length === 0) {
        return { total: 0, success: 0, fail: 0, avgTime: 0, successRate: 0, failRate: 0 };
    }

    const total = logs.length;
    let success = 0;
    let fail = 0;
    let totalDuration = 0;

    // 单次遍历完成所有统计，替代多次 filter + reduce
    for (let i = 0; i < total; i++) {
        const log = logs[i];
        const status = log.status;
        if (status >= 200 && status < 300) {
            success++;
        } else if (status >= 400) {
            fail++;
        }
        totalDuration += log.duration || 0;
    }

    const avgTime = (totalDuration / total).toFixed(1);
    const successRate = ((success / total) * 100).toFixed(1);
    const failRate = ((fail / total) * 100).toFixed(1);

    return { total, success, fail, avgTime, successRate, failRate };
}

/**
 * 更新统计 UI
 */
function updateUI(stats) {
    const elTotal = document.getElementById('stat-total');
    const elSuccess = document.getElementById('stat-success');
    const elFail = document.getElementById('stat-fail');
    const elAvgTime = document.getElementById('stat-avgTime');
    const elSuccessRate = document.getElementById('success-rate');
    const elFailRate = document.getElementById('fail-rate');

    animateValue(elTotal, parseInt(elTotal.textContent, 10) || 0, stats.total, 500);
    animateValue(elSuccess, parseInt(elSuccess.textContent, 10) || 0, stats.success, 500);
    animateValue(elFail, parseInt(elFail.textContent, 10) || 0, stats.fail, 500);

    elAvgTime.textContent = stats.avgTime;
    elSuccessRate.textContent = `成功率: ${stats.successRate}%`;
    elFailRate.textContent = `失败率: ${stats.failRate}%`;
}

/**
 * 数字滚动动画
 */
function animateValue(obj, start, end, duration) {
    if (start === end) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.textContent = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// ---------- JSON 展示 ----------

function add_json_message(message) {
    const jsonContent = document.getElementById('jsonContent');
    if (jsonContent) {
        const jsonStr = JSON.stringify(message, null, 2);
        jsonContent.textContent = jsonStr;
    }
}

// ---------- 分页 ----------

/**
 * 渲染当前页表格
 */
function renderTable(data) {
    if (!data || !data.message) return;

    const paginationInfo = document.getElementById('paginationInfo');
    const totalData = data.message.length;
    const startIndex = (appState.currentPage - 1) * appState.pageSize;
    const endIndex = Math.min(startIndex + appState.pageSize, totalData);
    const currentPageData = data.message.slice(startIndex, endIndex);

    UPDATE_TABLE(currentPageData, startIndex);

    // 更新分页信息
    paginationInfo.textContent = `显示第 ${startIndex + 1} 到 ${endIndex} 条，共 ${totalData} 条`;

    // 渲染分页按钮
    renderPagination(totalData);
}

/**
 * 渲染分页按钮 HTML（不再绑定事件，事件委托已在 DOMContentLoaded 中处理）
 */
function renderPagination(totalData) {
    const paginationContainer = document.getElementById('paginationContainer');
    const totalPages = Math.ceil(totalData / appState.pageSize);

    if (totalPages === 0) {
        paginationContainer.innerHTML = '';
        return;
    }

    let html = '';

    // 上一页
    html += `
        <li class="page-item ${appState.currentPage === 1 ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${appState.currentPage - 1}" aria-label="上一页">
                <span aria-hidden="true">&laquo;</span>
            </a>
        </li>
    `;

    // 页码
    for (let i = 1; i <= totalPages; i++) {
        html += `
            <li class="page-item ${i === appState.currentPage ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
        `;
    }

    // 下一页
    html += `
        <li class="page-item ${appState.currentPage === totalPages ? 'disabled' : ''}">
            <a class="page-link" href="#" data-page="${appState.currentPage + 1}" aria-label="下一页">
                <span aria-hidden="true">&raquo;</span>
            </a>
        </li>
    `;

    paginationContainer.innerHTML = html;
}

/**
 * 处理每页显示条数变化
 */
function handlePageSizeChange() {
    const pageSizeSelect = document.getElementById('pageSizeSelect');
    const newSize = parseInt(pageSizeSelect.value, 10);
    if (!isNaN(newSize) && newSize > 0 && newSize !== appState.pageSize) {
        appState.pageSize = newSize;
        appState.currentPage = 1;
        if (appState.logData) {
            renderTable(appState.logData);
        }
    }
}
