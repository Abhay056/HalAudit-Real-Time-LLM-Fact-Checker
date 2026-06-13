/**
 * HalAudit API Client
 * Fetch-based client with error handling, retries, and rate limit awareness.
 */

const API_BASE = window.location.origin + '/api/v1';

class HalAuditAPI {
    constructor(baseUrl = API_BASE) {
        this.baseUrl = baseUrl;
        this.maxRetries = 2;
        this.retryDelay = 1000;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        };

        let lastError;
        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                const response = await fetch(url, config);

                // Handle rate limiting
                if (response.status === 429) {
                    const retryAfter = response.headers.get('Retry-After');
                    const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : this.retryDelay * (attempt + 1);
                    console.warn(`Rate limited. Retrying in ${waitTime}ms...`);
                    await this.sleep(waitTime);
                    continue;
                }

                // Store rate limit info
                const rateInfo = {
                    limit: response.headers.get('X-RateLimit-Limit'),
                    remaining: response.headers.get('X-RateLimit-Remaining'),
                    reset: response.headers.get('X-RateLimit-Reset'),
                };

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new APIError(
                        errorData.detail || `HTTP ${response.status}`,
                        response.status,
                        rateInfo
                    );
                }

                const data = await response.json();
                data._rateLimit = rateInfo;
                return data;

            } catch (error) {
                lastError = error;
                if (error instanceof APIError && error.status !== 429 && error.status < 500) {
                    throw error; // Don't retry client errors
                }
                if (attempt < this.maxRetries) {
                    await this.sleep(this.retryDelay * (attempt + 1));
                }
            }
        }

        throw lastError;
    }

    // --- Audit Endpoints ---

    async auditText(text, options = {}) {
        return this.request('/audit', {
            method: 'POST',
            body: JSON.stringify({ text, options }),
        });
    }

    async auditTextAsync(text, options = {}) {
        return this.request('/audit/async', {
            method: 'POST',
            body: JSON.stringify({ text, options }),
        });
    }

    async getAuditStatus(jobId) {
        return this.request(`/audit/${jobId}`);
    }

    async generateAndAudit(prompt, options = {}) {
        return this.request('/generate-and-audit', {
            method: 'POST',
            body: JSON.stringify({ prompt, options }),
        });
    }

    // --- History ---

    async getAuditHistory(params = {}) {
        const query = new URLSearchParams();
        if (params.limit) query.set('limit', params.limit);
        if (params.offset !== undefined) query.set('offset', params.offset);
        if (params.min_trust_score !== undefined) query.set('min_trust_score', params.min_trust_score);
        if (params.max_trust_score !== undefined) query.set('max_trust_score', params.max_trust_score);
        if (params.has_contradictions !== undefined) query.set('has_contradictions', params.has_contradictions);

        const queryStr = query.toString();
        return this.request(`/audit/history${queryStr ? '?' + queryStr : ''}`);
    }

    // --- Corpus ---

    async ingestCorpus(texts, source = 'manual') {
        return this.request('/corpus/ingest', {
            method: 'POST',
            body: JSON.stringify({ texts, source }),
        });
    }

    // --- Health & Stats ---

    async healthCheck() {
        return this.request('/health');
    }

    async getStats() {
        return this.request('/stats');
    }

    // --- Utilities ---

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Poll for async job result with exponential backoff.
     */
    async pollForResult(jobId, { maxAttempts = 60, interval = 1000, onStatus } = {}) {
        for (let i = 0; i < maxAttempts; i++) {
            const status = await this.getAuditStatus(jobId);

            if (onStatus) onStatus(status);

            if (status.status === 'completed' && status.result) {
                return status.result;
            }

            if (status.status === 'failed') {
                throw new APIError(status.error || 'Job failed', 500);
            }

            // Exponential backoff: 1s, 1.5s, 2.25s... capped at 10s
            const waitTime = Math.min(interval * Math.pow(1.5, i), 10000);
            await this.sleep(waitTime);
        }

        throw new APIError('Polling timeout — job took too long', 408);
    }
}

class APIError extends Error {
    constructor(message, status, rateLimit) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.rateLimit = rateLimit;
    }
}

// Export singleton
const api = new HalAuditAPI();
