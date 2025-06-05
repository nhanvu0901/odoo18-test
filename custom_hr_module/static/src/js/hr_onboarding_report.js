import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";

class HROnboardingReportAction extends Component {
    static template = "hr_onboarding_report.HROnboardingReportTemplate";

    setup() {
        this.onboardingChartRef = useRef("onboardingChart");
        this.offboardingChartRef = useRef("offboardingChart");

        onMounted(() => {
            this.renderCharts();
        });
    }

    get reportData() {
        return this.props.action.context.report_data || {};
    }

    get dateFrom() {
        return this.props.action.context.date_from || '';
    }

    get dateTo() {
        return this.props.action.context.date_to || '';
    }

    get departments() {
        return this.props.action.context.departments || [];
    }

    get employeeData() {
        return this.reportData.employee_data || [];
    }

    get onboardingStats() {
        return this.reportData.onboarding_stats || {};
    }

    get offboardingStats() {
        return this.reportData.offboarding_stats || {};
    }

    renderCharts() {
        if (this.onboardingChartRef.el) {
            this.renderPieChart(this.onboardingChartRef.el, this.onboardingStats, 'Onboarding');
        }
        if (this.offboardingChartRef.el) {
            this.renderPieChart(this.offboardingChartRef.el, this.offboardingStats, 'Offboarding');
        }
    }

    renderPieChart(canvas, data, title) {
        const ctx = canvas.getContext('2d');

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const total = Object.values(data).reduce((sum, val) => sum + val, 0);
        if (total === 0) {
            ctx.fillStyle = '#666';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`No ${title.toLowerCase()} data for selected period`, canvas.width / 2, canvas.height / 2);
            return;
        }

        const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#FF9F7F', '#8FBC8F'];
        let currentAngle = 0;
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        const radius = Math.min(centerX, centerY) - 60;

        // Draw pie slices
        Object.entries(data).forEach(([department, count], index) => {
            const sliceAngle = (count / total) * 2 * Math.PI;

            // Draw slice
            ctx.beginPath();
            ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
            ctx.lineTo(centerX, centerY);
            ctx.fillStyle = colors[index % colors.length];
            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();

            currentAngle += sliceAngle;
        });

        // Draw legend
        let legendY = 20;
        ctx.font = '12px Arial';
        ctx.textAlign = 'left';

        Object.entries(data).forEach(([department, count], index) => {
            const percentage = ((count / total) * 100).toFixed(1);

            // Draw color box
            ctx.fillStyle = colors[index % colors.length];
            ctx.fillRect(canvas.width - 150, legendY, 12, 12);

            // Draw text
            ctx.fillStyle = '#333';
            ctx.fillText(`${department}: ${count} (${percentage}%)`, canvas.width - 135, legendY + 10);

            legendY += 20;
        });
    }
}

registry.category("actions").add("hr_onboarding_report_action", HROnboardingReportAction);