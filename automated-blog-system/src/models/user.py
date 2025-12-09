from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

@user_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'success': True, 'message': 'API is healthy'})

@user_bp.route('/info', methods=['GET'])
def get_info():
    """Get API information."""
    return jsonify({
        'success': True,
        'info': {
            'name': 'Automated Blog System API',
            'version': '1.0.0',
            'description': 'Multi-niche automated blog content generation system'
        }
    })

