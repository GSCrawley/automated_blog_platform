#!/usr/bin/env python3
"""
Test script to check agent system imports and initialization
"""

import os
import sys

# Add the core directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.join(current_dir, 'core')
sys.path.insert(0, core_dir)

def test_agent_imports():
    """Test if all agent modules can be imported"""
    print("🧪 Testing Agent System Imports...")
    print("=" * 50)
    
    try:
        print("1. Testing BaseAgent import...")
        from agents.base_agent import BaseAgent, AgentStatus, DecisionImpact
        print("   ✅ BaseAgent imported successfully")
    except Exception as e:
        print(f"   ❌ BaseAgent import failed: {e}")
        return False
    
    try:
        print("2. Testing MessageBroker import...")
        from infrastructure.message_broker import MessageBroker
        print("   ✅ MessageBroker imported successfully")
    except Exception as e:
        print(f"   ❌ MessageBroker import failed: {e}")
        return False
    
    try:
        print("3. Testing AgentManager import...")
        from agents.agent_manager import AgentManager
        print("   ✅ AgentManager imported successfully")
    except Exception as e:
        print(f"   ❌ AgentManager import failed: {e}")
        return False
    
    try:
        print("4. Testing MarketAnalyticsAgent import...")
        from agents.market_analytics_agent import MarketAnalyticsAgent
        print("   ✅ MarketAnalyticsAgent imported successfully")
    except Exception as e:
        print(f"   ❌ MarketAnalyticsAgent import failed: {e}")
        return False
    
    try:
        print("5. Testing OrchestratorAgent import...")
        from agents.orchestrator_agent import OrchestratorAgent
        print("   ✅ OrchestratorAgent imported successfully")
    except Exception as e:
        print(f"   ❌ OrchestratorAgent import failed: {e}")
        return False
    
    return True

def test_agent_initialization():
    """Test if agent system can be initialized"""
    print("\n🚀 Testing Agent System Initialization...")
    print("=" * 50)
    
    try:
        from agents.agent_manager import AgentManager
        
        print("1. Creating AgentManager instance...")
        agent_manager = AgentManager()
        print("   ✅ AgentManager created successfully")
        
        print("2. Testing agent manager methods...")
        status = agent_manager.perform_health_check()
        print(f"   ✅ Health check completed: {status.get('overall_status', 'unknown')}")
        
        print("3. Testing agent statistics...")
        stats = agent_manager.get_statistics()
        print(f"   ✅ Statistics retrieved: {stats.get('total_agents', 0)} agents registered")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_redis_connection():
    """Test Redis connection"""
    print("\n🔗 Testing Redis Connection...")
    print("=" * 50)
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("   ✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"   ⚠️ Redis connection failed: {e}")
        print("   💡 This is expected if Redis is not installed/running")
        return False

if __name__ == "__main__":
    print("🔍 Agent System Diagnostic Test")
    print("=" * 30)
    
    # Test imports
    imports_ok = test_agent_imports()
    
    # Test initialization
    init_ok = test_agent_initialization()
    
    # Test Redis
    redis_ok = test_redis_connection()
    
    print("\n📊 Test Results:")
    print("=" * 20)
    print(f"Imports:        {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"Initialization: {'✅ PASS' if init_ok else '❌ FAIL'}")
    print(f"Redis:          {'✅ PASS' if redis_ok else '⚠️ OPTIONAL'}")
    
    if imports_ok and init_ok:
        print("\n🎉 Agent system is ready!")
        print("💡 You can now start the Flask server and the agent system should work.")
        if not redis_ok:
            print("⚠️ Note: Install Redis for full functionality: brew install redis")
    else:
        print("\n❌ Agent system has issues that need to be resolved.")
    
    # Exit with appropriate code
    exit(0 if (imports_ok and init_ok) else 1)
