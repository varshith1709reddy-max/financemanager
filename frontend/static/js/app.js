/**
 * Personal Finance Manager - Main Application Controller
 */

const App = {
    user: null,
    accounts: [],
    categories: [],
    activeView: 'dashboard',
    selectedAccountId: null,

    icons: {
        edit: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>',
        delete: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>',
        alert: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
        check: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>'
    },

    txnFilters: {
        page: 1,
        limit: 15,
        type: '',
        account_id: '',
        category_id: '',
        search: '',
        start_date: '',
        end_date: ''
    },

    async init() {
        // Set default dates
        const today = new Date().toISOString().split('T')[0];
        const currentMonth = today.substring(0, 7);

        const dateInputs = ['txn-date', 'transfer-date', 'contribute-date'];
        dateInputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = today;
        });

        const budgetMonthEl = document.getElementById('budget-month-selector');
        if (budgetMonthEl) budgetMonthEl.value = currentMonth;
        const budgetFormMonthEl = document.getElementById('budget-form-month');
        if (budgetFormMonthEl) budgetFormMonthEl.value = currentMonth;

        const reportStartEl = document.getElementById('report-start-date');
        const reportEndEl = document.getElementById('report-end-date');
        if (reportStartEl && reportEndEl) {
            reportStartEl.value = today.substring(0, 4) + '-01-01';
            reportEndEl.value = today;
        }

        window.addEventListener('auth:expired', () => {
            this.showToast('Session expired. Please sign in again.', 'error');
            this.showAuth();
        });

        // Check active session
        try {
            const res = await API.getMe();
            if (res.user) {
                this.user = res.user;
                this.showApp();
                return;
            }
        } catch {
            // Not authenticated
        }

        this.showAuth();
    },

    // UI Toast Notification
    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const iconSvg = type === 'success' 
            ? '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>'
            : type === 'error'
            ? '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>'
            : '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
        toast.innerHTML = `<span style="display: flex; align-items: center; margin-right: 6px;">${iconSvg}</span> <span>${message}</span>`;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            toast.style.transition = 'all 0.2s ease';
            setTimeout(() => toast.remove(), 200);
        }, 3500);
    },

    formatCurrency(val) {
        const currency = this.user?.currency || 'INR';
        const symbol = currency === 'INR' ? '₹' : currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : '$';
        const num = parseFloat(val) || 0;
        return `${symbol}${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },

    // Auth flows
    switchAuthTab(tab) {
        const tabLogin = document.getElementById('tab-login');
        const tabReg = document.getElementById('tab-register');
        const formLogin = document.getElementById('form-login');
        const formReg = document.getElementById('form-register');

        if (tab === 'login') {
            tabLogin.classList.add('active');
            tabReg.classList.remove('active');
            formLogin.style.display = 'block';
            formReg.style.display = 'none';
        } else {
            tabReg.classList.add('active');
            tabLogin.classList.remove('active');
            formReg.style.display = 'block';
            formLogin.style.display = 'none';
        }
    },

    async handleLogin(e) {
        e.preventDefault();
        const identifier = document.getElementById('login-identifier').value.trim();
        const password = document.getElementById('login-password').value;

        try {
            const res = await API.login(identifier, password);
            this.user = res.user;
            this.showToast('Welcome back, ' + this.user.full_name + '!');
            this.showApp();
        } catch (err) {
            this.showToast(err.message || 'Login failed', 'error');
        }
    },

    async handleRegister(e) {
        e.preventDefault();
        const fullName = document.getElementById('reg-fullname').value.trim();
        const username = document.getElementById('reg-username').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const password = document.getElementById('reg-password').value;
        const currency = document.getElementById('reg-currency').value;

        try {
            const res = await API.register({
                full_name: fullName,
                username,
                email,
                password,
                currency
            });
            this.user = res.user;
            this.showToast('Account created successfully!');
            this.showApp();
        } catch (err) {
            this.showToast(err.message || 'Registration failed', 'error');
        }
    },

    async handleDemoLogin() {
        try {
            const res = await API.demoLogin();
            this.user = res.user;
            this.showToast('Demo environment loaded!');
            this.showApp();
        } catch (err) {
            this.showToast(err.message || 'Demo initialization failed', 'error');
        }
    },

    async handleLogout() {
        await API.logout();
        this.user = null;
        this.showToast('Logged out');
        this.showAuth();
    },

    showAuth() {
        document.getElementById('auth-screen').style.display = 'flex';
        document.getElementById('app-screen').style.display = 'none';
    },

    async showApp() {
        document.getElementById('auth-screen').style.display = 'none';
        document.getElementById('app-screen').style.display = 'flex';

        // Update User Profile Bar
        document.getElementById('user-display-name').textContent = this.user.full_name || this.user.username;
        document.getElementById('user-display-email').textContent = this.user.email;
        const initials = (this.user.full_name || this.user.username).split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
        document.getElementById('user-avatar').textContent = initials;

        // Load common categories and accounts
        await Promise.all([this.loadCategories(), this.loadAccountsList()]);

        // Navigate to active view
        this.navigateTo(this.activeView);
    },

    async loadCategories() {
        try {
            const res = await API.getCategories();
            this.categories = res.categories || [];
            this.populateCategorySelects();
        } catch (err) {
            console.error('Failed to load categories', err);
        }
    },

    populateCategorySelects() {
        const txnCat = document.getElementById('txn-category-id');
        const filterCat = document.getElementById('txn-filter-category');
        const budgetCat = document.getElementById('budget-category-id');

        const txnType = document.querySelector('input[name="txn-type"]:checked')?.value || 'expense';
        const filtered = this.categories.filter(c => c.type === txnType);

        if (txnCat) {
            txnCat.innerHTML = filtered.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }

        if (budgetCat) {
            const expenseCats = this.categories.filter(c => c.type === 'expense');
            budgetCat.innerHTML = expenseCats.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
        }

        if (filterCat) {
            filterCat.innerHTML = '<option value="">All Categories</option>' + 
                this.categories.map(c => `<option value="${c.id}">${c.name} (${c.type})</option>`).join('');
        }
    },

    async loadAccountsList() {
        try {
            const res = await API.getAccounts();
            this.accounts = res.accounts || [];
            this.populateAccountSelects();
        } catch (err) {
            console.error('Failed to load accounts', err);
        }
    },

    populateAccountSelects() {
        const srcAcc = document.getElementById('txn-account-id');
        const dstAcc = document.getElementById('txn-to-account-id');
        const transferFrom = document.getElementById('transfer-from-id');
        const transferTo = document.getElementById('transfer-to-id');
        const filterAcc = document.getElementById('txn-filter-account');
        const goalAcc = document.getElementById('contribute-account-id');

        const optionsHtml = this.accounts.map(a => 
            `<option value="${a.id}">${a.name} (${this.formatCurrency(a.balance)})</option>`
        ).join('');

        if (srcAcc) srcAcc.innerHTML = optionsHtml;
        if (dstAcc) dstAcc.innerHTML = optionsHtml;
        if (transferFrom) transferFrom.innerHTML = optionsHtml;
        if (transferTo) transferTo.innerHTML = optionsHtml;
        if (filterAcc) {
            filterAcc.innerHTML = '<option value="">All Accounts</option>' + 
                this.accounts.map(a => `<option value="${a.id}">${a.name}</option>`).join('');
        }
        if (goalAcc) {
            goalAcc.innerHTML = '<option value="">Do not deduct from account balance</option>' + optionsHtml;
        }
    },

    // Navigation
    navigateTo(viewName) {
        this.activeView = viewName;
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.getAttribute('data-view') === viewName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        document.querySelectorAll('.app-view').forEach(view => {
            view.style.display = 'none';
        });

        const activeSection = document.getElementById(`view-${viewName}`);
        if (activeSection) activeSection.style.display = 'block';

        if (viewName === 'dashboard') this.loadDashboard();
        else if (viewName === 'transactions') this.loadTransactions();
        else if (viewName === 'budgets-goals') {
            this.loadBudgets();
            this.loadGoals();
        }
        else if (viewName === 'reports') this.loadReports();
    },

    // ================= 1. DASHBOARD =================
    async loadDashboard() {
        try {
            const data = await API.getDashboard();
            const metrics = data.metrics || {};

            // Format Month Header
            const dateObj = new Date();
            const monthName = dateObj.toLocaleString('default', { month: 'long', year: 'numeric' });
            document.getElementById('dash-month-label').textContent = monthName;

            // KPIs
            document.getElementById('kpi-net-worth').textContent = this.formatCurrency(metrics.net_worth);
            document.getElementById('kpi-income').textContent = this.formatCurrency(metrics.this_month_income);
            document.getElementById('kpi-expense').textContent = this.formatCurrency(metrics.this_month_expense);
            document.getElementById('kpi-savings-rate').textContent = `${metrics.savings_rate}%`;
            document.getElementById('kpi-net-savings-sub').textContent = `Net savings: ${this.formatCurrency(metrics.this_month_net)}`;

            // Accounts Pills on Dashboard
            const accPillsContainer = document.getElementById('dash-accounts-pills');
            const accounts = data.accounts || [];
            if (accPillsContainer) {
                if (accounts.length === 0) {
                    accPillsContainer.innerHTML = `<span style="font-size: 13px; color: var(--text-muted);">No accounts found. Click "+ Add Wallet/Account"</span>`;
                } else {
                    accPillsContainer.innerHTML = accounts.map(a => `
                        <div style="background: var(--bg-main); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 8px 14px; display: flex; align-items: center; gap: 10px;">
                            <div>
                                <div style="font-size: 11px; color: var(--text-muted); text-transform: uppercase; font-weight: 600;">${a.type}</div>
                                <div style="font-size: 14px; font-weight: 700;">${a.name}</div>
                            </div>
                            <div style="font-size: 15px; font-weight: 700; color: var(--primary); margin-left: 8px;">
                                ${this.formatCurrency(a.balance)}
                            </div>
                        </div>
                    `).join('');
                }
            }

            // MoM Indicators
            const incBadge = document.getElementById('kpi-income-badge');
            if (metrics.income_change_pct !== null) {
                incBadge.textContent = `${metrics.income_change_pct >= 0 ? '+' : ''}${metrics.income_change_pct}% MoM`;
                incBadge.className = `kpi-badge ${metrics.income_change_pct >= 0 ? 'positive' : 'neutral'}`;
            }

            const expBadge = document.getElementById('kpi-expense-badge');
            if (metrics.expense_change_pct !== null) {
                expBadge.textContent = `${metrics.expense_change_pct >= 0 ? '+' : ''}${metrics.expense_change_pct}% MoM`;
                expBadge.className = `kpi-badge ${metrics.expense_change_pct > 0 ? 'negative' : 'positive'}`;
            }

            // Budget Alerts
            const alertsContainer = document.getElementById('dashboard-alerts-container');
            const alerts = data.budget_alerts || [];
            if (alerts.length > 0) {
                alertsContainer.style.display = 'block';
                alertsContainer.innerHTML = alerts.map(a => `
                    <div style="background: ${a.is_exceeded ? 'var(--danger-light)' : 'var(--warning-light)'}; 
                                color: ${a.is_exceeded ? '#B91C1C' : '#B45309'}; 
                                padding: 12px 18px; border-radius: var(--radius-md); font-size: 13px; font-weight: 500; display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <span style="display: flex; align-items: center; gap: 8px;">
                            ${this.icons.alert}
                            <span><strong>${a.category_name}</strong> budget alert: ${this.formatCurrency(a.spent_amount)} spent of ${this.formatCurrency(a.amount_limit)} limit (${a.percentage_spent}%)</span>
                        </span>
                        <button class="btn btn-secondary btn-sm" onclick="App.navigateTo('budgets')">Review Budgets</button>
                    </div>
                `).join('');
            } else {
                alertsContainer.style.display = 'none';
            }

            // Monthly Trends Chart
            const trends = data.monthly_trends || [];
            ChartEngine.renderDoubleBarChart(
                'chart-monthly-trends',
                trends.map(t => t.label),
                trends.map(t => t.income),
                trends.map(t => t.expense)
            );

            // Category Spending Donut Chart
            const categories = data.category_breakdown || [];
            ChartEngine.renderDonutChart('chart-category-donut', categories);

            // Category breakdown list
            const catListContainer = document.getElementById('dash-category-list');
            if (categories.length === 0) {
                catListContainer.innerHTML = `<p style="font-size: 12px; color: var(--text-muted); text-align: center;">No category spending recorded this month.</p>`;
            } else {
                catListContainer.innerHTML = categories.slice(0, 5).map(c => `
                    <div class="cat-item">
                        <div class="cat-info">
                            <span class="cat-dot" style="background: ${c.color || '#3B82F6'};"></span>
                            <span class="cat-name">${c.name}</span>
                        </div>
                        <div>
                            <span class="cat-amt">${this.formatCurrency(c.amount)}</span>
                            <span class="cat-pct">(${c.percentage}%)</span>
                        </div>
                    </div>
                `).join('');
            }

            // Recent Transactions Table
            const recentTxns = data.recent_transactions || [];
            const tbody = document.getElementById('dash-recent-txns');
            if (recentTxns.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No transactions recorded yet. Click "+ Add Transaction" to start!</td></tr>`;
            } else {
                tbody.innerHTML = recentTxns.map(t => `
                    <tr>
                        <td style="color: var(--text-muted); font-size: 12px;">${t.date}</td>
                        <td style="font-weight: 500;">${t.description}</td>
                        <td><span class="pill" style="background: ${t.category_color ? t.category_color + '22' : '#E5E7EB'}; color: ${t.category_color || '#374151'};">${t.category_name || (t.type === 'transfer' ? 'Transfer' : 'General')}</span></td>
                        <td style="color: var(--text-muted); font-size: 12px;">${t.account_name || 'Account'}</td>
                        <td style="text-align: right;" class="txn-amount ${t.type}">
                            ${t.type === 'income' ? '+' : t.type === 'expense' ? '-' : '⇄'} ${this.formatCurrency(t.amount)}
                        </td>
                    </tr>
                `).join('');
            }

            // Top Savings Goals
            const goalsListContainer = document.getElementById('dash-goals-list');
            const topGoals = data.top_goals || [];
            if (topGoals.length === 0) {
                goalsListContainer.innerHTML = `<p style="font-size: 12px; color: var(--text-muted); text-align: center;">No savings goals set. Click "+ New Savings Goal"!</p>`;
            } else {
                goalsListContainer.innerHTML = topGoals.map(g => `
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                            <span style="font-weight: 600;">${g.name} ${g.is_completed ? '<span class="pill" style="font-size: 10px; padding: 2px 6px; background: #D1FAE5; color: #047857;">Done</span>' : ''}</span>
                            <span style="color: var(--text-muted);">${this.formatCurrency(g.current_amount)} / ${this.formatCurrency(g.target_amount)}</span>
                        </div>
                        <div class="progress-container">
                            <div class="progress-bar ${g.percentage >= 100 ? 'success' : 'neutral'}" style="width: ${g.percentage}%; background: ${g.color || '#10B981'};"></div>
                        </div>
                        <div style="text-align: right; font-size: 11px; color: var(--text-muted);">${g.percentage}% achieved</div>
                    </div>
                `).join('');
            }
        } catch (err) {
            this.showToast('Failed to load dashboard: ' + err.message, 'error');
        }
    },

    // ================= 2. ACCOUNTS =================
    async loadAccounts() {
        try {
            await this.loadAccountsList();
            const grid = document.getElementById('accounts-cards-grid');

            if (this.accounts.length === 0) {
                grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                    <p style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">No accounts found</p>
                    <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">Create a checking, savings, or credit card account to track your money.</p>
                    <button class="btn btn-primary" onclick="App.openAccountModal()">+ Add Your First Account</button>
                </div>`;
                return;
            }

            grid.innerHTML = this.accounts.map(a => `
                <div class="account-card" style="cursor: pointer;" onclick="App.selectAccount(${a.id})">
                    <div class="account-card-header">
                        <div>
                            <span class="account-type-badge">${a.type.replace('_', ' ')}</span>
                            <h4 style="font-size: 16px; font-weight: 700; margin-top: 6px;">${a.name}</h4>
                            ${a.account_number ? `<span style="font-size: 11px; color: var(--text-subtle);">••• ${a.account_number}</span>` : ''}
                        </div>
                        <div style="display: flex; gap: 4px;" onclick="event.stopPropagation()">
                            <button class="btn-icon" title="Edit" onclick="App.openAccountModal(${JSON.stringify(a).replace(/"/g, '&quot;')})">${App.icons.edit}</button>
                            <button class="btn-icon" title="Delete" onclick="App.deleteAccount(${a.id})">${App.icons.delete}</button>
                        </div>
                    </div>
                    <div>
                        <div class="account-balance" style="color: ${a.type === 'credit_card' ? 'var(--danger)' : 'var(--text-main)'};">
                            ${this.formatCurrency(a.balance)}
                        </div>
                        <div style="font-size: 11px; color: var(--text-muted);">
                            Initial balance: ${this.formatCurrency(a.initial_balance)}
                        </div>
                    </div>
                    <div class="account-footer">
                        <span>${a.transaction_count || 0} transactions</span>
                        <span style="color: var(--primary); font-weight: 600; font-size: 11px;">View activity →</span>
                    </div>
                </div>
            `).join('');

            // Automatically select first account if none selected
            if (!this.selectedAccountId && this.accounts.length > 0) {
                this.selectAccount(this.accounts[0].id);
            }
        } catch (err) {
            this.showToast('Failed to load accounts', 'error');
        }
    },

    async selectAccount(accountId) {
        this.selectedAccountId = accountId;
        try {
            const res = await API.getAccount(accountId);
            const acc = res.account;
            const txns = res.recent_transactions || [];

            document.getElementById('account-detail-title').textContent = `${acc.name} Activity`;
            document.getElementById('account-detail-badge').textContent = `Balance: ${this.formatCurrency(acc.balance)}`;

            const tbody = document.getElementById('account-activity-tbody');
            if (txns.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No transactions recorded for this account.</td></tr>`;
                return;
            }

            tbody.innerHTML = txns.map(t => `
                <tr>
                    <td style="color: var(--text-muted); font-size: 12px;">${t.date}</td>
                    <td style="font-weight: 500;">${t.description}</td>
                    <td><span class="pill" style="background: var(--bg-main);">${t.type.toUpperCase()}</span></td>
                    <td><span class="pill" style="background: ${t.category_color ? t.category_color + '22' : '#E5E7EB'}; color: ${t.category_color || '#374151'};">${t.category_name || (t.type === 'transfer' ? 'Transfer' : 'General')}</span></td>
                    <td style="text-align: right;" class="txn-amount ${t.type}">
                        ${t.type === 'income' ? '+' : t.type === 'expense' ? '-' : '⇄'} ${this.formatCurrency(t.amount)}
                    </td>
                    <td style="text-align: right;">
                        <button class="btn-icon" title="Delete" onclick="App.deleteTransaction(${t.id})">${App.icons.delete}</button>
                    </td>
                </tr>
            `).join('');
        } catch (err) {
            console.error('Failed to load account activity', err);
        }
    },

    openAccountModal(acc = null) {
        const form = document.getElementById('form-account');
        form.reset();
        const editIdEl = document.getElementById('account-edit-id');
        const titleEl = document.getElementById('modal-acc-title');

        if (acc) {
            titleEl.textContent = 'Edit Account';
            editIdEl.value = acc.id;
            document.getElementById('acc-name').value = acc.name;
            document.getElementById('acc-type').value = acc.type;
            document.getElementById('acc-initial-balance').value = acc.initial_balance;
            document.getElementById('acc-currency').value = acc.currency;
            document.getElementById('acc-number').value = acc.account_number || '';
        } else {
            titleEl.textContent = 'Add Account';
            editIdEl.value = '';
            document.getElementById('acc-initial-balance').value = '0.00';
            document.getElementById('acc-currency').value = this.user?.currency || 'USD';
        }

        document.getElementById('modal-account').classList.add('open');
    },

    async handleSaveAccount(e) {
        e.preventDefault();
        const editId = document.getElementById('account-edit-id').value;
        const data = {
            name: document.getElementById('acc-name').value.trim(),
            type: document.getElementById('acc-type').value,
            initial_balance: parseFloat(document.getElementById('acc-initial-balance').value) || 0,
            currency: document.getElementById('acc-currency').value,
            account_number: document.getElementById('acc-number').value.trim()
        };

        try {
            if (editId) {
                await API.updateAccount(editId, data);
                this.showToast('Account updated');
            } else {
                await API.createAccount(data);
                this.showToast('Account created');
            }
            this.closeModals();
            await this.loadAccounts();
        } catch (err) {
            this.showToast(err.message || 'Error saving account', 'error');
        }
    },

    async deleteAccount(id) {
        if (!confirm('Are you sure you want to delete this account? Associated transactions will also be removed.')) return;
        try {
            await API.deleteAccount(id);
            this.showToast('Account deleted');
            if (this.selectedAccountId === id) this.selectedAccountId = null;
            await this.loadAccounts();
        } catch (err) {
            this.showToast(err.message || 'Error deleting account', 'error');
        }
    },

    // ================= 3. TRANSACTIONS =================
    async loadTransactions() {
        try {
            const res = await API.getTransactions(this.txnFilters);
            const txns = res.transactions || [];
            const tbody = document.getElementById('transactions-table-body');

            if (txns.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 32px; color: var(--text-muted);">No transactions match your filters.</td></tr>`;
            } else {
                tbody.innerHTML = txns.map(t => `
                    <tr>
                        <td style="color: var(--text-muted); font-size: 12px; white-space: nowrap;">${t.date}</td>
                        <td>
                            <div style="font-weight: 600;">${t.description}</div>
                            ${t.notes ? `<div style="font-size: 11px; color: var(--text-muted);">${t.notes}</div>` : ''}
                        </td>
                        <td><span class="pill" style="background: var(--bg-main); text-transform: uppercase; font-size: 10px;">${t.type}</span></td>
                        <td>
                            <span class="pill" style="background: ${t.category_color ? t.category_color + '22' : '#E5E7EB'}; color: ${t.category_color || '#374151'};">
                                ${t.category_name || (t.type === 'transfer' ? 'Account Transfer' : 'General')}
                            </span>
                        </td>
                        <td style="font-size: 12px;">
                            ${t.account_name || ''}
                            ${t.to_account_name ? ` → ${t.to_account_name}` : ''}
                        </td>
                        <td style="text-align: right;" class="txn-amount ${t.type}">
                            ${t.type === 'income' ? '+' : t.type === 'expense' ? '-' : '⇄'} ${this.formatCurrency(t.amount)}
                        </td>
                        <td style="text-align: right; white-space: nowrap;">
                            <button class="btn-icon" title="Edit" onclick="App.openTransactionModal(${JSON.stringify(t).replace(/"/g, '&quot;')})">${App.icons.edit}</button>
                            <button class="btn-icon" title="Delete" onclick="App.deleteTransaction(${t.id})">${App.icons.delete}</button>
                        </td>
                    </tr>
                `).join('');
            }

            // Pagination Controls
            const page = res.page || 1;
            const total = res.total || 0;
            const limit = res.limit || 15;
            const totalPages = res.total_pages || 1;

            const startIdx = total === 0 ? 0 : (page - 1) * limit + 1;
            const endIdx = Math.min(total, page * limit);
            document.getElementById('txn-page-info').textContent = `${startIdx}-${endIdx} of ${total}`;

            document.getElementById('btn-prev-page').disabled = (page <= 1);
            document.getElementById('btn-next-page').disabled = (page >= totalPages);

        } catch (err) {
            this.showToast('Failed to load transactions', 'error');
        }
    },

    applyTxnFilters() {
        this.txnFilters.search = document.getElementById('txn-filter-search').value.trim();
        this.txnFilters.type = document.getElementById('txn-filter-type').value;
        this.txnFilters.account_id = document.getElementById('txn-filter-account').value;
        this.txnFilters.category_id = document.getElementById('txn-filter-category').value;
        this.txnFilters.start_date = document.getElementById('txn-filter-start').value;
        this.txnFilters.end_date = document.getElementById('txn-filter-end').value;
        this.txnFilters.page = 1;
        this.loadTransactions();
    },

    resetTxnFilters() {
        document.getElementById('txn-filter-search').value = '';
        document.getElementById('txn-filter-type').value = '';
        document.getElementById('txn-filter-account').value = '';
        document.getElementById('txn-filter-category').value = '';
        document.getElementById('txn-filter-start').value = '';
        document.getElementById('txn-filter-end').value = '';
        this.txnFilters = { page: 1, limit: 15, type: '', account_id: '', category_id: '', search: '', start_date: '', end_date: '' };
        this.loadTransactions();
    },

    changeTxnPage(delta) {
        this.txnFilters.page += delta;
        this.loadTransactions();
    },

    openTransactionModal(txn = null) {
        const form = document.getElementById('form-transaction');
        form.reset();
        const editIdEl = document.getElementById('txn-edit-id');
        const titleEl = document.getElementById('modal-txn-title');

        this.populateAccountSelects();

        if (txn) {
            titleEl.textContent = 'Edit Transaction';
            editIdEl.value = txn.id;
            const radio = document.querySelector(`input[name="txn-type"][value="${txn.type}"]`);
            if (radio) radio.checked = true;
            this.handleTxnTypeChange();

            document.getElementById('txn-amount').value = txn.amount;
            document.getElementById('txn-date').value = txn.date;
            document.getElementById('txn-description').value = txn.description;
            document.getElementById('txn-account-id').value = txn.account_id;
            if (txn.to_account_id) document.getElementById('txn-to-account-id').value = txn.to_account_id;
            if (txn.category_id) document.getElementById('txn-category-id').value = txn.category_id;
            document.getElementById('txn-notes').value = txn.notes || '';
            document.getElementById('txn-tags').value = txn.tags || '';
        } else {
            titleEl.textContent = 'Add Transaction';
            editIdEl.value = '';
            document.querySelector('input[name="txn-type"][value="expense"]').checked = true;
            this.handleTxnTypeChange();
            document.getElementById('txn-date').value = new Date().toISOString().split('T')[0];
        }

        document.getElementById('modal-transaction').classList.add('open');
    },

    handleTxnTypeChange() {
        const type = document.querySelector('input[name="txn-type"]:checked').value;
        const toAccGroup = document.getElementById('txn-to-account-group');
        const catGroup = document.getElementById('txn-category-group');
        const accLabel = document.getElementById('txn-account-label');

        if (type === 'transfer') {
            toAccGroup.style.display = 'block';
            catGroup.style.display = 'none';
            accLabel.textContent = 'Source Account';
        } else {
            toAccGroup.style.display = 'none';
            catGroup.style.display = 'block';
            accLabel.textContent = 'Account';
            this.populateCategorySelects();
        }
    },

    async handleSaveTransaction(e) {
        e.preventDefault();
        const editId = document.getElementById('txn-edit-id').value;
        const type = document.querySelector('input[name="txn-type"]:checked').value;
        const data = {
            type,
            amount: parseFloat(document.getElementById('txn-amount').value),
            date: document.getElementById('txn-date').value,
            description: document.getElementById('txn-description').value.trim(),
            account_id: parseInt(document.getElementById('txn-account-id').value),
            category_id: type !== 'transfer' ? parseInt(document.getElementById('txn-category-id').value) || null : null,
            to_account_id: type === 'transfer' ? parseInt(document.getElementById('txn-to-account-id').value) : null,
            notes: document.getElementById('txn-notes').value.trim(),
            tags: document.getElementById('txn-tags').value.trim()
        };

        try {
            if (editId) {
                await API.updateTransaction(editId, data);
                this.showToast('Transaction updated');
            } else {
                await API.createTransaction(data);
                this.showToast('Transaction saved');
            }
            this.closeModals();
            await Promise.all([this.loadAccountsList(), this.loadTransactions()]);
        } catch (err) {
            this.showToast(err.message || 'Error saving transaction', 'error');
        }
    },

    async deleteTransaction(id) {
        if (!confirm('Are you sure you want to delete this transaction?')) return;
        try {
            await API.deleteTransaction(id);
            this.showToast('Transaction deleted');
            await Promise.all([this.loadAccountsList(), this.loadTransactions()]);
        } catch (err) {
            this.showToast(err.message || 'Error deleting transaction', 'error');
        }
    },

    // ================= TRANSFERS =================
    openTransferModal() {
        document.getElementById('form-transfer').reset();
        document.getElementById('transfer-date').value = new Date().toISOString().split('T')[0];
        document.getElementById('transfer-desc').value = 'Account Transfer';
        this.populateAccountSelects();
        document.getElementById('modal-transfer').classList.add('open');
    },

    async handleSaveTransfer(e) {
        e.preventDefault();
        const fromId = parseInt(document.getElementById('transfer-from-id').value);
        const toId = parseInt(document.getElementById('transfer-to-id').value);
        const amount = parseFloat(document.getElementById('transfer-amount').value);
        const date = document.getElementById('transfer-date').value;
        const desc = document.getElementById('transfer-desc').value.trim();
        const notes = document.getElementById('transfer-notes').value.trim();

        if (fromId === toId) {
            this.showToast('Source and destination accounts must be different', 'error');
            return;
        }

        try {
            await API.createTransfer({
                from_account_id: fromId,
                to_account_id: toId,
                amount,
                date,
                description: desc,
                notes
            });
            this.showToast('Funds transferred successfully!');
            this.closeModals();
            await Promise.all([this.loadAccountsList(), this.loadTransactions()]);
        } catch (err) {
            this.showToast(err.message || 'Transfer failed', 'error');
        }
    },

    // ================= 4. BUDGETS =================
    async loadBudgets() {
        const monthInput = document.getElementById('budget-month-selector')?.value || new Date().toISOString().substring(0, 7);
        try {
            const res = await API.getBudgets(monthInput);
            const budgets = res.budgets || [];
            const summary = res.summary || {};

            // Update Overall Summary Bar
            document.getElementById('budget-total-spent').textContent = this.formatCurrency(summary.total_spent);
            document.getElementById('budget-total-limit').textContent = this.formatCurrency(summary.total_budgeted);
            document.getElementById('budget-total-remaining').textContent = this.formatCurrency(summary.total_remaining);

            const overallBar = document.getElementById('budget-overall-bar');
            overallBar.style.width = `${Math.min(100, summary.overall_percentage)}%`;
            overallBar.className = `progress-bar ${summary.overall_percentage > 100 ? 'danger' : summary.overall_percentage >= 80 ? 'warning' : 'success'}`;

            const grid = document.getElementById('budgets-cards-grid');
            if (budgets.length === 0) {
                grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                    <p style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">No budgets configured for ${monthInput}</p>
                    <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">Set spending caps for Canteen, Xerox, Travel, or Outings to stay on track.</p>
                    <button class="btn btn-primary" onclick="App.openBudgetModal()">+ Create Budget Limit</button>
                </div>`;
                return;
            }

            grid.innerHTML = budgets.map(b => `
                <div class="card" style="margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span class="cat-dot" style="background: ${b.category_color || '#3B82F6'}; width: 12px; height: 12px;"></span>
                            <h4 style="font-size: 15px; font-weight: 700;">${b.category_name}</h4>
                        </div>
                        <div style="display: flex; gap: 4px;">
                            <button class="btn-icon" title="Delete" onclick="App.deleteBudget(${b.id})">${App.icons.delete}</button>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px;">
                        <span>Spent: <strong>${this.formatCurrency(b.spent_amount)}</strong></span>
                        <span style="color: var(--text-muted);">Cap: ${this.formatCurrency(b.amount_limit)}</span>
                    </div>

                    <div class="progress-container">
                        <div class="progress-bar ${b.is_exceeded ? 'danger' : b.is_warning ? 'warning' : 'success'}" 
                             style="width: ${Math.min(100, b.percentage_spent)}%;"></div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; margin-top: 8px;">
                        <span style="color: ${b.is_exceeded ? 'var(--danger)' : b.is_warning ? 'var(--warning)' : 'var(--success)'}; font-weight: 600;">
                            ${b.is_exceeded ? 'Over Budget' : b.is_warning ? 'Approaching Limit' : 'Within Budget'}
                        </span>
                        <span style="color: var(--text-muted);">${b.percentage_spent}%</span>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            this.showToast('Failed to load budgets', 'error');
        }
    },

    openBudgetModal() {
        const form = document.getElementById('form-budget');
        form.reset();
        this.populateCategorySelects();
        const currentMonth = document.getElementById('budget-month-selector')?.value || new Date().toISOString().substring(0, 7);
        document.getElementById('budget-form-month').value = currentMonth;
        document.getElementById('modal-budget').classList.add('open');
    },

    async handleSaveBudget(e) {
        e.preventDefault();
        const data = {
            category_id: parseInt(document.getElementById('budget-category-id').value),
            amount_limit: parseFloat(document.getElementById('budget-amount-limit').value),
            month: document.getElementById('budget-form-month').value,
            alert_threshold: parseFloat(document.getElementById('budget-threshold').value)
        };

        try {
            await API.saveBudget(data);
            this.showToast('Budget saved successfully');
            this.closeModals();
            this.loadBudgets();
        } catch (err) {
            this.showToast(err.message || 'Error saving budget', 'error');
        }
    },

    async deleteBudget(id) {
        if (!confirm('Remove this category budget?')) return;
        try {
            await API.deleteBudget(id);
            this.showToast('Budget deleted');
            this.loadBudgets();
        } catch (err) {
            this.showToast(err.message || 'Error deleting budget', 'error');
        }
    },

    // ================= 5. SAVINGS GOALS =================
    async loadGoals() {
        try {
            const res = await API.getGoals();
            const goals = res.goals || [];
            const summary = res.summary || {};

            // Update KPIs
            document.getElementById('goals-kpi-count').textContent = summary.total_goals || 0;
            document.getElementById('goals-kpi-completed').textContent = `${summary.completed_goals || 0} completed`;
            document.getElementById('goals-kpi-target').textContent = this.formatCurrency(summary.total_target);
            document.getElementById('goals-kpi-saved').textContent = this.formatCurrency(summary.total_saved);
            document.getElementById('goals-kpi-pct').textContent = `${summary.overall_percentage || 0}% achieved`;

            const grid = document.getElementById('goals-cards-grid');
            if (goals.length === 0) {
                grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 40px; background: white; border-radius: var(--radius-md); border: 1px solid var(--border);">
                    <p style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">No savings goals yet</p>
                    <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 16px;">Set targets for vacation trips, emergency cushions, or large purchases.</p>
                    <button class="btn btn-primary" onclick="App.openGoalModal()">+ Create Savings Goal</button>
                </div>`;
                return;
            }

            grid.innerHTML = goals.map(g => `
                <div class="card" style="margin-bottom: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 14px;">
                        <div>
                            <span class="pill" style="background: ${g.color || '#10B981'}22; color: ${g.color || '#10B981'}; font-weight: 600;">
                                ${g.is_completed ? 'Target Achieved' : `${g.progress_percentage}%`}
                            </span>
                            <h4 style="font-size: 16px; font-weight: 700; margin-top: 6px;">${g.name}</h4>
                            ${g.target_date ? `<span style="font-size: 11px; color: var(--text-muted);">Target: ${g.target_date} (${g.days_left !== null ? g.days_left + ' days left' : ''})</span>` : ''}
                        </div>
                        <div style="display: flex; gap: 4px;">
                            <button class="btn-icon" title="Edit" onclick="App.openGoalModal(${JSON.stringify(g).replace(/"/g, '&quot;')})">${App.icons.edit}</button>
                            <button class="btn-icon" title="Delete" onclick="App.deleteGoal(${g.id})">${App.icons.delete}</button>
                        </div>
                    </div>

                    <div style="margin: 12px 0;">
                        <div style="display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 4px;">
                            <span>Saved: <strong style="color: ${g.color || '#10B981'};">${this.formatCurrency(g.current_amount)}</strong></span>
                            <span style="color: var(--text-muted);">Goal: ${this.formatCurrency(g.target_amount)}</span>
                        </div>
                        <div class="progress-container">
                            <div class="progress-bar" style="width: ${g.progress_percentage}%; background: ${g.color || '#10B981'};"></div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 14px; margin-top: 14px;">
                        <span style="font-size: 12px; color: var(--text-muted);">
                            ${g.remaining_amount > 0 ? `${this.formatCurrency(g.remaining_amount)} to go` : 'Goal fulfilled!'}
                        </span>
                        <button class="btn btn-secondary btn-sm" onclick="App.openContributeModal(${g.id}, '${g.name}')">
                            + Deposit
                        </button>
                    </div>
                </div>
            `).join('');
        } catch (err) {
            this.showToast('Failed to load goals', 'error');
        }
    },

    openGoalModal(g = null) {
        const form = document.getElementById('form-goal');
        form.reset();
        const editIdEl = document.getElementById('goal-edit-id');
        const titleEl = document.getElementById('modal-goal-title');

        if (g) {
            titleEl.textContent = 'Edit Savings Goal';
            editIdEl.value = g.id;
            document.getElementById('goal-name').value = g.name;
            document.getElementById('goal-target').value = g.target_amount;
            document.getElementById('goal-current').value = g.current_amount;
            document.getElementById('goal-date').value = g.target_date || '';
            document.getElementById('goal-color').value = g.color || '#10B981';
            document.getElementById('goal-notes').value = g.notes || '';
        } else {
            titleEl.textContent = 'New Savings Goal';
            editIdEl.value = '';
            document.getElementById('goal-current').value = '0.00';
            document.getElementById('goal-color').value = '#10B981';
        }

        document.getElementById('modal-goal').classList.add('open');
    },

    async handleSaveGoal(e) {
        e.preventDefault();
        const editId = document.getElementById('goal-edit-id').value;
        const data = {
            name: document.getElementById('goal-name').value.trim(),
            target_amount: parseFloat(document.getElementById('goal-target').value),
            current_amount: parseFloat(document.getElementById('goal-current').value) || 0,
            target_date: document.getElementById('goal-date').value || null,
            color: document.getElementById('goal-color').value,
            notes: document.getElementById('goal-notes').value.trim()
        };

        try {
            if (editId) {
                await API.updateGoal(editId, data);
                this.showToast('Goal updated');
            } else {
                await API.createGoal(data);
                this.showToast('Savings goal created');
            }
            this.closeModals();
            this.loadGoals();
        } catch (err) {
            this.showToast(err.message || 'Error saving goal', 'error');
        }
    },

    openContributeModal(goalId, goalName) {
        document.getElementById('form-contribute').reset();
        document.getElementById('contribute-goal-id').value = goalId;
        document.getElementById('contribute-goal-name').value = goalName;
        document.getElementById('contribute-date').value = new Date().toISOString().split('T')[0];
        this.populateAccountSelects();
        document.getElementById('modal-contribute').classList.add('open');
    },

    async handleSaveContribution(e) {
        e.preventDefault();
        const goalId = document.getElementById('contribute-goal-id').value;
        const amount = parseFloat(document.getElementById('contribute-amount').value);
        const date = document.getElementById('contribute-date').value;
        const accId = document.getElementById('contribute-account-id').value;
        const notes = document.getElementById('contribute-notes').value.trim();

        try {
            await API.contributeGoal(goalId, {
                amount,
                date,
                account_id: accId ? parseInt(accId) : null,
                notes
            });
            this.showToast('Contribution recorded!');
            this.closeModals();
            await Promise.all([this.loadAccountsList(), this.loadGoals()]);
        } catch (err) {
            this.showToast(err.message || 'Contribution failed', 'error');
        }
    },

    async deleteGoal(id) {
        if (!confirm('Are you sure you want to delete this savings goal?')) return;
        try {
            await API.deleteGoal(id);
            this.showToast('Goal removed');
            this.loadGoals();
        } catch (err) {
            this.showToast(err.message || 'Error deleting goal', 'error');
        }
    },

    // ================= 6. REPORTS =================
    async loadReports() {
        const startDate = document.getElementById('report-start-date').value;
        const endDate = document.getElementById('report-end-date').value;

        try {
            const [cfRes, spendRes] = await Promise.all([
                API.getCashFlowReport(startDate, endDate),
                API.getSpendingReport(startDate, endDate)
            ]);

            const summary = cfRes.summary || {};
            document.getElementById('report-kpi-income').textContent = this.formatCurrency(summary.total_income);
            document.getElementById('report-kpi-expense').textContent = this.formatCurrency(summary.total_expense);
            document.getElementById('report-kpi-net').textContent = this.formatCurrency(summary.total_net);
            document.getElementById('report-kpi-rate').textContent = `${summary.overall_savings_rate}%`;

            // Cash flow trend line
            const cfData = cfRes.data || [];
            ChartEngine.renderLineChart(
                'chart-report-cashflow',
                cfData.map(d => d.month),
                cfData.map(d => d.net),
                '#4F46E5',
                'Net Cash Flow'
            );

            // Category spending
            const catData = spendRes.categories || [];
            ChartEngine.renderDonutChart('chart-report-spending', catData, this.formatCurrency(spendRes.total_spending));

            // Breakdown list
            const tableContainer = document.getElementById('report-spending-table');
            if (catData.length === 0) {
                tableContainer.innerHTML = `<p style="font-size: 13px; color: var(--text-muted); text-align: center;">No spending during this period.</p>`;
            } else {
                tableContainer.innerHTML = catData.map(c => `
                    <div class="cat-item">
                        <div class="cat-info">
                            <span class="cat-dot" style="background: ${c.color || '#3B82F6'};"></span>
                            <span class="cat-name">${c.name}</span>
                        </div>
                        <div>
                            <span class="cat-amt">${this.formatCurrency(c.total_amount)}</span>
                            <span class="cat-pct">(${c.percentage}%)</span>
                        </div>
                    </div>
                `).join('');
            }

        } catch (err) {
            this.showToast('Failed to generate report', 'error');
        }
    },

    async handleExportCSV() {
        try {
            const startDate = document.getElementById('txn-filter-start')?.value || '';
            const endDate = document.getElementById('txn-filter-end')?.value || '';
            const blob = await API.exportCSV(startDate, endDate);

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `finance_transactions_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();

            this.showToast('CSV export downloaded');
        } catch (err) {
            this.showToast('Export failed: ' + err.message, 'error');
        }
    },

    // Modal Helpers
    closeModals() {
        document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('open'));
    }
};

// Start application once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
