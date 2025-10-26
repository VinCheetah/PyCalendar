#!/usr/bin/env python3
"""
Script pour mettre à jour tous les imports relatifs en imports absolus pycalendar.*

Ce script parcourt tous les fichiers Python dans src/pycalendar/ et remplace :
- from core.* → from pycalendar.core.*
- from data.* → from pycalendar.data.*
- etc.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Modules à transformer
MODULES = [
    "core",
    "data",
    "constraints",
    "generators",
    "solvers",
    "orchestrator",
    "exporters",
    "validation",
    "interface",
    "cli",
]


def fix_imports_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """
    Fix imports in a single Python file.
    
    Returns:
        (number_of_changes, list_of_changes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"⚠️  Erreur lecture {file_path}: {e}")
        return 0, []
    
    original_content = content
    changes = []
    
    for module in MODULES:
        # Pattern 1: from module.xxx import yyy
        pattern1 = rf'^from {module}\.([\w.]+) import '
        replacement1 = rf'from pycalendar.{module}.\1 import '
        new_content, n1 = re.subn(pattern1, replacement1, content, flags=re.MULTILINE)
        if n1 > 0:
            changes.append(f"from {module}.* → from pycalendar.{module}.*")
            content = new_content
        
        # Pattern 2: from module import yyy
        pattern2 = rf'^from {module} import '
        replacement2 = rf'from pycalendar.{module} import '
        new_content, n2 = re.subn(pattern2, replacement2, content, flags=re.MULTILINE)
        if n2 > 0:
            changes.append(f"from {module} import → from pycalendar.{module} import")
            content = new_content
        
        # Pattern 3: import module
        pattern3 = rf'^import {module}$'
        replacement3 = rf'import pycalendar.{module} as {module}'
        new_content, n3 = re.subn(pattern3, replacement3, content, flags=re.MULTILINE)
        if n3 > 0:
            changes.append(f"import {module} → import pycalendar.{module}")
            content = new_content
    
    # Write back if changed
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return len(changes), changes
        except Exception as e:
            print(f"⚠️  Erreur écriture {file_path}: {e}")
            return 0, []
    
    return 0, []


def main():
    """Main function."""
    src_dir = Path(__file__).parent / "src" / "pycalendar"
    
    if not src_dir.exists():
        print(f"❌ Dossier introuvable: {src_dir}")
        return 1
    
    print(f"🔍 Recherche des fichiers Python dans: {src_dir}")
    
    python_files = list(src_dir.rglob("*.py"))
    print(f"📁 {len(python_files)} fichiers Python trouvés\n")
    
    total_files_changed = 0
    total_changes = 0
    
    for py_file in python_files:
        rel_path = py_file.relative_to(src_dir.parent)
        num_changes, changes = fix_imports_in_file(py_file)
        
        if num_changes > 0:
            total_files_changed += 1
            total_changes += num_changes
            print(f"✅ {rel_path}")
            for change in set(changes):
                print(f"   - {change}")
    
    print(f"\n{'='*70}")
    print(f"✅ Terminé!")
    print(f"   • {total_files_changed} fichiers modifiés")
    print(f"   • {total_changes} imports corrigés")
    print(f"{'='*70}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
