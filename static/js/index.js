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
    //判断iframe标签是否存在，决定是否加载页面内容
    if (element) {
        document.getElementById('docsFrame').src = "/docs";
    } else {
        console.log('元素不存在');
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



async function seach_logs(){
     const params = new URLSearchParams({
            str_date: document.getElementById('str_date').value,
            end_date: document.getElementById('end_date').value,
            level: document.getElementById('level').value,
            keyword: document.getElementById('keyword').value
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
        console.log(data);
        if (data.code === 200) {
            const logs = data.logs;
            const table = document.getElementById('logs-table');
            table.innerHTML = '';
            logs.forEach(log => {
                const row = table.insertRow();
                const datetimeCell = row.insertCell();
                const levelCell = row.insertCell();
                const messageCell = row.insertCell();
                datetimeCell.innerHTML = log.datetime;
                levelCell.innerHTML = log.level;
                messageCell.innerHTML = log.message;
            });
        }
        else {
            console.error('Search logs error:', data.message);
        }
    }
    catch (error) {
        console.error('Search logs error:', error);
    }
}

