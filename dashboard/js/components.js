/**
 * HalAudit UI Components
 * Reusable component rendering functions for the dashboard.
 */

const Components = {

    /**
     * Render the Trust Score Gauge (animated SVG circle)
     */
    trustGauge(score, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const percentage = Math.round(score * 100);
        const radius = 80;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (score * circumference);

        let level = 'low';
        let strokeColor = 'var(--contradicted)';
        if (score >= 0.7) {
            level = 'high';
            strokeColor = 'var(--supported)';
        } else if (score >= 0.4) {
            level = 'medium';
            strokeColor = 'var(--unverifiable)';
        }

        container.innerHTML = `
            <div class="gauge-wrapper gauge-${level}">
                <svg class="gauge-svg" viewBox="0 0 200 200">
                    <circle class="gauge-track" cx="100" cy="100" r="${radius}" />
                    <circle class="gauge-fill" cx="100" cy="100" r="${radius}"
                        stroke-dasharray="${circumference}"
                        stroke-dashoffset="${circumference}"
                        style="stroke: ${strokeColor};"
                        data-target-offset="${offset}" />
                </svg>
                <div class="gauge-text">
                    <div class="gauge-value" style="color: ${strokeColor};">0%</div>
                    <div class="gauge-label">Trust Score</div>
                </div>
            </div>
        `;

        // Animate after render
        requestAnimationFrame(() => {
            setTimeout(() => {
                const fill = container.querySelector('.gauge-fill');
                const valueEl = container.querySelector('.gauge-value');
                if (fill) {
                    fill.style.strokeDashoffset = offset;
                }
                // Animate the number
                this.animateNumber(valueEl, 0, percentage, 1200, '%');
            }, 100);
        });
    },

    /**
     * Animate a number from start to end
     */
    animateNumber(element, start, end, duration, suffix = '') {
        if (!element) return;
        const startTime = performance.now();
        const update = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (end - start) * eased);
            element.textContent = current + suffix;
            if (progress < 1) {
                requestAnimationFrame(update);
            }
        };
        requestAnimationFrame(update);
    },

    /**
     * Render score summary stats
     */
    scoreStats(report, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="stat-item">
                <div class="stat-dot supported"></div>
                <div class="stat-info">
                    <div class="stat-label">Supported</div>
                    <div class="stat-value" style="color: var(--supported);">${report.supported_count}</div>
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-dot contradicted"></div>
                <div class="stat-info">
                    <div class="stat-label">Contradicted</div>
                    <div class="stat-value" style="color: var(--contradicted);">${report.contradicted_count}</div>
                </div>
            </div>
            <div class="stat-item">
                <div class="stat-dot unverifiable"></div>
                <div class="stat-info">
                    <div class="stat-label">Unverifiable</div>
                    <div class="stat-value" style="color: var(--unverifiable);">${report.unverifiable_count}</div>
                </div>
            </div>
            <div class="latency-badge">
                <span class="icon">⚡</span>
                ${report.latency_ms.toFixed(0)}ms
            </div>
        `;
    },

    /**
     * Render a single claim card
     */
    claimCard(claim, index) {
        const labelClass = claim.label.toLowerCase();
        const confidencePercent = Math.round(claim.confidence * 100);

        const verdictIcons = {
            'supported': '✓',
            'contradicted': '✗',
            'unverifiable': '?'
        };

        const evidenceHtml = claim.evidence && claim.evidence.length > 0
            ? claim.evidence.map((ev, i) => `
                <div class="evidence-item">
                    <div class="evidence-text">${this.escapeHtml(ev.text)}</div>
                    <div class="evidence-meta">
                        <span class="evidence-source">${this.escapeHtml(ev.source)}</span>
                        <span class="evidence-score">Relevance: ${(ev.relevance_score * 100).toFixed(0)}%</span>
                    </div>
                </div>
            `).join('')
            : '<div class="evidence-item"><div class="evidence-text" style="font-style: italic;">No evidence retrieved from corpus.</div></div>';

        return `
            <div class="claim-card ${labelClass}" id="claim-${index}">
                <div class="claim-header" onclick="Components.toggleEvidence(${index})">
                    <div class="claim-content">
                        <div class="claim-index">Claim #${index + 1}</div>
                        <div class="claim-text">${this.escapeHtml(claim.claim)}</div>
                        ${claim.reasoning ? `<div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; font-style: italic;">${this.escapeHtml(claim.reasoning)}</div>` : ''}
                    </div>
                    <div class="verdict-badge ${labelClass}">
                        ${verdictIcons[labelClass] || '?'} ${claim.label}
                    </div>
                </div>
                <div class="confidence-bar-container">
                    <div class="confidence-bar-label">
                        <span>Confidence</span>
                        <span>${confidencePercent}%</span>
                    </div>
                    <div class="confidence-bar-track">
                        <div class="confidence-bar-fill" style="width: 0%;" data-target="${confidencePercent}"></div>
                    </div>
                </div>
                <div class="toggle-evidence" onclick="Components.toggleEvidence(${index})">
                    <span class="arrow">▼</span>
                    <span>Evidence (${claim.evidence ? claim.evidence.length : 0})</span>
                </div>
                <div class="evidence-section" id="evidence-${index}">
                    <div class="evidence-list">
                        ${evidenceHtml}
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * Toggle evidence accordion for a claim card
     */
    toggleEvidence(index) {
        const section = document.getElementById(`evidence-${index}`);
        const toggle = document.querySelector(`#claim-${index} .toggle-evidence`);
        if (section && toggle) {
            section.classList.toggle('open');
            toggle.classList.toggle('open');
        }
    },

    /**
     * Render all claim cards
     */
    claimsList(claims, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!claims || claims.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-text">No claims extracted from the text.</div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="claims-section-title">
                📋 Claim Analysis (${claims.length} claims)
            </div>
            ${claims.map((claim, i) => this.claimCard(claim, i)).join('')}
        `;

        // Animate confidence bars after render
        requestAnimationFrame(() => {
            setTimeout(() => {
                container.querySelectorAll('.confidence-bar-fill').forEach(bar => {
                    const target = bar.getAttribute('data-target');
                    bar.style.width = target + '%';
                });
            }, 200);
        });
    },

    /**
     * Render a history table row
     */
    historyRow(audit, index) {
        const date = new Date(audit.timestamp);
        const dateStr = date.toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric'
        });
        const timeStr = date.toLocaleTimeString('en-US', {
            hour: '2-digit', minute: '2-digit'
        });

        const trustPercent = Math.round(audit.trust_score * 100);
        let trustColor = 'var(--contradicted)';
        if (audit.trust_score >= 0.7) trustColor = 'var(--supported)';
        else if (audit.trust_score >= 0.4) trustColor = 'var(--unverifiable)';

        return `
            <tr onclick="app.viewAuditDetail('${audit.id}')" data-audit-id="${audit.id}">
                <td>
                    <div style="font-size: 0.85rem;">${dateStr}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${timeStr}</div>
                </td>
                <td class="text-preview">${this.escapeHtml(audit.original_text.substring(0, 120))}${audit.original_text.length > 120 ? '...' : ''}</td>
                <td>
                    <div class="trust-mini-bar">
                        <div class="trust-mini-value" style="color: ${trustColor};">${trustPercent}%</div>
                        <div class="trust-mini-track">
                            <div class="trust-mini-fill" style="width: ${trustPercent}%; background: ${trustColor};"></div>
                        </div>
                    </div>
                </td>
                <td style="font-family: var(--font-mono);">${audit.total_claims}</td>
                <td>
                    <span style="color: var(--supported);">${audit.supported_count}</span> / 
                    <span style="color: var(--contradicted);">${audit.contradicted_count}</span> / 
                    <span style="color: var(--unverifiable);">${audit.unverifiable_count}</span>
                </td>
                <td>
                    <span class="latency-badge">${audit.latency_ms.toFixed(0)}ms</span>
                </td>
            </tr>
        `;
    },

    /**
     * Render analytics metric cards
     */
    metricCard(icon, bgClass, value, label) {
        return `
            <div class="metric-card">
                <div class="metric-icon ${bgClass}">${icon}</div>
                <div class="metric-value">${value}</div>
                <div class="metric-label">${label}</div>
            </div>
        `;
    },

    /**
     * Render loading skeleton
     */
    loadingSkeleton(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="loading-overlay">
                <div class="spinner"></div>
                <div class="loading-text">Analyzing claims and retrieving evidence...</div>
            </div>
        `;
    },

    /**
     * Show a toast notification
     */
    showToast(message, type = 'info', duration = 4000) {
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }

        const icons = { success: '✓', error: '✗', info: 'ℹ' };
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${this.escapeHtml(message)}`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            toast.style.transition = 'all 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    /**
     * Render an audit detail modal
     */
    auditDetailModal(report) {
        const overlay = document.createElement('div');
        overlay.className = 'modal-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) overlay.remove();
        };

        overlay.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2 class="card-title">Audit Report</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">✕</button>
                </div>
                <div class="trust-score-container">
                    <div id="modal-gauge"></div>
                    <div id="modal-stats" class="score-stats"></div>
                </div>
                <div class="original-text-section">
                    <div class="card-subtitle">Original Text</div>
                    <div class="original-text">${this.escapeHtml(report.original_text)}</div>
                </div>
                <div id="modal-claims" class="claims-list" style="margin-top: 24px;"></div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Render sub-components
        this.trustGauge(report.trust_score, 'modal-gauge');
        this.scoreStats(report, 'modal-stats');
        this.claimsList(report.claims, 'modal-claims');
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
