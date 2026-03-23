#!/usr/bin/env python3
"""
Add Apache 2.0 license headers to all Python files in claw-mem.

Usage:
    python scripts/add_license_headers.py

This script adds the Apache 2.0 license header to all Python files
in the src/ directory that don't already have one.
"""

import os
from pathlib import Path

LICENSE_HEADER = """# Copyright 2026 Peter Cheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""

def add_header_to_file(filepath: Path) -> bool:
    """
    Add license header to a Python file if not present.
    
    Args:
        filepath: Path to the Python file
        
    Returns:
        True if header was added, False if already present
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip if already has header
    if 'Licensed under the Apache License' in content:
        return False
    
    # Handle shebang lines
    if content.startswith('#!'):
        # Find the end of the shebang line
        first_newline = content.find('\n')
        if first_newline != -1:
            # Insert header after shebang
            new_content = content[:first_newline + 1] + LICENSE_HEADER + content[first_newline + 1:]
        else:
            new_content = content + '\n' + LICENSE_HEADER
    else:
        # Add header at the beginning
        new_content = LICENSE_HEADER + content
    
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True

def main():
    """Main entry point."""
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Directories to process
    directories = [
        project_root / 'src',
        project_root / 'tests',
        project_root / 'scripts',
    ]
    
    total_count = 0
    updated_count = 0
    skipped_count = 0
    
    print("Adding Apache 2.0 license headers...\n")
    
    for directory in directories:
        if not directory.exists():
            print(f"Skipping {directory} (does not exist)")
            continue
        
        print(f"Processing {directory}...")
        
        for py_file in directory.rglob('*.py'):
            total_count += 1
            
            if add_header_to_file(py_file):
                print(f"  ✅ Added: {py_file.relative_to(project_root)}")
                updated_count += 1
            else:
                skipped_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total files checked: {total_count}")
    print(f"  Headers added: {updated_count}")
    print(f"  Already had headers: {skipped_count}")
    print(f"{'='*60}")
    
    if updated_count > 0:
        print(f"\n✅ Successfully added {updated_count} license header(s)")
    else:
        print(f"\n✅ All files already have license headers")

if __name__ == '__main__':
    main()
