let diff = 0

// 页面加载时检查是否已登录
window.addEventListener('load', async () => {
    try {
            const response = await fetch('/api/verify', {
                credentials: 'include'
            });

            if (response.ok) {
                    // 已登录，显示提示
                    const data = await response.json();
                    const messageDiv = document.getElementById('message');
                    if(messageDiv){
                        messageDiv.style.display = 'block';
                        messageDiv.className = 'message success';
                        messageDiv.innerHTML = `已登录为 ${data.user.username}，<a href="/index">进入主页</a> | <a href="javascript:void(0)" onclick="logout()">退出登录</a>`;
                    }else{
                        console.log("非登录页面")
                    }
            }
        }
        catch (error) {
            // 未登录或 token 无效，忽略错误
            console.error('登时效验证错误:', error);
        }
});

async function logout() {
    try {
            await fetch('/api/logout', {
                    method: 'POST',
                    credentials: 'include'
            });
            window.location.href="/login";
        }
        catch (error) {
            console.error('Logout error:', error);
        }
}

//获取界面DOM元素
document.addEventListener('DOMContentLoaded', function() {
    const timeStr = document.getElementById('date-message').textContent;
    let targetDate = new Date(timeStr);
    function updateTimer() {
        const now = new Date();
        diff = targetDate - now; // 毫秒差值
    }

    const $modal = $('#loginModal');
    const $confirmBtn = $('#confirmLoginBtn');
    const element = document.getElementById('docsFrame');
    const end_date= document.getElementById('end_date');
    //判断iframe标签是否存在，决定是否加载页面内容
    if (element) {
        document.getElementById('docsFrame').src = "/docs";
    }
    if (end_date){
        const today = new Date();
        // 获取年、月、日
        const year = today.getFullYear();
        // 月份从0开始，需+1；且需补零（如 9 -> 09）
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        // 拼接成 YYYY-MM-DD格式
        const formattedDate = `${year}-${month}-${day}`;
        document.getElementById('end_date').value = formattedDate
        document.getElementById('str_date').value = formattedDate
    }
    // 初始化模态框配置
    // backdrop: 'static' 防止点击背景关闭
    // keyboard: false 防止按ESC键关闭
    $modal.modal({
        backdrop: 'static',
        keyboard: false,
        show: false // 初始不显示
    });
    // 5. 启动定时器 (每秒刷新)

    setInterval(updateTimer, 1000);
    updateTimer(); // 立即执行一次，避免页面加载时的1秒空白
        // 获取所有需要鉴权的导航链接
    const links = document.querySelectorAll('#navbarNav .nav-link');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault(); // 1. 阻止默认跳转
            const targetUrl = this.getAttribute('data-target') || this.getAttribute('href')|| this.getAttribute('onclick');
            // 2. 验证 Cookie 是否有效
            if (diff > 0) {
                // 有效：手动跳转
                window.location.href = targetUrl;
            } else {
                // 无效：显示弹窗
                $modal.modal('show');
                $confirmBtn.on('click', function() {
                // 1. 可选：添加加载状态反馈
                const originalText = $confirmBtn.text();
                $confirmBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm mr-2"></span>跳转中...');

                // 2. 执行跳转逻辑
                // 使用 setTimeout 模拟短暂的UI反馈，然后跳转
                setTimeout(function() {
                    window.location.href = '/login';
                }, 800);
            });
            }
        });
    });
});



async function read_logs(){
     const params = new URLSearchParams({
            str_date: document.getElementById('str_date').value,
            end_date: document.getElementById('end_date').value,
            level: document.getElementById('level').value
    });
    try {
        const response = await fetch(`/apilog/get_logs?${params}`, {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
        });
        const data = await response.json();
        const Stats = calculateStats(data);
        updateUI(Stats)
        // 更新表格
        UPDATE_TABLE(data);

    }
    catch (error) {
        console.log('数据查询错误:', error);
    }
}



//更新表格
function UPDATE_TABLE(data){
    const table = document.getElementById('logs-table');
    if (data.code === 200) {
            const logs = data.message;
            console.log(logs)
            table.innerHTML = '';
            logs.forEach(log => {
                const row = table.insertRow();
                const datetimeCell = row.insertCell();
                //带徽标的level
                const levelCell = row.insertCell();
                const level_span = document.createElement('span');
                level_span.textContent = log.level;
                //带徽标的level
                const pathCell = row.insertCell();
                const request_bodyCell = row.insertCell();
                //请求体解析按钮
                const request_str = JSON.stringify(log.request);
                const but_requestCell = row.insertCell();
                const but_request_but = document.createElement('button');
                but_request_but.textContent = "解析";
                but_request_but.className = "btn btn-primary btn-sm";
                but_request_but.setAttribute("data-toggle", "modal");
                but_request_but.setAttribute("data-target", "#basicModal");
                but_request_but.setAttribute("onclick",`add_json_message(${request_str})`);
                //请求体解析按钮
                //带徽标的status
                const status_codeCell = row.insertCell();
                const status_code_span = document.createElement('span');
                status_code_span.textContent = log.status;
                //带徽标的status
                const response_bodyCell = row.insertCell();
                //响应体解析按钮
                const response_str = JSON.stringify(log.response);
                const but_responseCell = row.insertCell();
                const but_response_but = document.createElement('button');
                but_response_but.textContent = "解析";
                but_response_but.className = "btn btn-primary btn-sm";
                but_response_but.setAttribute("data-toggle", "modal");
                but_response_but.setAttribute("data-target", "#basicModal");
                but_response_but.setAttribute("onclick",`add_json_message(${response_str})`);
                //响应体解析按钮
                const duration_msCell = row.insertCell();
                datetimeCell.innerHTML = log.time;
                levelCell.appendChild(level_span);
                pathCell.innerHTML = log.url;
                request_bodyCell.innerHTML = request_str;
                but_requestCell.appendChild(but_request_but);
                status_codeCell.appendChild(status_code_span);
                response_bodyCell.innerHTML = response_str;
                but_responseCell.appendChild(but_response_but);
                duration_msCell.innerHTML = log.duration
                // 根据状态码自动换颜色
                let badgeClass = 'badge ';
                if (log.status >= 200 && log.status < 300) {
                    badgeClass += 'badge-success';  // 绿色
                } else if (log.status >= 300 && log.status < 400) {
                    badgeClass += 'badge-info';     // 蓝色
                } else if (log.status >= 400 && log.status < 500) {
                    badgeClass += 'badge-warning';  // 黄色
                } else if (log.status >= 500) {
                    badgeClass += 'badge-danger';   // 红色
                }

                let levelClass = 'badge ';
                if (log.level ==="INFO") {
                    levelClass += 'badge-primary';
                } else if (log.level ==="DEBUG") {
                    levelClass += 'badge-secondary';
                } else if (log.level ==="WARNING") {
                    levelClass += 'badge-warning';
                } else if (log.level ==="ERROR") {
                    levelClass += 'badge-danger';
                }else if (log.level ==="CRITICAL") {
                    levelClass += 'badge-dark';
                }
                // 添加样式
                datetimeCell.className = "time-col";
                level_span.className = levelClass;
                pathCell.className = "font-monospace";
                request_bodyCell.className = "req-body";
                status_code_span.className = badgeClass;
                response_bodyCell.className = "req-body";
                duration_msCell.className = "ms-col";
                // 报文title
                request_bodyCell.title = JSON.stringify(log.request);
                response_bodyCell.title = JSON.stringify(log.response);
            });
        }
        else {
            table.innerHTML = '';
        }
}

//统计数据
function calculateStats(data){
    if (data.code === 200) {
        const logs = data.message;
        if (!logs || logs.length === 0) {
                return { total: 0, success: 0, fail: 0, avgTime: 0, successRate: 0, failRate: 0 };
            }

        const total = logs.length;

        // 使用 filter 统计成功和失败
        // 定义成功：状态码 2xx
        const successLogs = logs.filter(log => log.status >= 200 && log.status < 300);
        const success = successLogs.length;

        // 定义失败：状态码 4xx 或 5xx
        const failLogs = logs.filter(log => log.status >= 400);
        const fail = failLogs.length;

        // 使用 reduce 计算总耗时，然后求平均
        const totalDuration = logs.reduce((sum, log) => sum + (log.duration || 0), 0);
        const avgTime = total > 0 ? (totalDuration / total).toFixed(1) : 0;

        // 计算比率
        const successRate = ((success / total) * 100).toFixed(1);
        const failRate = ((fail / total) * 100).toFixed(1);

        return {
                total,
                success,
                fail,
                avgTime,
                successRate,
                failRate
            };

    }else{
        return { total: 0, success: 0, fail: 0, avgTime: 0, successRate: 0, failRate: 0 };
    }
}

function updateUI(stats) {
    // 获取 DOM 元素
    const elTotal = document.getElementById('stat-total');
    const elSuccess = document.getElementById('stat-success');
    const elFail = document.getElementById('stat-fail');
    const elAvgTime = document.getElementById('stat-avgTime');
    const elSuccessRate = document.getElementById('success-rate');
    const elFailRate = document.getElementById('fail-rate');
    // 添加简单的数字滚动动画效果 (可选)
    animateValue(elTotal, parseInt(elTotal.innerText), stats.total, 500);
    animateValue(elSuccess, parseInt(elSuccess.innerText), stats.success, 500);
    animateValue(elFail, parseInt(elFail.innerText), stats.fail, 500);

    // 平均耗时保留一位小数
    elAvgTime.innerText = stats.avgTime;
    // 更新比率文本
    elSuccessRate.innerText = `成功率: ${stats.successRate}%`;
    elFailRate.innerText = `失败率: ${stats.failRate}%`;
}

// --- 4. 辅助工具：数字动画 ---
function animateValue(obj, start, end, duration) {
    if (start === end) return;
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        obj.innerHTML = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
                window.requestAnimationFrame(step);
}

function add_json_message(message){
    const jsonContent= document.getElementById('jsonContent');
    if (jsonContent){
        const jsonbox = JSON.stringify(message, null, 2);
        //jsonContent.innerText = jsonbox
        $('#jsonContent').text(jsonbox);
    }
}
