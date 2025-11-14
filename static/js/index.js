// 页面加载时检查是否已登录
window.addEventListener('load', async () => {
    try {
            const response = await fetch('/api/verify', {
                credentials: 'include'
            });

            if (response.ok) {
                    // 已登录，显示提示
                    const data = await response.json();
                    console.log('登时效验证成功:', data);
                    const messageDiv = document.getElementById('message');
                    messageDiv.className = 'display-4 text-center';
                    messageDiv.textContent = `${data.user.username}欢迎回来！`;
                    messageDiv.style.display = 'block';
            }
        }
        catch (error) {
            // 未登录或 token 无效，忽略错误
            console.error('登时效验证错误:', error);
            window.window.location.href="/login";
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
