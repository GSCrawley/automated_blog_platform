/**
 * Centralized API service for making requests to the backend.
 *
 * PR #4 expanded the public surface: typed wrappers (JSDoc) for the new
 * Article filter/pagination params, PATCH endpoints, the stage-outputs
 * endpoint, and the cost-aware dashboard stats. The shape of every wrapper
 * mirrors the backend's `{success, ...}` response envelope.
 */

// Base API URL - should be configurable based on environment
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api';

/**
 * Generic request function with error handling.
 *
 * @param {string} endpoint API path beginning with `/` (no base URL).
 * @param {RequestInit} [options] Standard fetch options.
 * @returns {Promise<Object>} Parsed JSON body. Throws on non-2xx with the
 *   server-provided `error` string when available.
 */
const request = async (endpoint, options = {}) => {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'An error occurred');
    }

    return data;
  } catch (error) {
    console.error(`API Error (${endpoint}):`, error);
    throw error;
  }
};

/**
 * Build a query string from a sparse params object. Skips null/undefined/''.
 *
 * @param {Object<string, *>} params
 * @returns {string} URL-encoded query string with leading `?`, or `''`.
 */
const qs = (params) => {
  if (!params) return '';
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') usp.append(k, v);
  });
  const s = usp.toString();
  return s ? `?${s}` : '';
};

/**
 * @typedef {Object} ArticleListFilters
 * @property {string} [status]            'draft' | 'published' | 'archived' | ...
 * @property {string} [editorial_verdict] 'PUBLISH' | 'REJECT' | 'PENDING'
 * @property {string} [current_stage]     'stage_0' | ... | 'awaiting_human_review' | 'halted_budget'
 * @property {number} [niche_id]
 * @property {number} [limit]             default 100, max 500
 * @property {number} [offset]            default 0
 * @property {1}      [include_archived]  pass `1` to include archived rows
 */

/**
 * @typedef {Object} StageOutputs
 * @property {Object|null} research_report
 * @property {Object|null} strategy
 * @property {Object|null} draft_sections
 * @property {Object|null} monetization_map
 * @property {Object|null} editorial_verdict
 */

/**
 * @typedef {Object} DashboardStats
 * @property {number} products
 * @property {number} articles
 * @property {number} niches
 * @property {number} awaiting_review
 * @property {Object<string, number>} by_stage   { current_stage: count }
 * @property {Object<string, number>} by_verdict { editorial_verdict: count }
 * @property {{month: string, spent_usd: number, cap_usd: number, pct_used: number}} cost
 */

/** Blog (articles, products, niches, dashboard stats) endpoints. */
export const blogApi = {
  // ---- Products ----------------------------------------------------------
  getProducts: () => request('/blog/products'),
  getProduct: (id) => request(`/blog/products/${id}`),
  createProduct: (product) => request('/blog/products', {
    method: 'POST', body: JSON.stringify(product),
  }),
  updateProduct: (id, product) => request(`/blog/products/${id}`, {
    method: 'PUT', body: JSON.stringify(product),
  }),
  /** Partial update — only fields present in `product` are written. */
  patchProduct: (id, product) => request(`/blog/products/${id}`, {
    method: 'PATCH', body: JSON.stringify(product),
  }),
  deleteProduct: (id) => request(`/blog/products/${id}`, { method: 'DELETE' }),

  // ---- Articles ----------------------------------------------------------
  /**
   * List articles with optional filters + pagination.
   * @param {ArticleListFilters} [filters]
   */
  getArticles: (filters) => request(`/blog/articles${qs(filters)}`),
  getArticle: (id) => request(`/blog/articles/${id}`),
  /**
   * Stage-output bundle (PR #4): the four PR #3 JSON columns parsed +
   * cost / verdict / blueprint_id / current_stage metadata in one call.
   * @returns {Promise<{success: boolean, stage_outputs: StageOutputs}>}
   */
  getArticleStageOutputs: (id) => request(`/blog/articles/${id}/stage-outputs`),
  createArticle: (article) => request('/blog/articles', {
    method: 'POST', body: JSON.stringify(article),
  }),
  generateArticle: (productId) => request('/blog/generate-article', {
    method: 'POST', body: JSON.stringify({ product_id: productId }),
  }),
  updateArticle: (id, article) => request(`/blog/articles/${id}`, {
    method: 'PUT', body: JSON.stringify(article),
  }),
  /** Partial update — same field allow-list as PUT, only writes what's sent. */
  patchArticle: (id, article) => request(`/blog/articles/${id}`, {
    method: 'PATCH', body: JSON.stringify(article),
  }),
  /**
   * Soft-delete (sets `status='archived'`). Pass `{hard: true}` to actually
   * drop the row — useful for tests, not the dashboard.
   */
  deleteArticle: (id, opts = {}) => request(
    `/blog/articles/${id}${opts.hard ? '?hard=1' : ''}`,
    { method: 'DELETE' }
  ),
  conversationalEdit: (id, data) => request(`/blog/articles/${id}/conversational-edit`, {
    method: 'POST', body: JSON.stringify(data),
  }),
  getEditorReview: (articleId) => request(`/agents/editorial/review/${articleId}`),
  triggerEditorReview: (articleId) => request(`/agents/editorial/review/${articleId}`, {
    method: 'POST',
  }),

  // ---- Keyword research / trending --------------------------------------
  researchKeywords: (topic) => request('/blog/keyword-research', {
    method: 'POST', body: JSON.stringify({ topic }),
  }),
  getTrendingProducts: (limit = 10) => request(`/blog/trending-products?limit=${limit}`),

  // ---- Niches ------------------------------------------------------------
  getNiches: () => request('/blog/niches'),
  getNiche: (id) => request(`/blog/niches/${id}`),
  createNiche: (niche) => request('/blog/niches', {
    method: 'POST', body: JSON.stringify(niche),
  }),
  updateNiche: (id, niche) => request(`/blog/niches/${id}`, {
    method: 'PUT', body: JSON.stringify(niche),
  }),
  /** Partial update — same field allow-list as PUT, only writes what's sent. */
  patchNiche: (id, niche) => request(`/blog/niches/${id}`, {
    method: 'PATCH', body: JSON.stringify(niche),
  }),
  deleteNiche: (id) => request(`/blog/niches/${id}`, { method: 'DELETE' }),
  getNichePipelineStatus: (id) => request(`/blog/niches/${id}/pipeline-status`),
  runNichePipeline: (id) => request(`/blog/niches/${id}/run-pipeline`, {
    method: 'POST',
  }),

  // ---- Dashboard ---------------------------------------------------------
  /**
   * PR #4 dashboard stats. Carries `by_stage`, `by_verdict`,
   * `awaiting_review`, and a `cost` panel for the current month.
   * @param {{niche_id?: number}} [filters]
   * @returns {Promise<{success: boolean, stats: DashboardStats}>}
   */
  getDashboardStats: (filters) => request(`/blog/dashboard/stats${qs(filters)}`),
};

/** PR #3 budget status. */
export const budgetApi = {
  /** Monthly cap vs spent + per-niche breakdown. */
  getStatus: () => request('/budget/status'),
};

/**
 * @typedef {Object} ReviewQueueItem
 * @property {number} id
 * @property {string} title
 * @property {number} niche_id
 * @property {string} niche_name
 * @property {('PUBLISH'|'REJECT'|'PENDING')} editorial_verdict
 * @property {string} current_stage
 * @property {number} word_count
 * @property {string} cost_usd
 * @property {string} blueprint_id
 * @property {string} updated_at
 * @property {{verdict?: string, blueprint_id?: string, axis_scores?: Object}} editorial_report_summary
 */

/**
 * @typedef {Object} GhostDriftReport
 * @property {Object} local                  Headless-contract from local DB
 * @property {Object} ghost                  Subset of fields pulled from Ghost
 * @property {boolean} drift_detected
 * @property {string[]} diverging_fields     ['title' | 'html' | 'meta_description' | 'tags']
 * @property {string} local_hash
 * @property {string} ghost_hash
 * @property {string?} last_sync_hash
 */

/**
 * PR #6 — human-in-the-loop review + publish surface. Every Ghost write
 * goes through here; the legacy ``publisherApi.publish`` is preserved for
 * tests but deprecated for UI use.
 */
export const reviewApi = {
  /**
   * @param {{niche_id?: number, editorial_verdict?: 'PUBLISH'|'REJECT', limit?: number, offset?: number, sort?: 'updated_at'|'cost_usd'}} [filters]
   * @returns {Promise<{success: boolean, articles: ReviewQueueItem[], total: number, limit: number, offset: number}>}
   */
  getQueue: (filters) => request(`/review/queue${qs(filters)}`),

  /** Full payload the review screen needs in one round-trip. */
  getArticle: (id) => request(`/review/${id}`),

  /**
   * Local-only edit before publish. Accepts any subset of:
   * title, slug, content, sections, summary, meta_description, keywords,
   * calls_to_action, meta.feature_image, meta.meta_title.
   * @returns {Promise<Object>} Same shape as ``getArticle``.
   */
  patch: (id, body) => request(`/review/${id}`, {
    method: 'PATCH', body: JSON.stringify(body),
  }),

  /** Human-triggered publish to Ghost. Refuses if verdict !== 'PUBLISH'. */
  publish: (id) => request(`/review/${id}/publish`, { method: 'POST' }),

  /** Set Ghost post to status='draft'. */
  unpublish: (id) => request(`/review/${id}/unpublish`, { method: 'POST' }),

  /**
   * Pull live Ghost state and compute drift against local.
   * @returns {Promise<GhostDriftReport & {success: boolean}>}
   */
  ghostSnapshot: (id) => request(`/review/${id}/ghost`),

  /** Overwrite local with Ghost's current version (snapshots local first). */
  pullFromGhost: (id) => request(`/review/${id}/pull-from-ghost`, { method: 'POST' }),

  /** Push local edits to Ghost (snapshots Ghost first). Verdict-gated. */
  pushToGhost: (id) => request(`/review/${id}/push-to-ghost`, { method: 'POST' }),
};

/** Publisher (PR #1). */
export const publisherApi = {
  health: () => request('/publisher/health'),
  publish: (articleId) => request(`/publisher/publish/${articleId}`, { method: 'POST' }),
  draft: (articleId) => request(`/publisher/draft/${articleId}`, { method: 'POST' }),
};

/** User API endpoints. */
export const userApi = {
  getUsers: () => request('/users'),
  getUser: (id) => request(`/users/${id}`),
  createUser: (user) => request('/users', { method: 'POST', body: JSON.stringify(user) }),
  updateUser: (id, user) => request(`/users/${id}`, { method: 'PUT', body: JSON.stringify(user) }),
  deleteUser: (id) => request(`/users/${id}`, { method: 'DELETE' }),
};

/** Automation API endpoints. */
export const automationApi = {
  getSchedulerStatus: () => request('/automation/scheduler/status'),
  startScheduler: () => request('/automation/scheduler/start', { method: 'POST' }),
  stopScheduler: () => request('/automation/scheduler/stop', { method: 'POST' }),
  triggerContentGeneration: () => request('/automation/scheduler/trigger-content-generation', {
    method: 'POST',
  }),
  triggerContentUpdate: () => request('/automation/scheduler/trigger-content-update', {
    method: 'POST',
  }),
};

/**
 * Analytics API endpoints (placeholder until PR #7 wires real GSC + affiliate
 * dashboards).
 */
export const analyticsApi = {
  getOverview: () => request('/analytics/overview'),
  getTopArticles: () => request('/analytics/top-articles'),
  getRevenueByNiche: () => request('/analytics/revenue-by-niche'),
  getTrafficSources: () => request('/analytics/traffic-sources'),
};

/**
 * PR #7 — Blueprint proposals + per-article improvement proposals.
 */
export const proposalsApi = {
  /**
   * @param {{status?: 'pending'|'accepted'|'rejected', niche_id?: number, limit?: number, offset?: number}} [filters]
   */
  list: (filters) => request(`/proposals/${qs(filters)}`),
  get: (id) => request(`/proposals/${id}`),
  accept: (id) => request(`/proposals/${id}/accept`, { method: 'POST' }),
  reject: (id, body = {}) => request(`/proposals/${id}/reject`, {
    method: 'POST', body: JSON.stringify(body),
  }),
  generate: (nicheId, opts = {}) => request(`/proposals/generate/${nicheId}`, {
    method: 'POST', body: JSON.stringify(opts),
  }),

  // Per-article improvement proposals
  getImprovements: (articleId, filters) =>
    request(`/review/${articleId}/improvements${qs(filters)}`),
  generateImprovements: (articleId) =>
    request(`/review/${articleId}/improvements/generate`, { method: 'POST' }),
  applyImprovement: (articleId, proposalId) =>
    request(`/review/${articleId}/improvements/${proposalId}/apply`, { method: 'POST' }),
  dismissImprovement: (articleId, proposalId, reason = '') =>
    request(`/review/${articleId}/improvements/${proposalId}/dismiss`, {
      method: 'POST', body: JSON.stringify({ reason }),
    }),
};

export default {
  blogApi,
  budgetApi,
  publisherApi,
  reviewApi,
  proposalsApi,
  userApi,
  automationApi,
  analyticsApi,
};
