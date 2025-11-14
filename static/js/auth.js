class TokenAuthManager {
    constructor() {
        //this.baseURL = 'http://localhost:8000';
        this.tokenKey = 'access_token';
        this.refreshTokenKey = 'refresh_token';

        this.init();
    }

    init() {
        this.bindEvents();
        this.checkExistingToken();
    }

    bindEvents() {
        document.getElementById('loginForm').addEventListener('submit', (e) => this.handleLogin(e));
    }

    // 处理登录表单提交
    async handleLogin(event) {
        event.preventDefault();

        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;

        try {
            // 显示加载状态
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>获取中...</i>';

            const formData = this.collectFormData();
            const response = await this.fetchToken(formData);

            this.handleSuccess(response);
            this.showMessage('Token获取成功！', 'success');

        } catch (error) {
            console.error('Token获取失败:', error);
            this.showMessage(`获取失败: ${error.message}`, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        }
    }

    // 收集表单数据
    collectFormData() {
        const formData = new URLSearchParams();

        // 必需字段
        formData.append('grant_type', 'password');
        formData.append('username', document.getElementById('username').value.trim());
        formData.append('password', document.getElementById('password').value);

        // 可选字段
        const scope = document.getElementById('scope').value;
        const clientId = document.getElementById('client_id').value;
        const clientSecret = document.getElementById('client_secret').value;

        if (scope) formData.append('scope', scope);
        if (clientId) formData.append('client_id', clientId);
        if (clientSecret) formData.append('client_secret', clientSecret);

        return formData;
    }

    // 获取Token
    async fetchToken(formData) {
        const response = await fetch(`/token`, {
            method: 'POST',
            headers: {
                'accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP错误: ${response.status}`);
        }

        return await response.json();
    }

    // 处理成功响应
    handleSuccess(data) {
        // 存储token
        this.setToken(data.access_token);
        if (data.refresh_token) {
            this.setRefreshToken(data.refresh_token);
        }

        // 显示结果
        this.showResult(data);
    }

    // 存储访问令牌
    setToken(token) {
        localStorage.setItem(this.tokenKey, token);
    }

    // 存储刷新令牌
    setRefreshToken(refreshToken) {
        localStorage.setItem(this.refreshTokenKey, refreshToken);
    }

    // 获取访问令牌
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }

    // 获取刷新令牌
    getRefreshToken() {
        return localStorage.getItem(this.refreshTokenKey);
    }

    // 显示结果
    showResult(data) {
        const resultSection = document.getElementById('resultSection');
        const accessTokenElement = document.getElementById('accessToken');
        const refreshTokenElement = document.getElementById('refreshToken');
        const tokenTypeElement = document.getElementById('tokenType');
        const expiresInElement = document.getElementById('expiresIn');

        // 更新显示内容
        accessTokenElement.textContent = data.access_token || '无';
        refreshTokenElement.textContent = data.refresh_token || '无';
        tokenTypeElement.textContent = data.token_type || 'Bearer';
        expiresInElement.textContent = data.expires_in ? `${data.expires_in}秒` : '未知';

        resultSection.classList.remove('hidden');
    }

    // 检查现有token
    checkExistingToken() {
        const token = this.getToken();
        if (token) {
            this.showResult({
                access_token: token,
                refresh_token: this.getRefreshToken(),
                token_type: 'Bearer',
                expires_in: 3600
        });
    }}

    // 显示消息提示
    showMessage(message, type='info') {
        // 移除之前的消息
        const existingMessage = document.querySelector('.message-alert');
        if (existingMessage) {
            existingMessage.remove();
        }

        const colors = {
            success: 'green',
            error: 'red',
            warning: 'yellow',
            info: 'blue'
        };

        const color = colors[type] || 'blue';

        const messageHtml = `
            <div class="message-alert bg-${color}-100 border border-${color}-400 text-${color}-700 px-4 py-3 rounded-lg mb-4 border-l-4 border-l-${color}-500 animate-fade-in">
                <div class="flex items-center">
                    <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} mr-2"></i>
                    <span>${message}</span>
                </div>
            </div>
        `;

        document.querySelector('form').insertAdjacentHTML('beforebegin', messageHtml);

        // 3秒后自动移除
        setTimeout(() => {
            const alert = document.querySelector('.message-alert');
            if (alert) {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.3s ease-in-out';
                setTimeout(() => alert.remove(), 300);
            }
        }, 3000);
    }

    // 刷新token（可选功能）
    async refreshAccessToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            throw new Error('没有可用的刷新令牌');
        }

        const formData = new URLSearchParams();
        formData.append('grant_type', 'refresh_token');
        formData.append('refresh_token', refreshToken);

        const response = await this.fetchToken(formData);
        this.handleSuccess(response);

        return response.access_token;
    }

    // 带认证的API请求
    async authenticatedFetch(url, options = {}) {
        const token = this.getToken();
        if (!token) {
            throw new Error('用户未认证');
        }

        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };

        return await fetch(url, mergedOptions);
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    window.tokenAuth = new TokenAuthManager();

    // 添加自定义动画样式
    const style = document.createElement('style');
    style.textContent = `
        .animate-fade-in {
            animation: fadeIn 0.3s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
});