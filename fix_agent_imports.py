#!/usr/bin/env python3
"""
Quick fix script to resolve agent system import issues
"""

import os

def fix_agent_models():
    """Fix the import issue in agent_models.py"""
    file_path = "automated-blog-system/src/models/agent_models.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the problematic import
    old_import = "from config import db"
    new_import = "from .user import db"
    
    if old_import in content:
        content = content.replace(old_import, new_import)
        
        # Write back the file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed import in {file_path}")
        return True
    else:
        print(f"⚠️ Import already fixed or not found in {file_path}")
        return False

def fix_agent_manager():
    """Fix the syntax issue in agent_manager.py"""
    file_path = "core/agents/agent_manager.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the file
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Find and fix line 47 (the problematic docstring)
    for i, line in enumerate(lines):
        if i == 46:  # Line 47 (0-indexed)
            if '"""Register an agent with the manager"""' not in line:
                # Check if it contains the malformed docstring
                if '"""' in line and ('\\n' in line or 'try:' in line):
                    lines[i] = '        """Register an agent with the manager"""\n'
                    print(f"✅ Fixed line 47 in {file_path}")
                    
                    # Write back the file
                    with open(file_path, 'w') as f:
                        f.writelines(lines)
                    return True
    
    print(f"⚠️ Line 47 already fixed or not found in {file_path}")
    return False

if __name__ == "__main__":
    print("🔧 Fixing agent system import and syntax issues...")
    
    fixed_models = fix_agent_models()
    fixed_manager = fix_agent_manager()
    
    if fixed_models or fixed_manager:
        print("\n✅ Fixes applied! Restart your Flask server:")
        print("   python src/main.py")
    else:
        print("\n⚠️ No fixes needed or files not found")
        print("   Check if you're in the right directory")
