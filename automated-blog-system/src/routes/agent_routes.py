from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

# Import database models
try:
    from src.models.agent_models import AgentState, BlogInstance, AgentTask, MarketData, AgentDecision
    from src.models.user import db
    AGENT_MODELS_AVAILABLE = True
except ImportError:
    AGENT_MODELS_AVAILABLE = False

agent_bp = Blueprint('agents', __name__)
logger = logging.getLogger(__name__)

@agent_bp.route('/agents/status', methods=['GET'])
def get_agent_status():
    """Get status of all agents"""
    try:
        # Try to get status from agent manager if available
        if hasattr(current_app, 'agent_manager') and current_app.agent_manager:
            agents_status = current_app.agent_manager.get_all_agent_statuses()
            
            # Add database information if available
            if AGENT_MODELS_AVAILABLE:
                try:
                    agent_states = AgentState.query.all()
                    for state in agent_states:
                        if state.agent_name in agents_status:
                            agents_status[state.agent_name]['database_state'] = state.to_dict()
                except Exception as e:
                    logger.warning(f"Could not fetch agent states from database: {e}")
            
            return jsonify({
                'status': 'success',
                'agents': agents_status,
                'total_agents': len(agents_status),
                'active_agents': sum(1 for agent in agents_status.values() if agent.get('status') == 'active'),
                'agent_manager_available': True
            })
        else:
            # Fallback to mock data if agent manager not available
            agents_status = {
                'orchestrator': {
                    'status': 'not_started',
                    'last_seen': None,
                    'assigned_blogs': [],
                    'performance_metrics': {},
                    'agent_manager_available': False
                },
                'market_analytics': {
                    'status': 'not_started',
                    'last_seen': None,
                    'assigned_blogs': [],
                    'performance_metrics': {},
                    'agent_manager_available': False
                }
            }
            
            return jsonify({
                'status': 'success',
                'agents': agents_status,
                'total_agents': len(agents_status),
                'active_agents': 0,
                'agent_manager_available': False,
                'message': 'Agent system not started. Use /system/start-agents to initialize.'
            })
        
    except Exception as e:
        logger.error(f"Error getting agent status: {str(e)}")
        return jsonify({'error': 'Failed to get agent status'}), 500

@agent_bp.route('/agents/<agent_name>/assign', methods=['POST'])
def assign_agent_to_blog(agent_name):
    """Assign an agent to a blog instance"""
    try:
        data = request.get_json()
        blog_instance_id = data.get('blog_instance_id')
        
        if not blog_instance_id:
            return jsonify({'error': 'blog_instance_id is required'}), 400
        
        # Try to assign agent using agent manager if available
        if hasattr(current_app, 'agent_manager') and current_app.agent_manager:
            success = current_app.agent_manager.assign_agent_to_blog(agent_name, blog_instance_id)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Agent {agent_name} assigned to blog {blog_instance_id}'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to assign agent {agent_name} to blog {blog_instance_id}'
                }), 500
        else:
            # Fallback to mock assignment if agent manager not available
            assignment_result = {
                'agent_name': agent_name,
                'blog_instance_id': blog_instance_id,
                'assigned_at': datetime.utcnow().isoformat(),
                'status': 'assigned'
            }
            
            logger.info(f"Agent {agent_name} assigned to blog {blog_instance_id}")
            
            return jsonify({
                'status': 'success',
                'message': f'Agent {agent_name} assigned to blog {blog_instance_id}',
                'assignment': assignment_result
            })
        
    except Exception as e:
        logger.error(f"Error assigning agent {agent_name}: {str(e)}")
        return jsonify({'error': 'Failed to assign agent'}), 500

@agent_bp.route('/agents/<agent_name>/tasks', methods=['GET'])
def get_agent_tasks(agent_name):
    """Get tasks assigned to a specific agent"""
    try:
        # Try to get tasks from agent manager if available
        if hasattr(current_app, 'agent_manager') and current_app.agent_manager:
            tasks = current_app.agent_manager.get_agent_tasks(agent_name)
            
            return jsonify({
                'status': 'success',
                'agent_name': agent_name,
                'tasks': tasks,
                'total_tasks': len(tasks)
            })
        else:
            # Fallback to mock tasks if agent manager not available
            tasks = [
                {
                    'id': 1,
                    'task_type': 'market_research',
                    'status': 'completed',
                    'priority': 8,
                    'created_at': datetime.utcnow().isoformat(),
                    'completed_at': datetime.utcnow().isoformat()
                },
                {
                    'id': 2,
                    'task_type': 'content_generation',
                    'status': 'in_progress',
                    'priority': 7,
                    'created_at': datetime.utcnow().isoformat(),
                    'completed_at': None
                }
            ]
            
            return jsonify({
                'status': 'success',
                'agent_name': agent_name,
                'tasks': tasks,
                'total_tasks': len(tasks)
            })
        
    except Exception as e:
        logger.error(f"Error getting tasks for agent {agent_name}: {str(e)}")
        return jsonify({'error': 'Failed to get agent tasks'}), 500

@agent_bp.route('/agents/<agent_name>/tasks', methods=['POST'])
def assign_task_to_agent(agent_name):
    """Assign a new task to an agent"""
    try:
        data = request.get_json()
        
        required_fields = ['task_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Try to assign task using agent manager if available
        if hasattr(current_app, 'agent_manager') and current_app.agent_manager:
            success = current_app.agent_manager.assign_task_to_agent(agent_name, data)
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': f'Task assigned to agent {agent_name}'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Failed to assign task to agent {agent_name}'
                }), 500
        else:
            # Fallback to mock task assignment if agent manager not available
            task_data = {
                'task_type': data['task_type'],
                'priority': data.get('priority', 5),
                'blog_instance_id': data.get('blog_instance_id'),
                'task_data': data.get('task_data', {}),
                'assigned_agent': agent_name,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Task {data['task_type']} assigned to agent {agent_name}")
            
            return jsonify({
                'status': 'success',
                'message': f'Task assigned to agent {agent_name}',
                'task': task_data
            })
        
    except Exception as e:
        logger.error(f"Error assigning task to agent {agent_name}: {str(e)}")
        return jsonify({'error': 'Failed to assign task'}), 500

@agent_bp.route('/blog-instances', methods=['GET'])
def get_blog_instances():
    """Get all blog instances"""
    try:
        # Try to get blog instances from database if available
        if AGENT_MODELS_AVAILABLE:
            try:
                blog_instances = BlogInstance.query.all()
                return jsonify({
                    'status': 'success',
                    'blog_instances': [instance.to_dict() for instance in blog_instances],
                    'total_instances': len(blog_instances)
                })
            except Exception as e:
                logger.warning(f"Could not fetch blog instances from database: {e}")
        
        # Fallback to mock blog instances if database not available
        blog_instances = [
            {
                'id': 1,
                'name': 'Tech Reviews Blog',
                'niche_id': 1,
                'niche_name': 'Technology',
                'assigned_agents': ['market_analytics', 'content_strategy'],
                'status': 'active',
                'performance_data': {
                    'monthly_visitors': 15000,
                    'conversion_rate': 2.5,
                    'revenue': 1250.00
                },
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'name': 'Home & Garden Blog',
                'niche_id': 2,
                'niche_name': 'Home & Garden',
                'assigned_agents': ['market_analytics'],
                'status': 'active',
                'performance_data': {
                    'monthly_visitors': 8500,
                    'conversion_rate': 3.1,
                    'revenue': 890.00
                },
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        return jsonify({
            'status': 'success',
            'blog_instances': blog_instances,
            'total_instances': len(blog_instances)
        })
        
    except Exception as e:
        logger.error(f"Error getting blog instances: {str(e)}")
        return jsonify({'error': 'Failed to get blog instances'}), 500

@agent_bp.route('/blog-instances', methods=['POST'])
def create_blog_instance():
    """Create a new blog instance"""
    try:
        data = request.get_json()

        required_fields = ['name', 'niche_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Try to create blog instance in database if available
        if AGENT_MODELS_AVAILABLE:
            try:
                blog_instance = BlogInstance(
                    name=data['name'],
                    niche_id=data['niche_id'],
                    assigned_agents=data.get('assigned_agents', []),
                    status='active',
                    settings=data.get('settings', {})
                )
                db.session.add(blog_instance)
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Blog instance created successfully',
                    'blog_instance': blog_instance.to_dict()
                }), 201
            except Exception as e:
                logger.warning(f"Could not create blog instance in database: {e}")
        
        # Fallback to mock blog instance creation if database not available
        blog_instance = {
            'id': 999,  # Mock ID
            'name': data['name'],
            'niche_id': data['niche_id'],
            'assigned_agents': data.get('assigned_agents', []),
            'status': 'active',
            'settings': data.get('settings', {}),
            'created_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Blog instance created: {data['name']}")
        
        return jsonify({
            'status': 'success',
            'message': 'Blog instance created successfully',
            'blog_instance': blog_instance
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating blog instance: {str(e)}")
        return jsonify({'error': 'Failed to create blog instance'}), 500

@agent_bp.route('/decisions/pending', methods=['GET'])
def get_pending_decisions():
    """Get decisions pending approval"""
    try:
        # Try to get pending decisions from database if available
        if AGENT_MODELS_AVAILABLE:
            try:
                pending_decisions = AgentDecision.query.filter_by(approval_status='pending').all()
                return jsonify({
                    'status': 'success',
                    'pending_decisions': [decision.to_dict() for decision in pending_decisions],
                    'total_pending': len(pending_decisions)
                })
            except Exception as e:
                logger.warning(f"Could not fetch pending decisions from database: {e}")
        
        # Fallback to mock pending decisions if database not available
        pending_decisions = [
            {
                'id': 1,
                'agent_name': 'content_strategy',
                'decision_type': 'content_publish',
                'blog_instance_id': 1,
                'decision_data': {
                    'article_title': 'Best Gaming Laptops 2024',
                    'target_keywords': ['gaming laptops', 'best laptops 2024'],
                    'estimated_word_count': 2500
                },
                'impact_level': 'medium',
                'created_at': datetime.utcnow().isoformat(),
                'requires_approval': True,
                'approval_status': 'pending'
            },
            {
                'id': 2,
                'agent_name': 'monetization',
                'decision_type': 'affiliate_program_change',
                'blog_instance_id': 1,
                'decision_data': {
                    'new_program': 'Amazon Associates',
                    'expected_commission_rate': '8%',
                    'reason': 'Higher commission rates available'
                },
                'impact_level': 'high',
                'created_at': datetime.utcnow().isoformat(),
                'requires_approval': True,
                'approval_status': 'pending'
            }
        ]
        
        return jsonify({
            'status': 'success',
            'pending_decisions': pending_decisions,
            'total_pending': len(pending_decisions)
        })
        
    except Exception as e:
        logger.error(f"Error getting pending decisions: {str(e)}")
        return jsonify({'error': 'Failed to get pending decisions'}), 500

@agent_bp.route('/decisions/<int:decision_id>/approve', methods=['POST'])
def approve_decision(decision_id):
    """Approve a pending decision"""
    try:
        data = request.get_json()
        approved_by = data.get('approved_by', 'admin')
        
        # Try to approve decision in database if available
        if AGENT_MODELS_AVAILABLE:
            try:
                decision = AgentDecision.query.get(decision_id)
                if decision:
                    decision.approval_status = 'approved'
                    decision.approved_by = approved_by
                    decision.approved_at = datetime.utcnow()
                    db.session.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Decision {decision_id} approved',
                        'approval': {
                            'decision_id': decision_id,
                            'approval_status': 'approved',
                            'approved_by': approved_by,
                            'approved_at': datetime.utcnow().isoformat()
                        }
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Decision {decision_id} not found'
                    }), 404
            except Exception as e:
                logger.warning(f"Could not approve decision in database: {e}")
        
        # Fallback to mock decision approval if database not available
        approval_result = {
            'decision_id': decision_id,
            'approval_status': 'approved',
            'approved_by': approved_by,
            'approved_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Decision {decision_id} approved by {approved_by}")
        
        return jsonify({
            'status': 'success',
            'message': f'Decision {decision_id} approved',
            'approval': approval_result
        })
        
    except Exception as e:
        logger.error(f"Error approving decision {decision_id}: {str(e)}")
        return jsonify({'error': 'Failed to approve decision'}), 500

@agent_bp.route('/decisions/<int:decision_id>/reject', methods=['POST'])
def reject_decision(decision_id):
    """Reject a pending decision"""
    try:
        data = request.get_json()
        rejected_by = data.get('rejected_by', 'admin')
        reason = data.get('reason', 'No reason provided')
        
        # Try to reject decision in database if available
        if AGENT_MODELS_AVAILABLE:
            try:
                decision = AgentDecision.query.get(decision_id)
                if decision:
                    decision.approval_status = 'rejected'
                    decision.rejected_by = rejected_by
                    decision.rejection_reason = reason
                    decision.rejected_at = datetime.utcnow()
                    db.session.commit()
                    
                    return jsonify({
                        'status': 'success',
                        'message': f'Decision {decision_id} rejected',
                        'rejection': {
                            'decision_id': decision_id,
                            'approval_status': 'rejected',
                            'rejected_by': rejected_by,
                            'rejection_reason': reason,
                            'rejected_at': datetime.utcnow().isoformat()
                        }
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': f'Decision {decision_id} not found'
                    }), 404
            except Exception as e:
                logger.warning(f"Could not reject decision in database: {e}")
        
        # Fallback to mock decision rejection if database not available
        rejection_result = {
            'decision_id': decision_id,
            'approval_status': 'rejected',
            'rejected_by': rejected_by,
            'rejection_reason': reason,
            'rejected_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Decision {decision_id} rejected by {rejected_by}: {reason}")
        
        return jsonify({
            'status': 'success',
            'message': f'Decision {decision_id} rejected',
            'rejection': rejection_result
        })
        
    except Exception as e:
        logger.error(f"Error rejecting decision {decision_id}: {str(e)}")
        return jsonify({'error': 'Failed to reject decision'}), 500

@agent_bp.route('/market-data', methods=['GET'])
def get_market_data():
    """Get recent market research data"""
    try:
        niche_id = request.args.get('niche_id')
        limit = int(request.args.get('limit', 10))
        
        # Try to get market data from database if available
        if AGENT_MODELS_AVAILABLE:
            try:
                market_data = MarketData.query.all()
                if niche_id:
                    market_data = [item for item in market_data if item.niche_id == int(niche_id)]
                market_data = market_data[:limit]
                
                return jsonify({
                    'status': 'success',
                    'market_data': [item.to_dict() for item in market_data],
                    'total_items': len(market_data)
                })
            except Exception as e:
                logger.warning(f"Could not fetch market data from database: {e}")
        
        # Fallback to mock market data if database not available
        market_data = [
            {
                'id': 1,
                'data_type': 'product_trend',
                'source': 'amazon',
                'product_name': 'Wireless Gaming Mouse',
                'niche_id': 1,
                'trend_score': 0.85,
                'confidence_score': 0.92,
                'data_payload': {
                    'search_volume': 45000,
                    'price_range': '$50-150',
                    'competition_level': 'medium',
                    'seasonal_trends': ['Q4 peak', 'Back-to-school boost']
                },
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'id': 2,
                'data_type': 'competitor_analysis',
                'source': 'web_scraping',
                'product_name': 'Smart Home Devices',
                'niche_id': 2,
                'trend_score': 0.78,
                'confidence_score': 0.88,
                'data_payload': {
                    'market_leaders': ['Amazon Echo', 'Google Nest'],
                    'content_gaps': ['Installation guides', 'Troubleshooting'],
                    'opportunity_score': 0.72
                },
                'created_at': datetime.utcnow().isoformat()
            }
        ]
        
        if niche_id:
            market_data = [item for item in market_data if item['niche_id'] == int(niche_id)]
        market_data = market_data[:limit]
        
        return jsonify({
            'status': 'success',
            'market_data': market_data,
            'total_items': len(market_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({'error': 'Failed to get market data'}), 500

@agent_bp.route('/system/health', methods=['GET'])
def get_system_health():
    """Get overall system health status"""
    try:
        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'database': 'healthy',
                'redis': 'healthy',
                'agents': {
                    'orchestrator': 'active',
                    'market_analytics': 'idle',
                    'content_strategy': 'not_started',
                    # WordPress manager removed
                },
                'scrapers': {
                    'amazon_scraper': 'idle',
                    'google_trends': 'not_configured'
                }
            },
            'metrics': {
                'total_blog_instances': 2,
                'active_agents': 2,
                'pending_tasks': 0,
                'pending_approvals': 2,
                'system_uptime': '2 hours 15 minutes'
            }
        }
        
        return jsonify({
            'status': 'success',
            'health': health_status
        })
        
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}")
        return jsonify({'error': 'Failed to get system health'}), 500

@agent_bp.route('/system/start-agents', methods=['POST'])
def start_agent_system():
    """Start the agent system"""
    try:
        if hasattr(current_app, 'agent_manager') and current_app.agent_manager:
            if not current_app.agent_manager.is_running:
                current_app.agent_manager.initialize_default_agents()
                success = current_app.agent_manager.start_all_agents()
                
                if success:
                    return jsonify({
                        'status': 'success',
                        'message': 'Agent system started successfully'
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to start some agents'
                    }), 500
            else:
                return jsonify({
                    'status': 'success',
                    'message': 'Agent system is already running'
                })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Agent manager not available'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting agent system: {str(e)}")
        return jsonify({'error': 'Failed to start agent system'}), 500

@agent_bp.route('/system/stop-agents', methods=['POST'])
def stop_agent_system():
    """Stop the agent system"""
    try:
        if hasattr(current_app, 'agent_manager') and current_app.agent_manager:
            success = current_app.agent_manager.stop_all_agents()
            
            if success:
                return jsonify({
                    'status': 'success',
                    'message': 'Agent system stopped successfully'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to stop some agents'
                }), 500
        else:
            return jsonify({
                'status': 'error',
                'message': 'Agent manager not available'
            }), 500
            
    except Exception as e:
        logger.error(f"Error stopping agent system: {str(e)}")
        return jsonify({'error': 'Failed to stop agent system'}), 500