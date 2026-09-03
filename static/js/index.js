let targetDate = undefined
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
            /*
            const messageDiv = document.getElementById('message');
            messageDiv.className = 'display-4 text-center';
            messageDiv.textContent = `${data.user.username}欢迎回来！`;
            messageDiv.style.display = 'block';
             */
            targetDate = new Date(data.user.expire_datetime);
        }
    } catch (error) {
        // 未登录或 token 无效，忽略错误
        console.error('登时效验证错误:', error);
        window.window.location.href = "/login";
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



document.addEventListener('DOMContentLoaded', function() {
    function updateTimer() {
         const now = new Date();
         diff = targetDate - now; // 毫秒差值
    }

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
                //console.log('有效即将跳转');
                setTimeout(() => {
                            window.location.href = targetUrl;
                }, 1000);

            } else {
                // 无效：显示弹窗
                //console.log('无效即将弹窗');
                setTimeout(() => {
                            showExpirationModal(targetUrl);
                }, 1000);

            }
        });
    });
});

// 模拟 Cookie 验证函数
function isCookieValid() {
    // 方法 A: 如果 Cookie 非 HttpOnly，直接读取判断
    /*
    const token = getCookie('auth_token');
    if (!token) return false;

    // 如果有存储过期时间，也可以在此比对时间戳
    // const expiry = getCookie('auth_token_expiry');
    // if (expiry && new Date().getTime() > parseInt(expiry)) return false;

    return true;
    */
    // 方法 B: 如果 Cookie 是 HttpOnly，需发送 AJAX 请求验证
    console.log('test_api');

    return fetch('/api/verify', { method: 'GET', credentials: 'include' })
        .then(res => res.ok)
        .catch(() => false);

}

// 辅助函数：获取 Cookie
/*
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
*/
// 显示弹窗逻辑
function showExpirationModal(redirectAfterLogin) {
    // 这里可以使用你项目中的 UI 库弹窗，或者原生 confirm
    // 注意：原生 confirm 会阻塞线程，体验较好但样式不可控
    const userConfirmed = confirm("登录已过期，请重新登录");
    console.log('登录已过期，请重新登录');

    if (userConfirmed) {
        // 点击确定后跳转登录页
        // 可以将原目标地址作为参数传给登录页，登录后再跳回来
        window.location.href = `/login`;
    }
}

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

