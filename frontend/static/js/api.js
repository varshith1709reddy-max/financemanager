/**
 * Personal Finance Manager - API Client
 */
const API = {
    token: localStorage.getItem('finance_token') || null,

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('finance_token', token);
        } else {
            localStorage.removeItem('finance_token');
        }
    },

    async request(endpoint, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const config = {
            ...options,
            headers
        };

        try {
            const response = await fetch(endpoint, config);

            // If CSV export or blob
            if (options.isBlob) {
                if (!response.ok) throw new Error('Export failed');
                return await response.blob();
            }

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                if (response.status === 401) {
                    this.setToken(null);
                    window.dispatchEvent(new CustomEvent('auth:expired'));
                }
                const error = new Error(data.error || 'Something went wrong');
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        } catch (err) {
            console.error(`API Error [${endpoint}]:`, err);
            throw err;
        }
    },

    // Auth
    async login(identifier, password) {
        const res = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username: identifier, password })
        });
        if (res.token) this.setToken(res.token);
        return res;
    },

    async register(userData) {
        const res = await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        if (res.token) this.setToken(res.token);
        return res;
    },

    async demoLogin() {
        const res = await this.request('/api/demo/seed', { method: 'POST' });
        if (res.token) this.setToken(res.token);
        return res;
    },

    async logout() {
        try {
            await this.request('/api/auth/logout', { method: 'POST' });
        } finally {
            this.setToken(null);
        }
    },

    async getMe() {
        return await this.request('/api/auth/me');
    },

    async updateProfile(profileData) {
        return await this.request('/api/auth/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    },

    // Dashboard
    async getDashboard() {
        return await this.request('/api/dashboard/summary');
    },

    // Accounts
    async getAccounts() {
        return await this.request('/api/accounts');
    },

    async getAccount(id) {
        return await this.request(`/api/accounts/${id}`);
    },

    async createAccount(data) {
        return await this.request('/api/accounts', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateAccount(id, data) {
        return await this.request(`/api/accounts/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteAccount(id) {
        return await this.request(`/api/accounts/${id}`, { method: 'DELETE' });
    },

    // Transactions
    async getTransactions(params = {}) {
        const query = new URLSearchParams();
        Object.entries(params).forEach(([key, val]) => {
            if (val !== undefined && val !== null && val !== '') {
                query.append(key, val);
            }
        });
        return await this.request(`/api/transactions?${query.toString()}`);
    },

    async createTransaction(data) {
        return await this.request('/api/transactions', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async createTransfer(data) {
        return await this.request('/api/transactions/transfer', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateTransaction(id, data) {
        return await this.request(`/api/transactions/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async deleteTransaction(id) {
        return await this.request(`/api/transactions/${id}`, { method: 'DELETE' });
    },

    // Categories
    async getCategories(type) {
        const url = type ? `/api/categories?type=${type}` : '/api/categories';
        return await this.request(url);
    },

    async createCategory(data) {
        return await this.request('/api/categories', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // Budgets
    async getBudgets(month) {
        const url = month ? `/api/budgets?month=${month}` : '/api/budgets';
        return await this.request(url);
    },

    async saveBudget(data) {
        return await this.request('/api/budgets', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async deleteBudget(id) {
        return await this.request(`/api/budgets/${id}`, { method: 'DELETE' });
    },

    // Savings Goals
    async getGoals() {
        return await this.request('/api/goals');
    },

    async createGoal(data) {
        return await this.request('/api/goals', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async updateGoal(id, data) {
        return await this.request(`/api/goals/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    async contributeGoal(id, data) {
        return await this.request(`/api/goals/${id}/contribute`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async deleteGoal(id) {
        return await this.request(`/api/goals/${id}`, { method: 'DELETE' });
    },

    // Reports
    async getCashFlowReport(startDate, endDate) {
        const q = new URLSearchParams();
        if (startDate) q.append('start_date', startDate);
        if (endDate) q.append('end_date', endDate);
        return await this.request(`/api/reports/cash-flow?${q.toString()}`);
    },

    async getSpendingReport(startDate, endDate) {
        const q = new URLSearchParams();
        if (startDate) q.append('start_date', startDate);
        if (endDate) q.append('end_date', endDate);
        return await this.request(`/api/reports/spending?${q.toString()}`);
    },

    async getIncomeReport(startDate, endDate) {
        const q = new URLSearchParams();
        if (startDate) q.append('start_date', startDate);
        if (endDate) q.append('end_date', endDate);
        return await this.request(`/api/reports/income?${q.toString()}`);
    },

    async exportCSV(startDate, endDate) {
        const q = new URLSearchParams();
        if (startDate) q.append('start_date', startDate);
        if (endDate) q.append('end_date', endDate);
        return await this.request(`/api/reports/export?${q.toString()}`, { isBlob: true });
    }
};
