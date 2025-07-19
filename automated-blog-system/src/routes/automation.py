from flask import Blueprint, request, jsonify
from src.services.automation_scheduler import AutomationScheduler

automation_bp = Blueprint('automation', __name__)

# Initialize scheduler
scheduler = AutomationScheduler()

@automation_bp.route('/scheduler/status', methods=['GET'])
def get_scheduler_status():
    """Get the current status of the automation scheduler."""
    try:
        status = scheduler.get_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/start', methods=['POST'])
def start_scheduler():
    """Start the automation scheduler."""
    try:
        scheduler.start()
        return jsonify({'success': True, 'message': 'Scheduler started successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """Stop the automation scheduler."""
    try:
        scheduler.stop()
        return jsonify({'success': True, 'message': 'Scheduler stopped successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/trigger-content-generation', methods=['POST'])
def trigger_content_generation():
    """Manually trigger content generation."""
    try:
        result = scheduler.generate_daily_content()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@automation_bp.route('/scheduler/trigger-content-update', methods=['POST'])
def trigger_content_update():
    """Manually trigger content updates."""
    try:
        result = scheduler.update_existing_content()
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

