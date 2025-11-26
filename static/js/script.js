document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageDiv = document.getElementById('message');

    try {
            // 显示加载状态
            messageDiv.style.display = 'block';
            messageDiv.className = 'message success';
            messageDiv.textContent = '登录中...';

            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                            'Content-Type': 'application/json',
                        },
                body: JSON.stringify({ username, password }),
                credentials: 'include'  // 重要：包含 cookies
            });

            if (response.ok) {
                const data = await response.json();

                messageDiv.className = 'message success';
                messageDiv.textContent = `登录成功！欢迎 ${data.user.username}，跳转中...`;

                // 登录成功，跳转到文档页面
                setTimeout(() => {
                    window.location.href = '/index';
                }, 1000);

            }
            else {
                    const errorData = await response.json();
                    messageDiv.className = 'message error';
                    messageDiv.textContent = `登录失败: ${errorData.detail}`;
            }
        }
        catch (error) {
            console.error('Login error:', error);
            messageDiv.className = 'message error';
            messageDiv.textContent = '网络错误，请检查连接后重试';
        }
});

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
                    messageDiv.style.display = 'block';
                    messageDiv.className = 'message success';
                    messageDiv.innerHTML = `已登录为 ${data.user.username}，<a href="/index">进入主页</a> | <a href="javascript:void(0)" onclick="logout()">退出登录</a>`;
            }
        }
        catch (error) {
            // 未登录或 token 无效，忽略错误
            console.error('登时效验证错误:', error);
        }
});

// 退出登录函数
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