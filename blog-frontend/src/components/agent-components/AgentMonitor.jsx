import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Refresh,
  Warning,
  CheckCircle,
  Error,
  Info
} from '@mui/icons-material';
import { agentApi } from '../../services/agentApi';

const AgentMonitor = () => {
  const [agents, setAgents] = useState({});
  const [systemHealth, setSystemHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [agentDetailsOpen, setAgentDetailsOpen] = useState(false);

  useEffect(() => {
    fetchAgentStatus();
    fetchSystemHealth();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      fetchAgentStatus();
      fetchSystemHealth();
    }, 10000); // Update every 10 seconds
    
    return () => clearInterval(interval);
  }, []);

  const fetchAgentStatus = async () => {
    try {
      const response = await agentApi.getAgentStatus();
      setAgents(response.agents || {});
      setError(null);
    } catch (err) {
      setError('Failed to fetch agent status');
      console.error('Error fetching agent status:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const response = await agentApi.getSystemHealth();
      setSystemHealth(response.health);
    } catch (err) {
      console.error('Error fetching system health:', err);
    }
  };

  const handleAgentAction = async (agentName, action) => {
    try {
      if (action === 'start') {
        await agentApi.startAgent(agentName);
      } else if (action === 'stop') {
        await agentApi.stopAgent(agentName);
      }
      
      // Refresh agent status
      fetchAgentStatus();
    } catch (err) {
      setError(`Failed to ${action} agent ${agentName}`);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'idle':
        return 'info';
      case 'error':
        return 'error';
      case 'paused':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle color="success" />;
      case 'idle':
        return <Info color="info" />;
      case 'error':
        return <Error color="error" />;
      case 'paused':
        return <Warning color="warning" />;
      default:
        return null;
    }
  };

  const handleAgentDetails = (agentName) => {
    setSelectedAgent(agents[agentName]);
    setAgentDetailsOpen(true);
  };

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography variant="h6" sx={{ mt: 2, textAlign: 'center' }}>
          Loading agent status...
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Agent Monitor
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* System Health Overview */}
      {systemHealth && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Health
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color={systemHealth.overall_status === 'healthy' ? 'success.main' : 'error.main'}>
                    {systemHealth.overall_status === 'healthy' ? '✓' : '⚠'}
                  </Typography>
                  <Typography variant="subtitle2">
                    Overall Status: {systemHealth.overall_status}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {systemHealth.metrics?.active_agents || 0}
                  </Typography>
                  <Typography variant="subtitle2">
                    Active Agents
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="info.main">
                    {systemHealth.metrics?.total_blog_instances || 0}
                  </Typography>
                  <Typography variant="subtitle2">
                    Blog Instances
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="warning.main">
                    {systemHealth.metrics?.pending_approvals || 0}
                  </Typography>
                  <Typography variant="subtitle2">
                    Pending Approvals
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Agent Status Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Agent Status
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={() => {
                fetchAgentStatus();
                fetchSystemHealth();
              }}
            >
              Refresh
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Agent Name</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Last Seen</TableCell>
                  <TableCell>Assigned Blogs</TableCell>
                  <TableCell>Performance</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {Object.entries(agents).map(([agentName, agentData]) => (
                  <TableRow key={agentName}>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {getStatusIcon(agentData.status)}
                        <Typography variant="body2" sx={{ ml: 1 }}>
                          {agentName}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={agentData.status}
                        color={getStatusColor(agentData.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {agentData.last_seen ? new Date(agentData.last_seen).toLocaleString() : 'Never'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {agentData.assigned_blogs?.length || 0} blogs
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        onClick={() => handleAgentDetails(agentName)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {agentData.status !== 'active' && (
                          <Button
                            size="small"
                            startIcon={<PlayArrow />}
                            onClick={() => handleAgentAction(agentName, 'start')}
                            color="success"
                          >
                            Start
                          </Button>
                        )}
                        {agentData.status === 'active' && (
                          <Button
                            size="small"
                            startIcon={<Stop />}
                            onClick={() => handleAgentAction(agentName, 'stop')}
                            color="error"
                          >
                            Stop
                          </Button>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {Object.keys(agents).length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No agents found. The agent system may not be running.
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Agent Details Dialog */}
      <Dialog
        open={agentDetailsOpen}
        onClose={() => setAgentDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Agent Details: {selectedAgent?.agent_name || 'Unknown'}
        </DialogTitle>
        <DialogContent>
          {selectedAgent && (
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Status
                </Typography>
                <Chip
                  label={selectedAgent.status}
                  color={getStatusColor(selectedAgent.status)}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Last Seen
                </Typography>
                <Typography variant="body2" sx={{ mb: 2 }}>
                  {selectedAgent.last_seen ? new Date(selectedAgent.last_seen).toLocaleString() : 'Never'}
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Performance Metrics
                </Typography>
                <Box sx={{ bgcolor: 'grey.100', p: 2, borderRadius: 1 }}>
                  <pre style={{ margin: 0, fontSize: '12px' }}>
                    {JSON.stringify(selectedAgent.performance_metrics || {}, null, 2)}
                  </pre>
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Assigned Blogs
                </Typography>
                <Typography variant="body2">
                  {selectedAgent.assigned_blogs?.length || 0} blog instances assigned
                </Typography>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAgentDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentMonitor;