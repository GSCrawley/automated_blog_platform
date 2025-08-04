import api from './api';

// Agent API endpoints
export const agentApi = {
  // Agent status and control
  getAgentStatus: () => api.get('/agents/status'),
  
  startAgent: (agentName) => api.post(`/agents/${agentName}/start`),
  
  stopAgent: (agentName) => api.post(`/agents/${agentName}/stop`),
  
  assignAgentToBlog: (agentName, blogInstanceId) => 
    api.post(`/agents/${agentName}/assign`, { blog_instance_id: blogInstanceId }),
  
  // Agent tasks
  getAgentTasks: (agentName) => api.get(`/agents/${agentName}/tasks`),
  
  assignTaskToAgent: (agentName, taskData) => 
    api.post(`/agents/${agentName}/tasks`, taskData),
  
  // Blog instances
  getBlogInstances: () => api.get('/blog-instances'),
  
  createBlogInstance: (blogData) => api.post('/blog-instances', blogData),
  
  updateBlogInstance: (blogId, blogData) => 
    api.put(`/blog-instances/${blogId}`, blogData),
  
  deleteBlogInstance: (blogId) => api.delete(`/blog-instances/${blogId}`),
  
  // Decisions and approvals
  getPendingDecisions: () => api.get('/decisions/pending'),
  
  approveDecision: (decisionId, approvedBy = 'admin') => 
    api.post(`/decisions/${decisionId}/approve`, { approved_by: approvedBy }),
  
  rejectDecision: (decisionId, rejectedBy = 'admin', reason = '') => 
    api.post(`/decisions/${decisionId}/reject`, { 
      rejected_by: rejectedBy, 
      reason: reason 
    }),
  
  // Market data
  getMarketData: (nicheId = null, limit = 10) => {
    const params = new URLSearchParams();
    if (nicheId) params.append('niche_id', nicheId);
    if (limit) params.append('limit', limit);
    
    return api.get(`/market-data?${params.toString()}`);
  },
  
  // System health
  getSystemHealth: () => api.get('/system/health'),
  
  // Agent coordination
  coordinateContentGeneration: (blogInstanceId, contentType = 'article', priority = 5) =>
    api.post('/agents/orchestrator/coordinate', {
      blog_instance_id: blogInstanceId,
      content_type: contentType,
      priority: priority
    }),
  
  // Market research requests
  requestMarketResearch: (niche, productCategory = null) =>
    api.post('/agents/market_analytics/research', {
      niche: niche,
      product_category: productCategory
    }),
  
  // Agent performance metrics
  getAgentMetrics: (agentName, timeframe = '24h') =>
    api.get(`/agents/${agentName}/metrics?timeframe=${timeframe}`),
  
  // Workflow management
  getActiveWorkflows: () => api.get('/workflows/active'),
  
  getWorkflowStatus: (workflowId) => api.get(`/workflows/${workflowId}/status`),
  
  cancelWorkflow: (workflowId) => api.post(`/workflows/${workflowId}/cancel`),
  
  // Agent configuration
  getAgentConfig: (agentName) => api.get(`/agents/${agentName}/config`),
  
  updateAgentConfig: (agentName, config) =>
    api.put(`/agents/${agentName}/config`, config),
  
  // Bulk operations
  startAllAgents: () => api.post('/agents/bulk/start'),
  
  stopAllAgents: () => api.post('/agents/bulk/stop'),
  
  restartAllAgents: () => api.post('/agents/bulk/restart'),
  
  // Monitoring and alerts
  getSystemAlerts: () => api.get('/system/alerts'),
  
  acknowledgeAlert: (alertId) => api.post(`/system/alerts/${alertId}/acknowledge`),
  
  // Agent logs
  getAgentLogs: (agentName, limit = 100, level = 'INFO') =>
    api.get(`/agents/${agentName}/logs?limit=${limit}&level=${level}`),
  
  // Statistics
  getSystemStatistics: () => api.get('/system/statistics'),
  
  getAgentStatistics: (agentName) => api.get(`/agents/${agentName}/statistics`)
};

export default agentApi;