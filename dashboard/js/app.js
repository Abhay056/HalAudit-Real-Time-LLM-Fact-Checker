/**
 * HalAudit Dashboard — Main Application
 * SPA router, state management, and view controllers.
 */

const app = {
    // --- State ---
    currentView: 'audit',
    currentReport: null,
    historyData: null,
    historyPage: 0,
    historyPageSize: 15,
    isLoading: false,

    // --- Initialization ---
    init() {
        this.bindNavigation();
        this.bindAuditForm();
        this.switchView('audit');

        // Sample text for easy demo
        const textarea = document.getElementById('audit-text');
        if (textarea) {
            textarea.value = `Albert Einstein was born in Austria in 1879. He developed the theory of relativity and won the Nobel Prize in Physics in 1921 for his work on relativity. The speed of light is approximately 300,000 kilometers per second. The Great Wall of China is visible from space with the naked eye. Water boils at 100 degrees Celsius at standard atmospheric pressure. The human body has approximately 206 bones. Python was created by James Gosling and first released in 1991.`;
            this.updateCharCount();
        }

        console.log('HalAudit Dashboard initialized');
    },

    // --- Navigation ---
    bindNavigation() {
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const view = tab.getAttribute('data-view');
                this.switchView(view);
            });
        });
    },

    switchView(viewName) {
        this.currentView = viewName;

        // Update nav tabs
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-view') === viewName);
        });

        // Update views
        document.querySelectorAll('.view').forEach(view => {
            view.classList.toggle('active', view.id === `${viewName}-view`);
        });

        // Load data for the view
        if (viewName === 'history') this.loadHistory();
        if (viewName === 'analytics') this.loadAnalytics();
    },

    // --- Audit Form ---
    bindAuditForm() {
        const textarea = document.getElementById('audit-text');
        const auditBtn = document.getElementById('audit-btn');
        const clearBtn = document.getElementById('clear-btn');

        if (textarea) {
            textarea.addEventListener('input', () => this.updateCharCount());
        }

        if (auditBtn) {
            auditBtn.addEventListener('click', () => this.runAudit());
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearAudit());
        }
    },

    updateCharCount() {
        const textarea = document.getElementById('audit-text');
        const counter = document.getElementById('char-count');
        if (textarea && counter) {
            counter.textContent = `${textarea.value.length} / 10,000`;
        }
    },

    // --- Run Audit ---
    async runAudit() {
        const textarea = document.getElementById('audit-text');
        const text = textarea ? textarea.value.trim() : '';

        if (text.length < 10) {
            Components.showToast('Please enter at least 10 characters to audit.', 'error');
            return;
        }

        if (this.isLoading) return;
        this.isLoading = true;

        const auditBtn = document.getElementById('audit-btn');
        if (auditBtn) {
            auditBtn.disabled = true;
            auditBtn.innerHTML = '<span class="spinner"></span> Auditing...';
        }

        // Show loading state
        const resultsSection = document.getElementById('results-section');
        if (resultsSection) {
            resultsSection.style.display = 'block';
            resultsSection.innerHTML = `
                <div class="card">
                    <div class="loading-overlay">
                        <div class="spinner"></div>
                        <div class="loading-text">Extracting claims and retrieving evidence...</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 8px;">
                            This may take 10-30 seconds on first run while models load.
                        </div>
                    </div>
                </div>
            `;
        }

        try {
            const report = await api.auditText(text);
            this.currentReport = report;
            this.renderResults(report);
            Components.showToast(
                `Audit complete: ${report.total_claims} claims analyzed in ${report.latency_ms.toFixed(0)}ms`,
                'success'
            );
        } catch (error) {
            console.error('Audit failed:', error);
            if (resultsSection) {
                resultsSection.innerHTML = `
                    <div class="card">
                        <div class="empty-state">
                            <div class="empty-state-icon">⚠️</div>
                            <div class="empty-state-text">
                                Audit failed: ${Components.escapeHtml(error.message)}
                            </div>
                            <button class="btn btn-secondary btn-sm" onclick="app.runAudit()" style="margin-top: 16px;">
                                Retry
                            </button>
                        </div>
                    </div>
                `;
            }
            Components.showToast(`Audit failed: ${error.message}`, 'error');
        } finally {
            this.isLoading = false;
            if (auditBtn) {
                auditBtn.disabled = false;
                auditBtn.innerHTML = '🔍 Audit Text';
            }
        }
    },

    // --- Render Results ---
    renderResults(report) {
        const resultsSection = document.getElementById('results-section');
        if (!resultsSection) return;

        resultsSection.style.display = 'block';
        resultsSection.innerHTML = `
            <div class="results-section">
                <div class="card" style="margin-bottom: var(--space-xl);">
                    <div class="trust-score-container">
                        <div id="trust-gauge"></div>
                        <div id="score-stats" class="score-stats"></div>
                    </div>
                </div>

                <div class="card" style="margin-bottom: var(--space-xl);">
                    <div id="claims-list"></div>
                </div>

                <div class="card original-text-section">
                    <div class="card-subtitle" style="display: flex; justify-content: space-between; align-items: center;">
                        <span>📝 Original Text</span>
                        <span class="latency-badge">
                            <span class="icon">⚡</span>
                            Total: ${report.latency_ms.toFixed(0)}ms
                            ${report.latency_breakdown ? ` · Extract: ${(report.latency_breakdown.claim_extraction_ms || 0).toFixed(0)}ms · RAG: ${(report.latency_breakdown.rag_retrieval_ms || 0).toFixed(0)}ms · NLI: ${(report.latency_breakdown.nli_scoring_ms || 0).toFixed(0)}ms` : ''}
                        </span>
                    </div>
                    <div class="original-text">${Components.escapeHtml(report.original_text)}</div>
                </div>
            </div>
        `;

        // Render sub-components
        Components.trustGauge(report.trust_score, 'trust-gauge');
        Components.scoreStats(report, 'score-stats');
        Components.claimsList(report.claims, 'claims-list');
    },

    // --- Clear Audit ---
    clearAudit() {
        const textarea = document.getElementById('audit-text');
        const resultsSection = document.getElementById('results-section');

        if (textarea) {
            textarea.value = '';
            this.updateCharCount();
        }
        if (resultsSection) {
            resultsSection.style.display = 'none';
            resultsSection.innerHTML = '';
        }
        this.currentReport = null;
    },

    // --- History View ---
    async loadHistory() {
        const container = document.getElementById('history-content');
        if (!container) return;

        container.innerHTML = `
            <div class="loading-overlay" style="padding: 48px;">
                <div class="spinner"></div>
                <div class="loading-text">Loading audit history...</div>
            </div>
        `;

        try {
            const data = await api.getAuditHistory({
                limit: this.historyPageSize,
                offset: this.historyPage * this.historyPageSize,
            });
            this.historyData = data;
            this.renderHistory(data);
        } catch (error) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <div class="empty-state-text">Failed to load history: ${Components.escapeHtml(error.message)}</div>
                </div>
            `;
        }
    },

    renderHistory(data) {
        const container = document.getElementById('history-content');
        if (!container) return;

        if (!data.audits || data.audits.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📋</div>
                    <div class="empty-state-text">
                        No audit history yet. Run your first audit to see results here.
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="app.switchView('audit')" style="margin-top: 16px;">
                        Run an Audit
                    </button>
                </div>
            `;
            return;
        }

        const totalPages = Math.ceil(data.total / this.historyPageSize);

        container.innerHTML = `
            <div class="history-table-wrapper">
                <table class="history-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Text</th>
                            <th>Trust Score</th>
                            <th>Claims</th>
                            <th>S / C / U</th>
                            <th>Latency</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.audits.map((audit, i) => Components.historyRow(audit, i)).join('')}
                    </tbody>
                </table>
            </div>
            <div class="pagination">
                <button class="page-btn" onclick="app.historyPrevPage()" ${this.historyPage === 0 ? 'disabled' : ''}>
                    ← Prev
                </button>
                <span class="page-info">
                    Page ${this.historyPage + 1} of ${totalPages} · ${data.total} total
                </span>
                <button class="page-btn" onclick="app.historyNextPage()" ${this.historyPage >= totalPages - 1 ? 'disabled' : ''}>
                    Next →
                </button>
            </div>
        `;
    },

    historyPrevPage() {
        if (this.historyPage > 0) {
            this.historyPage--;
            this.loadHistory();
        }
    },

    historyNextPage() {
        if (this.historyData && (this.historyPage + 1) * this.historyPageSize < this.historyData.total) {
            this.historyPage++;
            this.loadHistory();
        }
    },

    async viewAuditDetail(auditId) {
        try {
            // Check if we have it in current history data
            let report = null;
            if (this.historyData && this.historyData.audits) {
                report = this.historyData.audits.find(a => a.id === auditId);
            }

            if (!report) {
                // Fetch from API
                const status = await api.getAuditStatus(auditId);
                report = status.result;
            }

            if (report) {
                Components.auditDetailModal(report);
            }
        } catch (error) {
            Components.showToast(`Failed to load audit: ${error.message}`, 'error');
        }
    },

    // --- Analytics View ---
    async loadAnalytics() {
        const container = document.getElementById('analytics-content');
        if (!container) return;

        container.innerHTML = `
            <div class="loading-overlay" style="padding: 48px;">
                <div class="spinner"></div>
                <div class="loading-text">Loading analytics...</div>
            </div>
        `;

        try {
            const stats = await api.getStats();
            this.renderAnalytics(stats);
        } catch (error) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📊</div>
                    <div class="empty-state-text">Failed to load analytics: ${Components.escapeHtml(error.message)}</div>
                </div>
            `;
        }
    },

    renderAnalytics(stats) {
        const container = document.getElementById('analytics-content');
        if (!container) return;

        const trustPercent = stats.avg_trust_score ? (stats.avg_trust_score * 100).toFixed(1) : '0';
        let trustColor = 'var(--contradicted)';
        if (stats.avg_trust_score >= 0.7) trustColor = 'var(--supported)';
        else if (stats.avg_trust_score >= 0.4) trustColor = 'var(--unverifiable)';

        container.innerHTML = `
            <div class="analytics-grid">
                ${Components.metricCard('📊', 'purple', stats.total_audits, 'Total Audits')}
                ${Components.metricCard('🎯', 'green', trustPercent + '%', 'Avg Trust Score')}
                ${Components.metricCard('⚡', 'amber', (stats.avg_latency_ms || 0).toFixed(0) + 'ms', 'Avg Latency')}
                ${Components.metricCard('📋', 'purple', stats.total_claims_processed || 0, 'Total Claims')}
                ${Components.metricCard('✓', 'green', stats.total_supported || 0, 'Total Supported')}
                ${Components.metricCard('✗', 'red', stats.total_contradicted || 0, 'Total Contradicted')}
                ${Components.metricCard('?', 'amber', stats.total_unverifiable || 0, 'Total Unverifiable')}
                ${Components.metricCard('📚', 'purple', stats.corpus_size || 0, 'Corpus Documents')}
            </div>

            <div class="card">
                <div class="card-title">Verdict Distribution</div>
                <div style="display: flex; gap: 8px; margin-top: 16px; height: 24px; border-radius: 12px; overflow: hidden;">
                    ${this.renderDistributionBar(stats)}
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 16px;">
                    <div style="text-align: center;">
                        <div style="color: var(--supported); font-weight: 700; font-size: 1.1rem;">${this.getPercentage(stats.total_supported, stats.total_claims_processed)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Supported</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: var(--contradicted); font-weight: 700; font-size: 1.1rem;">${this.getPercentage(stats.total_contradicted, stats.total_claims_processed)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Contradicted</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: var(--unverifiable); font-weight: 700; font-size: 1.1rem;">${this.getPercentage(stats.total_unverifiable, stats.total_claims_processed)}</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Unverifiable</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderDistributionBar(stats) {
        const total = stats.total_claims_processed || 1;
        const supported = ((stats.total_supported || 0) / total) * 100;
        const contradicted = ((stats.total_contradicted || 0) / total) * 100;
        const unverifiable = ((stats.total_unverifiable || 0) / total) * 100;

        return `
            <div style="width: ${supported}%; background: var(--supported); transition: width 0.8s ease;"></div>
            <div style="width: ${contradicted}%; background: var(--contradicted); transition: width 0.8s ease;"></div>
            <div style="width: ${unverifiable}%; background: var(--unverifiable); transition: width 0.8s ease;"></div>
        `;
    },

    getPercentage(value, total) {
        if (!total || !value) return '0%';
        return ((value / total) * 100).toFixed(1) + '%';
    },
};

// --- Initialize on DOM ready ---
document.addEventListener('DOMContentLoaded', () => app.init());
