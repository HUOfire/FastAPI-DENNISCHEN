let targetDate = undefined

// 页面加载时检查是否已登录
window.addEventListener('load', async () => {

    try {
        const response = await fetch('/api/verify', {
            credentials: 'include'
        });

        if (response.ok) {
            // 已登录，显示提示
            const data = await response.json();
            //data.datetime = undefined;
            console.log('登时效验证成功:', data.user);
            const messageDiv = document.getElementById('message');
            messageDiv.className = 'display-4 text-center';
            messageDiv.textContent = `${data.user.username}欢迎回来！`;
            messageDiv.style.display = 'block';
            console.log(data.user.expire_datetime)
            targetDate = new Date(data.user.expire_datetime);
            console.log(targetDate)
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
    // 获取所有需要鉴权的导航链接
    const links = document.querySelectorAll('#navbarNav .nav-link');
    console.log('test_01');
    links.forEach(link => {
        console.log('test_02');
        link.addEventListener('click', function(e) {
            e.preventDefault(); // 1. 阻止默认跳转
            console.log('test_03');
            const targetUrl = this.getAttribute('data-target') || this.getAttribute('href');
            console.log('test_04');
            // 2. 验证 Cookie 是否有效
            if (isCookieValid()) {
                // 有效：手动跳转
                console.log('有效即将跳转');
                setTimeout(() => {
                            window.location.href = targetUrl;
                }, 1000);

            } else {
                // 无效：显示弹窗
                console.log('无效即将弹窗');
                setTimeout(() => {
                            showExpirationModal(targetUrl);
                }, 1000);

            }
        });
    });

    function updateTimer() {
         const now = new Date();
         const diff = targetDate - now; // 毫秒差值
         console.log(targetDate,diff)

        const card = document.getElementById('timer');
         if (!card) {
            console.warn("Element with id 'timer' not found.");
            return;
        }
         // 2. 判断是否结束
         if (diff <= 0) {
                 document.getElementById("timer").innerText = "已结束";
                 return;
         }

         // 3. 计算天、时、分、秒
         const days = Math.floor(diff / (1000 * 60 * 60 * 24));
         const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
         const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
         const seconds = Math.floor((diff % (1000 * 60)) / 1000);

         let str_date = String(hours) + 'H:' + String(minutes) + 'M:' + String(seconds) + 'S'
         // 4. 格式化输出 (补零)

         card.className = 'display-4 text-center';
         card.innerText = `登录有效时间剩余：${str_date}`;
         card.style.display = 'block';
         //document.getElementById("timer").innerText = `登录有效时间剩余：${str_date}`;
    }

    // 5. 启动定时器 (每秒刷新)
    setInterval(updateTimer, 1000);
    updateTimer(); // 立即执行一次，避免页面加载时的1秒空白
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

