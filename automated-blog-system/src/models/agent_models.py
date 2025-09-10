from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .user import db

class AgentState(db.Model):
    """Model to track the state of individual agents"""
    __tablename__ = 'agent_states'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    agent_type = Column(String(50), nullable=False)  # orchestrator, market_analytics, etc.
    blog_instance_id = Column(Integer, ForeignKey('blog_instances.id'), nullable=True)
    state_data = Column(JSON, default={})  # Store agent-specific state
    last_action = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='idle')  # idle, active, error, paused
    performance_metrics = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_name': self.agent_name,
            'agent_type': self.agent_type,
            'blog_instance_id': self.blog_instance_id,
            'state_data': self.state_data,
            'last_action': self.last_action.isoformat() if self.last_action else None,
            'status': self.status,
            'performance_metrics': self.performance_metrics,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class BlogInstance(db.Model):
    """Model to manage multiple blog instances (headless - decoupled from CMS)."""
    __tablename__ = 'blog_instances'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    niche_id = Column(Integer, ForeignKey('niches.id'), nullable=False)
    assigned_agents = Column(JSON, default=[])  # List of agent names assigned to this blog
    status = Column(String(50), default='active')  # active, paused, error, maintenance
    performance_data = Column(JSON, default={})
    settings = Column(JSON, default={})  # Blog-specific settings / future CMS mapping
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    niche = relationship('Niche', backref='blog_instances')
    agent_states = relationship('AgentState', backref='blog_instance')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'niche_id': self.niche_id,
            'niche_name': self.niche.name if self.niche else None,
            'assigned_agents': self.assigned_agents,
            'status': self.status,
            'performance_data': self.performance_data,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class AgentTask(db.Model):
    """Model to track tasks assigned to agents"""
    __tablename__ = 'agent_tasks'
    
    id = Column(Integer, primary_key=True)
    task_type = Column(String(100), nullable=False)  # content_generation, market_research, etc.
    assigned_agent = Column(String(100), nullable=False)
    blog_instance_id = Column(Integer, ForeignKey('blog_instances.id'), nullable=True)
    priority = Column(Integer, default=5)  # 1-10, 10 being highest priority
    status = Column(String(20), default='pending')  # pending, in_progress, completed, failed
    task_data = Column(JSON, default={})  # Task-specific parameters
    result_data = Column(JSON, default={})  # Task results
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_type': self.task_type,
            'assigned_agent': self.assigned_agent,
            'blog_instance_id': self.blog_instance_id,
            'priority': self.priority,
            'status': self.status,
            'task_data': self.task_data,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class MarketData(db.Model):
    """Model to store market research data from scraping"""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    data_type = Column(String(50), nullable=False)  # product_trend, competitor_analysis, etc.
    source = Column(String(100), nullable=False)  # amazon, google_trends, etc.
    product_name = Column(String(200))
    niche_id = Column(Integer, ForeignKey('niches.id'), nullable=True)
    data_payload = Column(JSON, nullable=False)  # The actual scraped data
    trend_score = Column(Float, default=0.0)  # Calculated trend score
    confidence_score = Column(Float, default=0.0)  # Confidence in the data
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # When this data becomes stale
    
    def to_dict(self):
        return {
            'id': self.id,
            'data_type': self.data_type,
            'source': self.source,
            'product_name': self.product_name,
            'niche_id': self.niche_id,
            'data_payload': self.data_payload,
            'trend_score': self.trend_score,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class AgentDecision(db.Model):
    """Model to track agent decisions for approval workflow"""
    __tablename__ = 'agent_decisions'
    
    id = Column(Integer, primary_key=True)
    agent_name = Column(String(100), nullable=False)
    decision_type = Column(String(100), nullable=False)  # content_publish, budget_allocation, etc.
    blog_instance_id = Column(Integer, ForeignKey('blog_instances.id'), nullable=True)
    decision_data = Column(JSON, nullable=False)  # Details of the decision
    requires_approval = Column(Boolean, default=False)
    approval_status = Column(String(20), default='pending')  # pending, approved, rejected
    approved_by = Column(String(100), nullable=True)  # User who approved/rejected
    impact_level = Column(String(20), default='low')  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'agent_name': self.agent_name,
            'decision_type': self.decision_type,
            'blog_instance_id': self.blog_instance_id,
            'decision_data': self.decision_data,
            'requires_approval': self.requires_approval,
            'approval_status': self.approval_status,
            'approved_by': self.approved_by,
            'impact_level': self.impact_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }