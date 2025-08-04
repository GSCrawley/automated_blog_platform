import redis
import json
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import threading
import time

class MessageBroker:
    """
    Redis-based message broker for inter-agent communication.
    Handles pub/sub messaging, task queues, and agent coordination.
    """
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379, redis_db: int = 0):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        
        # Set up logging
        self.logger = logging.getLogger('MessageBroker')
        
        # Initialize Redis connections
        self.redis_client = None
        self.pubsub = None
        self.connect()
        
        # Message handlers
        self.message_handlers = {}
        
        # Task queue management
        self.task_queues = {}
        
        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'tasks_queued': 0,
            'tasks_processed': 0,
            'start_time': datetime.utcnow().isoformat()
        }
        
        self.logger.info(f"Message Broker initialized (Redis: {redis_host}:{redis_port})")
    
    def connect(self) -> bool:
        """Establish connection to Redis"""
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True
            )
            
            # Test connection
            self.redis_client.ping()
            
            # Set up pub/sub
            self.pubsub = self.redis_client.pubsub()
            
            self.logger.info("Successfully connected to Redis")
            return True
            
        except redis.ConnectionError as e:
            self.logger.error(f"Failed to connect to Redis: {str(e)}")
            return False
    
    def publish_message(self, channel: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a specific channel"""
        if not self.redis_client:
            self.logger.error("Redis client not available")
            return False
        
        try:
            message_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'message_id': f"{channel}_{int(time.time() * 1000)}",
                'data': message
            }
            
            result = self.redis_client.publish(channel, json.dumps(message_data))
            
            if result > 0:
                self.stats['messages_sent'] += 1
                self.logger.debug(f"Message published to {channel}: {message.get('type', 'unknown')}")
                return True
            else:
                self.logger.warning(f"No subscribers for channel {channel}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to publish message to {channel}: {str(e)}")
            return False
    
    def subscribe_to_channel(self, channel: str, handler: Callable[[Dict[str, Any]], None]):
        """Subscribe to a channel with a message handler"""
        if not self.pubsub:
            self.logger.error("Pub/sub not available")
            return False
        
        try:
            self.pubsub.subscribe(channel)
            self.message_handlers[channel] = handler
            self.logger.info(f"Subscribed to channel: {channel}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {channel}: {str(e)}")
            return False
    
    def unsubscribe_from_channel(self, channel: str):
        """Unsubscribe from a channel"""
        if not self.pubsub:
            return False
        
        try:
            self.pubsub.unsubscribe(channel)
            if channel in self.message_handlers:
                del self.message_handlers[channel]
            self.logger.info(f"Unsubscribed from channel: {channel}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from {channel}: {str(e)}")
            return False
    
    def start_listening(self):
        """Start listening for messages in a separate thread"""
        if not self.pubsub:
            self.logger.error("Pub/sub not available")
            return
        
        def listen_loop():
            self.logger.info("Started message listening loop")
            
            try:
                for message in self.pubsub.listen():
                    if message['type'] == 'message':
                        self.handle_message(message)
                        
            except Exception as e:
                self.logger.error(f"Error in listening loop: {str(e)}")
        
        # Start listening in a separate thread
        listen_thread = threading.Thread(target=listen_loop, daemon=True)
        listen_thread.start()
        
        self.logger.info("Message listening thread started")
    
    def handle_message(self, raw_message: Dict[str, Any]):
        """Handle incoming messages"""
        try:
            channel = raw_message['channel']
            message_data = json.loads(raw_message['data'])
            
            # Update statistics
            self.stats['messages_received'] += 1
            
            # Find and call the appropriate handler
            if channel in self.message_handlers:
                handler = self.message_handlers[channel]
                handler(message_data)
            else:
                self.logger.warning(f"No handler for channel: {channel}")
                
        except Exception as e:
            self.logger.error(f"Error handling message: {str(e)}")
    
    def add_task_to_queue(self, queue_name: str, task: Dict[str, Any], priority: int = 5) -> bool:
        """Add a task to a priority queue"""
        if not self.redis_client:
            return False
        
        try:
            task_data = {
                'task_id': f"{queue_name}_{int(time.time() * 1000)}",
                'priority': priority,
                'created_at': datetime.utcnow().isoformat(),
                'task': task
            }
            
            # Use Redis sorted set for priority queue (lower score = higher priority)
            queue_key = f"task_queue:{queue_name}"
            score = 10 - priority  # Invert priority so higher priority = lower score
            
            result = self.redis_client.zadd(queue_key, {json.dumps(task_data): score})
            
            if result:
                self.stats['tasks_queued'] += 1
                self.logger.debug(f"Task added to queue {queue_name} with priority {priority}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to add task to queue {queue_name}: {str(e)}")
            return False
    
    def get_task_from_queue(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get the highest priority task from a queue"""
        if not self.redis_client:
            return None
        
        try:
            queue_key = f"task_queue:{queue_name}"
            
            # Get the task with the lowest score (highest priority)
            result = self.redis_client.zpopmin(queue_key)
            
            if result:
                task_json, score = result[0]
                task_data = json.loads(task_json)
                
                self.stats['tasks_processed'] += 1
                self.logger.debug(f"Task retrieved from queue {queue_name}")
                
                return task_data
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get task from queue {queue_name}: {str(e)}")
            return None
    
    def get_queue_size(self, queue_name: str) -> int:
        """Get the number of tasks in a queue"""
        if not self.redis_client:
            return 0
        
        try:
            queue_key = f"task_queue:{queue_name}"
            return self.redis_client.zcard(queue_key)
        except Exception as e:
            self.logger.error(f"Failed to get queue size for {queue_name}: {str(e)}")
            return 0
    
    def set_agent_status(self, agent_name: str, status: Dict[str, Any]):
        """Set agent status in Redis"""
        if not self.redis_client:
            return False
        
        try:
            status_key = f"agent_status:{agent_name}"
            status_data = {
                **status,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            self.redis_client.hset(status_key, mapping=status_data)
            
            # Set expiration to detect dead agents
            self.redis_client.expire(status_key, 300)  # 5 minutes
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set agent status for {agent_name}: {str(e)}")
            return False
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent status from Redis"""
        if not self.redis_client:
            return None
        
        try:
            status_key = f"agent_status:{agent_name}"
            status_data = self.redis_client.hgetall(status_key)
            
            return status_data if status_data else None
            
        except Exception as e:
            self.logger.error(f"Failed to get agent status for {agent_name}: {str(e)}")
            return None
    
    def get_all_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all agents"""
        if not self.redis_client:
            return {}
        
        try:
            agent_statuses = {}
            
            # Find all agent status keys
            status_keys = self.redis_client.keys("agent_status:*")
            
            for key in status_keys:
                agent_name = key.split(":", 1)[1]
                status_data = self.redis_client.hgetall(key)
                if status_data:
                    agent_statuses[agent_name] = status_data
            
            return agent_statuses
            
        except Exception as e:
            self.logger.error(f"Failed to get all agent statuses: {str(e)}")
            return {}
    
    def create_coordination_channel(self, channel_name: str) -> str:
        """Create a coordination channel for agent collaboration"""
        coordination_channel = f"coordination:{channel_name}"
        
        # Initialize channel metadata
        if self.redis_client:
            try:
                metadata = {
                    'created_at': datetime.utcnow().isoformat(),
                    'participants': 0,
                    'message_count': 0
                }
                
                self.redis_client.hset(f"channel_meta:{coordination_channel}", mapping=metadata)
                
                self.logger.info(f"Coordination channel created: {coordination_channel}")
                return coordination_channel
                
            except Exception as e:
                self.logger.error(f"Failed to create coordination channel: {str(e)}")
        
        return coordination_channel
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message broker statistics"""
        current_stats = self.stats.copy()
        
        if self.redis_client:
            try:
                # Add Redis info
                redis_info = self.redis_client.info()
                current_stats['redis_info'] = {
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'used_memory': redis_info.get('used_memory_human', '0B'),
                    'uptime_in_seconds': redis_info.get('uptime_in_seconds', 0)
                }
                
                # Add queue information
                queue_info = {}
                queue_keys = self.redis_client.keys("task_queue:*")
                for key in queue_keys:
                    queue_name = key.split(":", 1)[1]
                    queue_info[queue_name] = self.redis_client.zcard(key)
                
                current_stats['queue_sizes'] = queue_info
                
            except Exception as e:
                self.logger.error(f"Error getting Redis statistics: {str(e)}")
        
        return current_stats
    
    def shutdown(self):
        """Gracefully shutdown the message broker"""
        self.logger.info("Shutting down message broker")
        
        if self.pubsub:
            self.pubsub.close()
        
        if self.redis_client:
            self.redis_client.close()
        
        self.logger.info("Message broker shutdown complete")