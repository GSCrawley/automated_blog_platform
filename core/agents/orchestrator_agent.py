import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent, AgentStatus, DecisionImpact

class OrchestratorAgent(BaseAgent):
    """
    Central coordinator agent that manages all blog instances,
    coordinates agent assignments, and handles major decision approvals.
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        super().__init__("orchestrator", "orchestrator", redis_host, redis_port)
        
        # Track all registered agents
        self.registered_agents = {}
        
        # Track blog instances and their assigned agents
        self.blog_instances = {}
        
        # Approval queue for high-impact decisions
        self.approval_queue = []
        
        # Task queue for coordinating work
        self.task_queue = []
        
        # Performance monitoring
        self.system_metrics = {
            'total_tasks_completed': 0,
            'total_decisions_made': 0,
            'average_response_time': 0.0,
            'system_uptime': datetime.utcnow().isoformat()
        }
        
        self.logger.info("Orchestrator Agent initialized")
    
    def get_capabilities(self) -> List[str]:
        """Return list of orchestrator capabilities"""
        return [
            'agent_coordination',
            'task_delegation',
            'decision_approval',
            'system_monitoring',
            'blog_instance_management',
            'resource_allocation'
        ]
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrator-specific tasks"""
        task_type = task_data.get('type')
        
        if task_type == 'register_agent':
            return self.register_agent(task_data)
        elif task_type == 'assign_agent_to_blog':
            return self.assign_agent_to_blog(task_data)
        elif task_type == 'coordinate_content_generation':
            return self.coordinate_content_generation(task_data)
        elif task_type == 'system_health_check':
            return self.perform_system_health_check()
        elif task_type == 'process_approval_queue':
            return self.process_approval_queue()
        else:
            return {'error': f'Unknown task type: {task_type}'}
    
    def register_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new agent with the orchestrator"""
        agent_name = agent_data.get('agent_name')
        agent_type = agent_data.get('agent_type')
        capabilities = agent_data.get('capabilities', [])
        
        if not agent_name or not agent_type:
            return {'error': 'Agent name and type are required'}
        
        self.registered_agents[agent_name] = {
            'agent_type': agent_type,
            'capabilities': capabilities,
            'status': 'active',
            'last_seen': datetime.utcnow().isoformat(),
            'assigned_blogs': [],
            'performance_metrics': {}
        }
        
        self.logger.info(f"Agent {agent_name} ({agent_type}) registered successfully")
        
        # Broadcast agent registration to all agents
        self.broadcast_message({
            'type': 'agent_registered',
            'agent_name': agent_name,
            'agent_type': agent_type,
            'capabilities': capabilities
        })
        
        return {'status': 'success', 'message': f'Agent {agent_name} registered'}
    
    def assign_agent_to_blog(self, assignment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign an agent to a specific blog instance"""
        agent_name = assignment_data.get('agent_name')
        blog_instance_id = assignment_data.get('blog_instance_id')
        
        if agent_name not in self.registered_agents:
            return {'error': f'Agent {agent_name} not found'}
        
        # Add blog to agent's assigned blogs
        if blog_instance_id not in self.registered_agents[agent_name]['assigned_blogs']:
            self.registered_agents[agent_name]['assigned_blogs'].append(blog_instance_id)
        
        # Track blog instance assignments
        if blog_instance_id not in self.blog_instances:
            self.blog_instances[blog_instance_id] = {'assigned_agents': []}
        
        if agent_name not in self.blog_instances[blog_instance_id]['assigned_agents']:
            self.blog_instances[blog_instance_id]['assigned_agents'].append(agent_name)
        
        # Notify the agent of the assignment
        self.send_message(agent_name, {
            'type': 'blog_assignment',
            'blog_instance_id': blog_instance_id,
            'assignment_time': datetime.utcnow().isoformat()
        })
        
        self.logger.info(f"Agent {agent_name} assigned to blog {blog_instance_id}")
        
        return {
            'status': 'success',
            'message': f'Agent {agent_name} assigned to blog {blog_instance_id}'
        }
    
    def coordinate_content_generation(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate content generation across multiple agents"""
        blog_instance_id = request_data.get('blog_instance_id')
        content_type = request_data.get('content_type', 'article')
        priority = request_data.get('priority', 5)
        
        # Find appropriate agents for content generation
        content_agents = self.find_agents_by_capability('content_generation')
        market_agents = self.find_agents_by_capability('market_research')
        seo_agents = self.find_agents_by_capability('seo_optimization')
        
        if not content_agents:
            return {'error': 'No content generation agents available'}
        
        # Create coordinated workflow
        workflow_id = f"content_gen_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Market research
        if market_agents:
            market_task = {
                'type': 'task_assignment',
                'task_id': f"{workflow_id}_market",
                'task_type': 'market_research',
                'blog_instance_id': blog_instance_id,
                'priority': priority,
                'assigned_by': self.agent_name,
                'workflow_id': workflow_id
            }
            self.send_message(market_agents[0], market_task)
        
        # Step 2: SEO research (can run in parallel with market research)
        if seo_agents:
            seo_task = {
                'type': 'task_assignment',
                'task_id': f"{workflow_id}_seo",
                'task_type': 'keyword_research',
                'blog_instance_id': blog_instance_id,
                'priority': priority,
                'assigned_by': self.agent_name,
                'workflow_id': workflow_id
            }
            self.send_message(seo_agents[0], seo_task)
        
        # Step 3: Content generation (will wait for research results)
        content_task = {
            'type': 'task_assignment',
            'task_id': f"{workflow_id}_content",
            'task_type': 'content_generation',
            'content_type': content_type,
            'blog_instance_id': blog_instance_id,
            'priority': priority,
            'assigned_by': self.agent_name,
            'workflow_id': workflow_id,
            'depends_on': [f"{workflow_id}_market", f"{workflow_id}_seo"]
        }
        self.send_message(content_agents[0], content_task)
        
        self.logger.info(f"Content generation workflow {workflow_id} initiated")
        
        return {
            'status': 'success',
            'workflow_id': workflow_id,
            'message': 'Content generation workflow initiated'
        }
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """Find all agents that have a specific capability"""
        matching_agents = []
        
        for agent_name, agent_info in self.registered_agents.items():
            if capability in agent_info.get('capabilities', []):
                if agent_info.get('status') == 'active':
                    matching_agents.append(agent_name)
        
        return matching_agents
    
    def perform_system_health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive system health check"""
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'agents': {},
            'blog_instances': {},
            'system_metrics': self.system_metrics
        }
        
        # Check agent health
        for agent_name, agent_info in self.registered_agents.items():
            # Request status from each agent
            self.send_message(agent_name, {'type': 'status_request'})
            
            # Check if agent has been seen recently
            last_seen = datetime.fromisoformat(agent_info['last_seen'])
            time_since_seen = datetime.utcnow() - last_seen
            
            if time_since_seen > timedelta(minutes=10):
                agent_status = 'unresponsive'
                health_report['overall_status'] = 'degraded'
            else:
                agent_status = agent_info.get('status', 'unknown')
            
            health_report['agents'][agent_name] = {
                'status': agent_status,
                'last_seen': agent_info['last_seen'],
                'assigned_blogs': len(agent_info.get('assigned_blogs', [])),
                'capabilities': agent_info.get('capabilities', [])
            }
        
        # Check blog instance health
        for blog_id, blog_info in self.blog_instances.items():
            health_report['blog_instances'][blog_id] = {
                'assigned_agents': len(blog_info.get('assigned_agents', [])),
                'status': 'active'  # This would be determined by actual blog health checks
            }
        
        self.logger.info("System health check completed")
        return health_report
    
    def process_approval_queue(self) -> Dict[str, Any]:
        """Process pending approval requests"""
        processed_count = 0
        
        for approval_request in self.approval_queue[:]:  # Copy list to avoid modification during iteration
            # For now, we'll auto-approve low-risk decisions and log high-risk ones
            impact_level = approval_request.get('impact_level', 'low')
            
            if impact_level == 'low':
                # Auto-approve low-impact decisions
                self.approve_decision(approval_request, 'auto_approved')
                self.approval_queue.remove(approval_request)
                processed_count += 1
            elif impact_level == 'medium':
                # Medium impact decisions need user approval
                self.logger.warning(f"Medium impact decision requires approval: {approval_request}")
            else:
                # High impact decisions definitely need user approval
                self.logger.critical(f"High impact decision requires immediate approval: {approval_request}")
        
        return {
            'status': 'success',
            'processed_count': processed_count,
            'pending_count': len(self.approval_queue)
        }
    
    def approve_decision(self, decision: Dict[str, Any], approved_by: str):
        """Approve a decision and notify the requesting agent"""
        decision['approval_status'] = 'approved'
        decision['approved_by'] = approved_by
        decision['approved_at'] = datetime.utcnow().isoformat()
        
        # Notify the requesting agent
        requesting_agent = decision.get('agent_name')
        if requesting_agent:
            self.send_message(requesting_agent, {
                'type': 'decision_approved',
                'decision': decision
            })
        
        self.logger.info(f"Decision approved: {decision.get('decision_type')} by {approved_by}")
    
    def handle_incoming_message(self, message: Dict[str, Any]):
        """Handle incoming messages with orchestrator-specific logic"""
        super().handle_incoming_message(message)
        
        data = message.get('data', {})
        message_type = data.get('type')
        sender = message.get('from')
        
        if message_type == 'approval_request':
            self.handle_approval_request(data, sender)
        elif message_type == 'task_result':
            self.handle_task_result(data, sender)
        elif message_type == 'agent_status_update':
            self.handle_agent_status_update(data, sender)
    
    def handle_approval_request(self, request_data: Dict[str, Any], sender: str):
        """Handle approval requests from other agents"""
        decision = request_data.get('decision', {})
        decision['requesting_agent'] = sender
        decision['received_at'] = datetime.utcnow().isoformat()
        
        self.approval_queue.append(decision)
        self.logger.info(f"Approval request received from {sender}: {decision.get('decision_type')}")
    
    def handle_task_result(self, result_data: Dict[str, Any], sender: str):
        """Handle task completion results from other agents"""
        task_id = result_data.get('task_id')
        workflow_id = result_data.get('workflow_id')
        
        self.logger.info(f"Task {task_id} completed by {sender}")
        
        # Update system metrics
        self.system_metrics['total_tasks_completed'] += 1
        
        # If this is part of a workflow, check if we can proceed to next steps
        if workflow_id:
            self.check_workflow_progress(workflow_id, task_id, result_data)
    
    def handle_agent_status_update(self, status_data: Dict[str, Any], sender: str):
        """Handle status updates from agents"""
        if sender in self.registered_agents:
            self.registered_agents[sender]['last_seen'] = datetime.utcnow().isoformat()
            self.registered_agents[sender]['status'] = status_data.get('status', 'active')
            self.registered_agents[sender]['performance_metrics'] = status_data.get('performance_metrics', {})
    
    def check_workflow_progress(self, workflow_id: str, completed_task_id: str, result_data: Dict[str, Any]):
        """Check if a workflow can proceed to the next step"""
        # This is a simplified workflow management system
        # In a real implementation, this would be more sophisticated
        self.logger.info(f"Workflow {workflow_id} progress: {completed_task_id} completed")
    
    def start_monitoring_loop(self):
        """Start the main monitoring and coordination loop"""
        self.logger.info("Starting orchestrator monitoring loop")
        
        while self.status != AgentStatus.ERROR:
            try:
                # Process approval queue
                self.process_approval_queue()
                
                # Perform periodic health checks
                if datetime.utcnow().minute % 5 == 0:  # Every 5 minutes
                    self.perform_system_health_check()
                
                # Listen for messages
                self.listen_for_messages()
                
                # Brief pause to prevent excessive CPU usage
                time.sleep(1)
                
            except KeyboardInterrupt:
                self.logger.info("Orchestrator shutdown requested")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                self.status = AgentStatus.ERROR
        
        self.shutdown()