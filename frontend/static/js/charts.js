/**
 * Zero-dependency HTML5 Canvas Charts
 */
const ChartEngine = {
    // Utility to get retina-sharp canvas context
    setupCanvas(canvas) {
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = (rect.width || 400) * dpr;
        canvas.height = (rect.height || 260) * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        return { ctx, width: rect.width || 400, height: rect.height || 260 };
    },

    formatCurrency(val, currency = 'INR') {
        const symbol = currency === 'INR' ? '₹' : currency === 'EUR' ? '€' : currency === 'GBP' ? '£' : '$';
        return `${symbol}${val.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
    },

    // Double Bar Chart for Income vs Expense
    renderDoubleBarChart(canvasId, labels, incomeData, expenseData) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const setup = this.setupCanvas(canvas);
        if (!setup) return;
        const { ctx, width, height } = setup;

        ctx.clearRect(0, 0, width, height);

        if (!labels || labels.length === 0) {
            ctx.fillStyle = '#9CA3AF';
            ctx.font = '14px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', width / 2, height / 2);
            return;
        }

        const padding = { top: 30, right: 20, bottom: 40, left: 55 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        const maxVal = Math.max(100, ...incomeData, ...expenseData) * 1.15;

        // Draw horizontal grid lines & Y-axis labels
        const gridSteps = 4;
        ctx.strokeStyle = '#F3F4F6';
        ctx.fillStyle = '#9CA3AF';
        ctx.font = '11px system-ui, sans-serif';
        ctx.textAlign = 'right';

        for (let i = 0; i <= gridSteps; i++) {
            const yVal = (maxVal / gridSteps) * i;
            const yPos = padding.top + chartH - (yVal / maxVal) * chartH;
            ctx.beginPath();
            ctx.moveTo(padding.left, yPos);
            ctx.lineTo(width - padding.right, yPos);
            ctx.stroke();
            ctx.fillText(this.formatCurrency(yVal), padding.left - 8, yPos + 4);
        }

        // Draw Bars
        const groupW = chartW / labels.length;
        const barW = Math.min(24, (groupW - 16) / 2);

        labels.forEach((label, idx) => {
            const groupX = padding.left + idx * groupW + groupW / 2;
            const inc = incomeData[idx] || 0;
            const exp = expenseData[idx] || 0;

            const incH = (inc / maxVal) * chartH;
            const expH = (exp / maxVal) * chartH;

            // Income bar (Green)
            const incX = groupX - barW - 2;
            const incY = padding.top + chartH - incH;
            ctx.fillStyle = '#10B981';
            this.roundRect(ctx, incX, incY, barW, Math.max(2, incH), 4);

            // Expense bar (Red/Orange)
            const expX = groupX + 2;
            const expY = padding.top + chartH - expH;
            ctx.fillStyle = '#EF4444';
            this.roundRect(ctx, expX, expY, barW, Math.max(2, expH), 4);

            // X-axis label
            ctx.fillStyle = '#6B7280';
            ctx.font = '11px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(label, groupX, height - 15);
        });
    },

    // Donut Chart for Category Distribution
    renderDonutChart(canvasId, items, centerText = '') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const setup = this.setupCanvas(canvas);
        if (!setup) return;
        const { ctx, width, height } = setup;

        ctx.clearRect(0, 0, width, height);

        if (!items || items.length === 0) {
            ctx.fillStyle = '#9CA3AF';
            ctx.font = '14px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No expenses recorded', width / 2, height / 2);
            return;
        }

        const total = items.reduce((sum, item) => sum + (item.amount || 0), 0);
        if (total <= 0) {
            ctx.fillStyle = '#9CA3AF';
            ctx.font = '14px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No spending yet', width / 2, height / 2);
            return;
        }

        const centerX = width / 2;
        const centerY = height / 2;
        const outerRadius = Math.min(centerX, centerY) - 15;
        const innerRadius = outerRadius * 0.62;

        let startAngle = -0.5 * Math.PI;

        items.forEach((item) => {
            const sliceAngle = ((item.amount || 0) / total) * (2 * Math.PI);
            const endAngle = startAngle + sliceAngle;

            ctx.beginPath();
            ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
            ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
            ctx.closePath();

            ctx.fillStyle = item.color || '#3B82F6';
            ctx.fill();

            startAngle = endAngle;
        });

        // Center cutout background
        ctx.beginPath();
        ctx.arc(centerX, centerY, innerRadius - 1, 0, 2 * Math.PI);
        ctx.fillStyle = '#FFFFFF';
        ctx.fill();

        // Center text
        ctx.textAlign = 'center';
        ctx.fillStyle = '#111827';
        ctx.font = 'bold 16px system-ui, sans-serif';
        ctx.fillText(centerText || this.formatCurrency(total), centerX, centerY + 5);

        ctx.font = '11px system-ui, sans-serif';
        ctx.fillStyle = '#6B7280';
        ctx.fillText('Total Spent', centerX, centerY - 14);
    },

    // Smooth Line/Area Chart for Cash Flow / Net Trend
    renderLineChart(canvasId, labels, dataPoints, color = '#3B82F6', label = 'Net Cash Flow') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const setup = this.setupCanvas(canvas);
        if (!setup) return;
        const { ctx, width, height } = setup;

        ctx.clearRect(0, 0, width, height);

        if (!labels || labels.length === 0) {
            ctx.fillStyle = '#9CA3AF';
            ctx.font = '14px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', width / 2, height / 2);
            return;
        }

        const padding = { top: 30, right: 25, bottom: 40, left: 55 };
        const chartW = width - padding.left - padding.right;
        const chartH = height - padding.top - padding.bottom;

        const minVal = Math.min(0, ...dataPoints);
        const maxVal = Math.max(100, ...dataPoints) * 1.15;
        const range = maxVal - minVal || 1;

        // Draw grid
        const gridSteps = 4;
        ctx.strokeStyle = '#F3F4F6';
        ctx.fillStyle = '#9CA3AF';
        ctx.font = '11px system-ui, sans-serif';
        ctx.textAlign = 'right';

        for (let i = 0; i <= gridSteps; i++) {
            const yVal = minVal + (range / gridSteps) * i;
            const yPos = padding.top + chartH - ((yVal - minVal) / range) * chartH;
            ctx.beginPath();
            ctx.moveTo(padding.left, yPos);
            ctx.lineTo(width - padding.right, yPos);
            ctx.stroke();
            ctx.fillText(this.formatCurrency(yVal), padding.left - 8, yPos + 4);
        }

        const stepX = chartW / (labels.length - 1 || 1);
        const points = dataPoints.map((val, idx) => ({
            x: padding.left + idx * stepX,
            y: padding.top + chartH - ((val - minVal) / range) * chartH
        }));

        // Fill area gradient
        const gradient = ctx.createLinearGradient(0, padding.top, 0, height - padding.bottom);
        gradient.addColorStop(0, `${color}44`);
        gradient.addColorStop(1, `${color}00`);

        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.lineTo(points[points.length - 1].x, padding.top + chartH);
        ctx.lineTo(points[0].x, padding.top + chartH);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Stroke line
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.stroke();

        // Draw dots and X labels
        points.forEach((p, idx) => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
            ctx.fillStyle = '#FFFFFF';
            ctx.fill();
            ctx.strokeStyle = color;
            ctx.lineWidth = 2;
            ctx.stroke();

            // X label
            ctx.fillStyle = '#6B7280';
            ctx.font = '11px system-ui, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(labels[idx], p.x, height - 15);
        });
    },

    roundRect(ctx, x, y, width, height, radius) {
        if (width < 2 * radius) radius = width / 2;
        if (height < 2 * radius) radius = height / 2;
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.arcTo(x + width, y, x + width, y + height, radius);
        ctx.arcTo(x + width, y + height, x, y + height, radius);
        ctx.arcTo(x, y + height, x, y, radius);
        ctx.arcTo(x, y, x + width, y, radius);
        ctx.closePath();
        ctx.fill();
    }
};
