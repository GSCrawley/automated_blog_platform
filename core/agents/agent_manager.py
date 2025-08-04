import logging
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.base_agent import BaseAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.market_analytics_agent import MarketAnalyticsAgent
from infrastructure.message_broker import MessageBroker

class AgentManager:
    """
    Central manager for all agents in the system.
    Handles agent lifecycle, coordination, and monitoring.
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_host = redis_host
        self.redis_port = redis_port
        
        # Set up logging
        self.logger = logging.getLogger('AgentManager')
        
        # Initialize message broker
        self.message_broker = MessageBroker(redis_host, redis_port)
        
        # Agent registry
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_threads: Dict[str, threading.Thread] = {}
        
        # Manager state
        self.is_running = False
        self.start_time = datetime.utcnow()
        
        # Statistics
        self.stats = {
            'agents_started': 0,
            'agents_stopped': 0,
            'total_uptime': 0,
            'last_health_check': None
        }
        
        self.logger.info("Agent Manager initialized")
    
    def register_agent(self, agent: BaseAgent) -> bool:
        """Register an agent with the manager"""
        try:
            agent_name = agent.agent_name
            
            if agent_name in self.agents:
                self.logger.warning(f"Agent {agent_name} already registered")
                return False
            
            self.agents[agent_name] = agent
            self.logger.info(f"Agent {agent_name} registered successfully")
            
            # Notify other agents of the new registration
            self.message_broker.publish_message('agents.global', {
                'type': 'agent_registered',
                'agent_name': agent_name,
                'agent_type': agent.agent_type,
                'capabilities': agent.get_capabilities()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent: {str(e)}")
            return False
    
    def start_agent(self, agent_name: str) -> bool:
        """Start a specific agent"""
        if agent_name not in self.agents:
            self.logger.error(f"Agent {agent_name} not found")
            return False
        
        if agent_name in self.agent_threads and self.agent_threads[agent_name].is_alive():
            self.logger.warning(f"Agent {agent_name} is already running")
            return True
        
        try:
            agent = self.agents[agent_name]
            
            # Create and start agent thread
            if hasattr(agent, 'start_monitoring_loop'):
                agent_thread = threading.Thread(
                    target=agent.start_monitoring_loop,
                    name=f"Agent-{agent_name}",
                    daemon=True
                )
            else:
                # For agents without monitoring loop, just start listening
                agent_thread = threading.Thread(
                    target=agent.listen_for_messages,
                    name=f"Agent-{agent_name}",
                    daemon=True
                )
            
            agent_thread.start()
            self.agent_threads[agent_name] = agent_thread
            
            self.stats['agents_started'] += 1
            self.logger.info(f"Agent {agent_name} started successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start agent {agent_name}: {str(e)}")
            return False
    
    def stop_agent(self, agent_name: str) -> bool:
        """Stop a specific agent"""
        if agent_name not in self.agents:
            self.logger.error(f"Agent {agent_name} not found")
            return False
        
        try:
            agent = self.agents[agent_name]
            
            # Shutdown the agent
            agent.shutdown()
            
            # Wait for thread to finish
            if agent_name in self.agent_threads:
                thread = self.agent_threads[agent_name]
                if thread.is_alive():
                    thread.join(timeout=5.0)  # Wait up to 5 seconds
                
                del self.agent_threads[agent_name]
            
            self.stats['agents_stopped'] += 1
            self.logger.info(f"Agent {agent_name} stopped successfully")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop agent {agent_name}: {str(e)}")
            return False
    
    def start_all_agents(self) -> bool:
        """Start all registered agents"""
        self.logger.info("Starting all agents...")
        
        success_count = 0
        for agent_name in self.agents.keys():
            if self.start_agent(agent_name):
                success_count += 1
        
        self.is_running = True
        
        self.logger.info(f"Started {success_count}/{len(self.agents)} agents")
        return success_count == len(self.agents)
    
    def stop_all_agents(self) -> bool:
        """Stop all running agents"""
        self.logger.info("Stopping all agents...")
        
        success_count = 0
        for agent_name in list(self.agents.keys()):
            if self.stop_agent(agent_name):
                success_count += 1
        
        self.is_running = False
        
        self.logger.info(f"Stopped {success_count}/{len(self.agents)} agents")
        return success_count == len(self.agents)
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        is_running = (
            agent_name in self.agent_threads and 
            self.agent_threads[agent_name].is_alive()
        )
        
        status = agent.get_status()
        status['is_running'] = is_running
        status['thread_alive'] = is_running
        
        return status
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        statuses = {}
        
        for agent_name in self.agents.keys():
            statuses[agent_name] = self.get_agent_status(agent_name)
        
        return statuses
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check of all agents"""
        health_report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_status': 'healthy',
            'manager_uptime': (datetime.utcnow() - self.start_time).total_seconds(),
            'total_agents': len(self.agents),
            'running_agents': 0,
            'failed_agents': [],
            'agent_details': {},
            'message_broker_status': 'unknown'
        }
        
        # Check message broker
        try:
            broker_stats = self.message_broker.get_statistics()
            health_report['message_broker_status'] = 'healthy'
            health_report['broker_stats'] = broker_stats
        except Exception as e:
            health_report['message_broker_status'] = 'error'
            health_report['broker_error'] = str(e)
            health_report['overall_status'] = 'degraded'
        
        # Check each agent
        for agent_name, agent in self.agents.items():
            try:
                agent_status = self.get_agent_status(agent_name)
                health_report['agent_details'][agent_name] = agent_status
                
                if agent_status and agent_status.get('is_running'):
                    health_report['running_agents'] += 1
                else:
                    health_report['failed_agents'].append(agent_name)
                    health_report['overall_status'] = 'degraded'
                    
            except Exception as e:
                health_report['failed_agents'].append(agent_name)
                health_report['agent_details'][agent_name] = {'error': str(e)}
                health_report['overall_status'] = 'degraded'
        
        self.stats['last_health_check'] = health_report['timestamp']
        
        return health_report
    
    def initialize_default_agents(self):
        """Initialize and register default agents"""
        self.logger.info("Initializing default agents...")
        
        try:
            # Initialize Orchestrator Agent
            orchestrator = OrchestratorAgent(self.redis_host, self.redis_port)
            self.register_agent(orchestrator)
            
            # Initialize Market Analytics Agent
            market_analytics = MarketAnalyticsAgent(self.redis_host, self.redis_port)
            self.register_agent(market_analytics)
            
            self.logger.info("Default agents initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize default agents: {str(e)}")
    
    def send_message_to_agent(self, target_agent: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific agent via the message broker"""
        return self.message_broker.publish_message(f'agents.{target_agent}', message)
    
    def broadcast_message(self, message: Dict[str, Any]) -> bool:
        """Broadcast a message to all agents"""
        return self.message_broker.publish_message('agents.global', message)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics"""
        current_stats = self.stats.copy()
        current_stats.update({
            'total_agents': len(self.agents),
            'running_agents': sum(
                1 for name in self.agents.keys() 
                if name in self.agent_threads and self.agent_threads[name].is_alive()
            ),
            'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
            'is_running': self.is_running,
            'message_broker_stats': self.message_broker.get_statistics()
        })
        
        return current_stats
    
    def start_monitoring_loop(self):
        """Start the main monitoring loop for the agent manager"""
        self.logger.info("Starting Agent Manager monitoring loop")
        
        # Start message broker listening
        self.message_broker.start_listening()
        
        # Initialize default agents
        self.initialize_default_agents()
        
        # Start all agents
        self.start_all_agents()
        
        try:
            while self.is_running:
                # Perform periodic health checks
                if datetime.utcnow().minute % 5 == 0:  # Every 5 minutes
                    health_report = self.perform_health_check()
                    
                    # Log any issues
                    if health_report['overall_status'] != 'healthy':
                        self.logger.warning(f"System health degraded: {health_report['failed_agents']}")
                
                # Brief pause
                time.sleep(30)  # Check every 30 seconds
                
        except KeyboardInterrupt:
            self.logger.info("Agent Manager shutdown requested")
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {str(e)}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the agent manager"""
        self.logger.info("Shutting down Agent Manager...")
        
        # Stop all agents
        self.stop_all_agents()
        
        # Shutdown message broker
        if self.message_broker:
            self.message_broker.shutdown()
        
        self.is_running = False
        
        # Log final statistics
        final_stats = self.get_statistics()
        self.logger.info(f"Agent Manager shutdown complete. Final stats: {final_stats}")

# Convenience function to start the agent system
def start_agent_system(redis_host: str = 'localhost', redis_port: int = 6379):
    """Start the complete agent system"""
    manager = AgentManager(redis_host, redis_port)
    
    try:
        manager.start_monitoring_loop()
    except KeyboardInterrupt:
        print("\nShutting down agent system...")
    finally:
        manager.shutdown()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the agent system
    start_agent_system()