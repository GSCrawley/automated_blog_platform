import json
import logging
import redis
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    ERROR = "error"
    PAUSED = "paused"

class DecisionImpact(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BaseAgent(ABC):
    """
    Base class for all agents in the system.
    Provides common functionality for communication, state management, and decision making.
    """
    
    def __init__(self, agent_name: str, agent_type: str, redis_host: str = 'localhost', redis_port: int = 6379):
        self.agent_name = agent_name
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.state_data = {}
        self.performance_metrics = {}
        
        # Set up logging
        self.logger = logging.getLogger(f"{agent_type}.{agent_name}")
        
        # Set up Redis for inter-agent communication
        try:
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis_client.ping()  # Test connection
        except redis.ConnectionError:
            self.logger.error("Failed to connect to Redis. Agent communication will be limited.")
            self.redis_client = None
        
        # Subscribe to agent communication channels
        self.setup_communication_channels()
        
        self.logger.info(f"Agent {self.agent_name} initialized")
    
    def setup_communication_channels(self):
        """
        Set up Redis pub/sub channels for agent communication
        """
        if self.redis_client:
            self.pubsub = self.redis_client.pubsub()
            # Subscribe to global agent channel and agent-specific channel
            self.pubsub.subscribe(f'agents.global')
            self.pubsub.subscribe(f'agents.{self.agent_name}')
    
    @abstractmethod
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific task assigned to this agent.
        Must be implemented by each agent type.
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return a list of capabilities this agent can perform.
        Must be implemented by each agent type.
        """
        pass
    
    def update_state(self, new_state: Dict[str, Any]):
        """
        Update the agent's internal state
        """
        self.state_data.update(new_state)
        self.state_data['last_updated'] = datetime.utcnow().isoformat()
        
        # Persist state to database if needed
        self.persist_state()
    
    def persist_state(self):
        """
        Persist agent state to database
        """
        # This would interact with the AgentState model
        # Implementation depends on database connection setup
        pass
    
    def send_message(self, target_agent: str, message: Dict[str, Any]):
        """
        Send a message to another agent
        """
        if not self.redis_client:
            self.logger.error("Cannot send message: Redis not available")
            return False
        
        message_data = {
            'from': self.agent_name,
            'to': target_agent,
            'timestamp': datetime.utcnow().isoformat(),
            'data': message
        }
        
        try:
            self.redis_client.publish(f'agents.{target_agent}', json.dumps(message_data))
            self.logger.info(f"Message sent to {target_agent}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send message to {target_agent}: {str(e)}")
            return False
    
    def broadcast_message(self, message: Dict[str, Any]):
        """
        Broadcast a message to all agents
        """
        if not self.redis_client:
            self.logger.error("Cannot broadcast message: Redis not available")
            return False
        
        message_data = {
            'from': self.agent_name,
            'broadcast': True,
            'timestamp': datetime.utcnow().isoformat(),
            'data': message
        }
        
        try:
            self.redis_client.publish('agents.global', json.dumps(message_data))
            self.logger.info("Message broadcasted to all agents")
            return True
        except Exception as e:
            self.logger.error(f"Failed to broadcast message: {str(e)}")
            return False
    
    def listen_for_messages(self):
        """
        Listen for incoming messages from other agents
        """
        if not self.redis_client or not hasattr(self, 'pubsub'):
            return
        
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    self.handle_incoming_message(json.loads(message['data']))
        except Exception as e:
            self.logger.error(f"Error listening for messages: {str(e)}")
    
    def handle_incoming_message(self, message: Dict[str, Any]):
        """
        Handle incoming messages from other agents
        """
        sender = message.get('from')
        data = message.get('data', {})
        
        self.logger.info(f"Received message from {sender}: {data}")
        
        # Process the message based on its type
        message_type = data.get('type')
        if message_type == 'task_assignment':
            self.handle_task_assignment(data)
        elif message_type == 'status_request':
            self.handle_status_request(sender)
        elif message_type == 'coordination':
            self.handle_coordination_message(data)
        else:
            self.logger.warning(f"Unknown message type: {message_type}")
    
    def handle_task_assignment(self, task_data: Dict[str, Any]):
        """
        Handle a task assignment from another agent
        """
        try:
            self.status = AgentStatus.ACTIVE
            result = self.execute_task(task_data)
            self.status = AgentStatus.IDLE
            
            # Send result back to the assigning agent
            if 'assigned_by' in task_data:
                self.send_message(task_data['assigned_by'], {
                    'type': 'task_result',
                    'task_id': task_data.get('task_id'),
                    'result': result
                })
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Task execution failed: {str(e)}")
    
    def handle_status_request(self, requester: str):
        """
        Handle a status request from another agent
        """
        status_data = {
            'type': 'status_response',
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'status': self.status.value,
            'capabilities': self.get_capabilities(),
            'performance_metrics': self.performance_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.send_message(requester, status_data)
    
    def handle_coordination_message(self, data: Dict[str, Any]):
        """
        Handle coordination messages from other agents
        """
        # This can be overridden by specific agent types
        self.logger.info(f"Coordination message received: {data}")
    
    def make_decision(self, decision_type: str, decision_data: Dict[str, Any], 
                     impact_level: DecisionImpact = DecisionImpact.LOW) -> Dict[str, Any]:
        """
        Make a decision and determine if it requires approval.
        Returns the decision result or approval request.
        """
        decision = {
            'decision_type': decision_type,
            'agent_name': self.agent_name,
            'decision_data': decision_data,
            'impact_level': impact_level.value,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Determine if approval is required based on impact level
        requires_approval = impact_level in [DecisionImpact.MEDIUM, DecisionImpact.HIGH]
        
        if requires_approval:
            # Send to approval queue
            decision['requires_approval'] = True
            self.request_approval(decision)
            return {'status': 'pending_approval', 'decision': decision}
        else:
            # Execute decision autonomously
            result = self.execute_decision(decision)
            return {'status': 'executed', 'result': result}
    
    def request_approval(self, decision: Dict[str, Any]):
        """
        Request approval for a high-impact decision
        """
        # This would interact with the approval system
        # For now, we'll just log it
        self.logger.info(f"Approval requested for decision: {decision['decision_type']}")
        
        # Send to orchestrator for approval handling
        self.send_message('orchestrator', {
            'type': 'approval_request',
            'decision': decision
        })
    
    def execute_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a decision that doesn't require approval
        """
        # This should be overridden by specific agent types
        self.logger.info(f"Executing decision: {decision['decision_type']}")
        return {'status': 'completed', 'timestamp': datetime.utcnow().isoformat()}
    
    def update_performance_metrics(self, metrics: Dict[str, Any]):
        """
        Update performance metrics for this agent
        """
        self.performance_metrics.update(metrics)
        self.performance_metrics['last_updated'] = datetime.utcnow().isoformat()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and metrics
        """
        return {
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'status': self.status.value,
            'capabilities': self.get_capabilities(),
            'state_data': self.state_data,
            'performance_metrics': self.performance_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def shutdown(self):
        """
        Gracefully shutdown the agent
        """
        self.logger.info(f"Shutting down agent {self.agent_name}")
        
        if hasattr(self, 'pubsub'):
            self.pubsub.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        self.status = AgentStatus.IDLE