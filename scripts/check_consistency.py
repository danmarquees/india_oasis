#!/usr/bin/env python
"""
India Oasis - Consistency Check Script
=====================================

This script checks for common inconsistencies in the India Oasis project,
including duplicate code, unused imports, missing dependencies, and configuration issues.

Usage:
    python scripts/check_consistency.py [--fix] [--verbose]

Options:
    --fix       Attempt to automatically fix issues where possible
    --verbose   Show detailed output
"""

import os
import sys
import re
import ast
import json
import argparse
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Dict, Set, Tuple, Any

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class ConsistencyChecker:
    def __init__(self, fix_mode=False, verbose=False):
        self.fix_mode = fix_mode
        self.verbose = verbose
        self.issues = []
        self.project_root = PROJECT_ROOT

        # File patterns to check
        self.python_files = list(self.project_root.rglob('*.py'))
        self.template_files = list(self.project_root.rglob('*.html'))
        self.config_files = ['requirements.txt', 'requirements-dev.txt', 'requirements-prod.txt']

    def log(self, message: str, level: str = 'INFO'):
        """Log message with level"""
        if self.verbose or level in ['ERROR', 'WARNING']:
            print(f"[{level}] {message}")

    def add_issue(self, issue_type: str, description: str, file_path: str = None, severity: str = 'WARNING'):
        """Add an issue to the issues list"""
        issue = {
            'type': issue_type,
            'description': description,
            'file': file_path,
            'severity': severity
        }
        self.issues.append(issue)
        self.log(f"{severity}: {description} {f'({file_path})' if file_path else ''}", severity)

    def check_duplicate_classes(self):
        """Check for duplicate class definitions"""
        self.log("Checking for duplicate classes...")

        class_definitions = defaultdict(list)

        for py_file in self.python_files:
            if '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find class definitions
                class_pattern = r'^class\s+(\w+)\s*[\(:]'
                matches = re.finditer(class_pattern, content, re.MULTILINE)

                for match in matches:
                    class_name = match.group(1)
                    class_definitions[class_name].append(str(py_file))

            except Exception as e:
                self.log(f"Error reading {py_file}: {e}", 'ERROR')

        # Report duplicates
        for class_name, files in class_definitions.items():
            if len(files) > 1:
                self.add_issue(
                    'DUPLICATE_CLASS',
                    f"Class '{class_name}' defined in multiple files: {', '.join(files)}",
                    severity='ERROR'
                )

    def check_duplicate_functions(self):
        """Check for duplicate function definitions within same files"""
        self.log("Checking for duplicate functions...")

        for py_file in self.python_files:
            if '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find function definitions
                func_pattern = r'^def\s+(\w+)\s*\('
                matches = re.finditer(func_pattern, content, re.MULTILINE)

                functions = []
                for match in matches:
                    func_name = match.group(1)
                    functions.append(func_name)

                # Check for duplicates within the same file
                func_counts = Counter(functions)
                for func_name, count in func_counts.items():
                    if count > 1:
                        self.add_issue(
                            'DUPLICATE_FUNCTION',
                            f"Function '{func_name}' defined {count} times in same file",
                            str(py_file),
                            'ERROR'
                        )

            except Exception as e:
                self.log(f"Error reading {py_file}: {e}", 'ERROR')

    def check_unused_imports(self):
        """Check for unused imports (basic check)"""
        self.log("Checking for potentially unused imports...")

        for py_file in self.python_files:
            if '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                imports = []
                content = ''.join(lines)

                # Find import statements
                for i, line in enumerate(lines):
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        # Skip Django imports (often used in ways that are hard to detect)
                        if 'django' in line:
                            continue

                        # Extract imported names
                        if line.startswith('import '):
                            imported = line.replace('import ', '').split(',')
                        elif ' import ' in line:
                            imported = line.split(' import ')[1].split(',')
                        else:
                            continue

                        for imp in imported:
                            imp = imp.strip().split(' as ')[0]
                            if imp and imp not in content[content.find(line) + len(line):]:
                                imports.append((imp, i + 1))

                # Basic unused import detection
                for imp, line_num in imports:
                    if imp not in content or content.count(imp) <= 1:
                        self.add_issue(
                            'POTENTIALLY_UNUSED_IMPORT',
                            f"Import '{imp}' on line {line_num} may be unused",
                            str(py_file),
                            'WARNING'
                        )

            except Exception as e:
                self.log(f"Error reading {py_file}: {e}", 'ERROR')

    def check_constants_consistency(self):
        """Check for hardcoded constants that should be centralized"""
        self.log("Checking for hardcoded constants...")

        # Common constants that should be centralized
        constant_patterns = {
            r'\bMAX_CART_QUANTITY\s*=\s*(\d+)': 'MAX_CART_QUANTITY',
            r'\bPRODUCTS_PER_PAGE\s*=\s*(\d+)': 'PRODUCTS_PER_PAGE',
            r'\bCACHE_TIMEOUT\s*=\s*(\d+)': 'CACHE_TIMEOUT',
        }

        constant_values = defaultdict(list)

        for py_file in self.python_files:
            if '__pycache__' in str(py_file):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                for pattern, const_name in constant_patterns.items():
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        value = match.group(1)
                        constant_values[const_name].append((str(py_file), value))

            except Exception as e:
                self.log(f"Error reading {py_file}: {e}", 'ERROR')

        # Check for inconsistent values
        for const_name, occurrences in constant_values.items():
            if len(occurrences) > 1:
                values = set(occ[1] for occ in occurrences)
                if len(values) > 1:
                    self.add_issue(
                        'INCONSISTENT_CONSTANTS',
                        f"Constant '{const_name}' has different values: {dict(occurrences)}",
                        severity='ERROR'
                    )
                elif len(occurrences) > 1:
                    files = [occ[0] for occ in occurrences]
                    self.add_issue(
                        'DUPLICATE_CONSTANTS',
                        f"Constant '{const_name}' defined in multiple files: {files}",
                        severity='WARNING'
                    )

    def check_missing_files(self):
        """Check for missing critical files"""
        self.log("Checking for missing critical files...")

        critical_files = [
            'manage.py',
            'requirements.txt',
            '.gitignore',
            'README.md',
        ]

        for file_name in critical_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                self.add_issue(
                    'MISSING_FILE',
                    f"Critical file '{file_name}' is missing",
                    severity='ERROR'
                )

    def check_template_consistency(self):
        """Check for template consistency issues"""
        self.log("Checking template consistency...")

        # Check for broken template tags
        broken_patterns = [
            r'{%\s*\w+.*%}',  # Unclosed template tags
            r'{{\s*\w+\s*\|\s*\w+.*}}',  # Template variables with filters
        ]

        for template_file in self.template_files:
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for common template issues
                if '{% load ' not in content and ('{{' in content or '{%' in content):
                    self.add_issue(
                        'MISSING_TEMPLATE_LOAD',
                        "Template uses tags/filters but missing {% load %} statements",
                        str(template_file),
                        'WARNING'
                    )

            except Exception as e:
                self.log(f"Error reading {template_file}: {e}", 'ERROR')

    def check_settings_consistency(self):
        """Check for settings file consistency"""
        self.log("Checking settings consistency...")

        settings_files = [
            'india_oasis_project/settings.py',
            'india_oasis_project/settings_development.py',
            'india_oasis_project/settings_production.py'
        ]

        for settings_file in settings_files:
            file_path = self.project_root / settings_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for common issues
                    if 'SECRET_KEY' in content and 'django-insecure' in content:
                        self.add_issue(
                            'INSECURE_SECRET_KEY',
                            "Settings file contains default insecure SECRET_KEY",
                            str(file_path),
                            'ERROR'
                        )

                    if 'DEBUG = True' in content and 'production' in settings_file:
                        self.add_issue(
                            'DEBUG_IN_PRODUCTION',
                            "DEBUG=True found in production settings",
                            str(file_path),
                            'ERROR'
                        )

                except Exception as e:
                    self.log(f"Error reading {file_path}: {e}", 'ERROR')

    def check_requirements_consistency(self):
        """Check for requirements file consistency"""
        self.log("Checking requirements consistency...")

        req_files = {}
        for req_file in self.config_files:
            file_path = self.project_root / req_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        packages = {}
                        for line in lines:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                if '==' in line:
                                    pkg, version = line.split('==', 1)
                                    packages[pkg] = version
                        req_files[req_file] = packages
                except Exception as e:
                    self.log(f"Error reading {file_path}: {e}", 'ERROR')

        # Check for version conflicts
        all_packages = set()
        for packages in req_files.values():
            all_packages.update(packages.keys())

        for package in all_packages:
            versions = {}
            for req_file, packages in req_files.items():
                if package in packages:
                    versions[req_file] = packages[package]

            if len(set(versions.values())) > 1:
                self.add_issue(
                    'VERSION_CONFLICT',
                    f"Package '{package}' has different versions: {versions}",
                    severity='WARNING'
                )

    def run_all_checks(self):
        """Run all consistency checks"""
        self.log("Starting consistency checks...")

        checks = [
            self.check_duplicate_classes,
            self.check_duplicate_functions,
            self.check_unused_imports,
            self.check_constants_consistency,
            self.check_missing_files,
            self.check_template_consistency,
            self.check_settings_consistency,
            self.check_requirements_consistency,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.log(f"Error running check {check.__name__}: {e}", 'ERROR')

        self.print_summary()

    def print_summary(self):
        """Print summary of all issues found"""
        print("\n" + "="*80)
        print("CONSISTENCY CHECK SUMMARY")
        print("="*80)

        if not self.issues:
            print("✅ No consistency issues found!")
            return

        # Group issues by severity
        by_severity = defaultdict(list)
        for issue in self.issues:
            by_severity[issue['severity']].append(issue)

        total_issues = len(self.issues)
        print(f"Total issues found: {total_issues}")

        for severity in ['ERROR', 'WARNING', 'INFO']:
            if severity in by_severity:
                issues = by_severity[severity]
                print(f"\n{severity}S ({len(issues)}):")
                print("-" * 40)

                # Group by type
                by_type = defaultdict(list)
                for issue in issues:
                    by_type[issue['type']].append(issue)

                for issue_type, type_issues in by_type.items():
                    print(f"\n  {issue_type} ({len(type_issues)}):")
                    for issue in type_issues:
                        file_info = f" [{issue['file']}]" if issue['file'] else ""
                        print(f"    • {issue['description']}{file_info}")

        print("\n" + "="*80)

        if any(issue['severity'] == 'ERROR' for issue in self.issues):
            print("❌ Critical issues found that should be fixed!")
            return 1
        elif any(issue['severity'] == 'WARNING' for issue in self.issues):
            print("⚠️  Warnings found - consider reviewing these issues.")
            return 0
        else:
            print("✅ Only minor issues found.")
            return 0

def main():
    parser = argparse.ArgumentParser(description='Check India Oasis project consistency')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues automatically')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    checker = ConsistencyChecker(fix_mode=args.fix, verbose=args.verbose)
    exit_code = checker.run_all_checks()

    sys.exit(exit_code)

if __name__ == '__main__':
    main()
