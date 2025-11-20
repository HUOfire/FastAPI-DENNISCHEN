// FastAPI 日志管理前端交互逻辑

class LogManagerApp {
    constructor() {
        this.currentLogs = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    setupEventListeners() {
        // 监听过滤器变化
        document.getElementById('level-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('module-filter').addEventListener('change', () => this.applyFilters());
        document.getElementById('keyword-search').addEventListener('input',
            debounce(() => this.applyFilters(), 300)
        );
    }

    async loadInitialData() {
        await this.refreshLogs();
    }

    async refreshLogs() {
        try {
            const params = this.getFilterParams();
            const response = await fetch(`/logs?${params.toString()}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.currentLogs = data.logs;
            this.updateLogsDisplay();
            this.updateStatistics();

        } catch (error) {
            console.error('获取日志失败:', error);
            this.showNotification('获取日志失败，请检查网络连接', 'error');
        }
    }

    getFilterParams() {
        const params = new URLSearchParams();

        const level = document.getElementById('level-filter').value;
        const module = document.getElementById('module-filter').value;
        const keyword = document.getElementById('keyword-search').value;
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;

        if (level) params.append('level', level);
        if (module) params.append('module', module);
        if (keyword) params.append('keyword', keyword);
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        return params;
    }

    updateLogsDisplay() {
        const container = document.getElementById('logs-container');

        if (this.currentLogs.length === 0) {
            container.innerHTML = `
                <tr>
                    <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                    <i class="fas fa-inbox text-4xl mb-2"></i>
                    <p>暂无日志数据</p>
                </td>
            </tr>`;
            return;
        }

        container.innerHTML = this.currentLogs.map(log => this.createLogRow(log)).join('');
    }

    createLogRow(log) {
        const logDate = new Date(log.timestamp);
        const formattedTime = logDate.toLocaleString('zh-CN');

        return `
            <tr class="fade-in hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${formattedTime}</td>
                <td class="px-6 py-4 whitespace-nowrap">
                <span class="log-level-${log.level.toLowerCase()}">${log.level}</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${log.module}</td>
                <td class="px-6 py-4 text-sm text-gray-900">${log.message}</td>
            </tr>
        `;
    }

    updateStatistics() {
        document.getElementById('total-logs').textContent = this.currentLogs.length;
    }

    showNotification(message, type = 'info') {
        // 实现通知显示逻辑
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-md text-white ${
            type === 'error' ? 'bg-red-500' : 
            type === 'success' ? 'bg-green-500' : 'bg-blue-500'};`
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    applyFilters() {
        this.refreshLogs();
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new LogManagerApp();
});