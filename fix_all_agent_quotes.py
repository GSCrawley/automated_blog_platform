#!/usr/bin/env python3
"""
Comprehensive fix script to resolve escaped quotes issues in all agent files
"""

import os
import re

def fix_escaped_quotes_in_file(file_path):
    """Fix escaped quotes in a single file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Track if any changes were made
        original_content = content
        
        # Fix escaped triple quotes in docstrings
        # Pattern: \"\"\" -> """
        content = content.replace('\\"\\"\\"', '"""')
        
        # Fix escaped single quotes in strings where appropriate
        # Be careful not to break legitimate escaped quotes
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Fixed escaped quotes in: {file_path}")
            return True
        else:
            print(f"⚪ No escaped quotes found in: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing {file_path}: {str(e)}")
        return False

def fix_all_agent_files():
    """Fix escaped quotes in all agent-related files"""
    
    # List of files to check and fix
    files_to_fix = [
        # Core agent files
        "core/agents/base_agent.py",
        "core/agents/agent_manager.py", 
        "core/agents/market_analytics_agent.py",
        "core/agents/orchestrator_agent.py",
        
        # Infrastructure files
        "core/infrastructure/message_broker.py",
        
        # Scraper files
        "core/scrapers/base_scraper.py",
        
        # Backend agent files
        "automated-blog-system/src/routes/agent_routes.py",
        "automated-blog-system/src/models/agent_models.py",
    ]
    
    print("🔧 Fixing escaped quotes in all agent files...")
    print("=" * 50)
    
    fixed_count = 0
    total_count = 0
    
    for file_path in files_to_fix:
        total_count += 1
        if fix_escaped_quotes_in_file(file_path):
            fixed_count += 1
    
    print("=" * 50)
    print(f"📊 Summary: Fixed {fixed_count}/{total_count} files")
    
    if fixed_count > 0:
        print("\n✅ Fixes applied! Now restart your Flask server:")
        print("   cd automated-blog-system")
        print("   python src/main.py")
        print("\nThen test the agent system:")
        print("   curl http://localhost:5000/api/agents/status")
        print("   curl -X POST http://localhost:5000/api/system/start-agents")
    else:
        print("\n⚪ No fixes needed - all files appear to be clean")
    
    return fixed_count > 0

def check_for_syntax_errors():
    """Check for common syntax errors in Python files"""
    
    python_files = [
        "core/agents/base_agent.py",
        "core/agents/agent_manager.py", 
        "core/agents/market_analytics_agent.py",
        "core/agents/orchestrator_agent.py",
        "core/infrastructure/message_broker.py",
        "core/scrapers/base_scraper.py",
    ]
    
    print("\n🔍 Checking for syntax errors...")
    
    for file_path in python_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Try to compile the file
                compile(content, file_path, 'exec')
                print(f"✅ {file_path} - syntax OK")
                
            except SyntaxError as e:
                print(f"❌ {file_path} - syntax error: {e}")
            except Exception as e:
                print(f"⚠️ {file_path} - error: {e}")

if __name__ == "__main__":
    print("🚀 Agent Files Quote Fixer")
    print("=" * 30)
    
    # Fix escaped quotes
    fixes_applied = fix_all_agent_files()
    
    # Check for syntax errors
    check_for_syntax_errors()
    
    print("\n🎉 Done!")
