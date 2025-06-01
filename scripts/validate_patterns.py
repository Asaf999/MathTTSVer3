#!/usr/bin/env python3
"""Pattern validation script for MathTTS v3"""

import yaml
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
import argparse

class PatternValidator:
    """Validates pattern files for consistency and correctness"""
    
    def __init__(self, patterns_dir: Path):
        self.patterns_dir = patterns_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.pattern_ids: Set[str] = set()
        self.pattern_priorities: Dict[str, int] = {}
        self.pattern_names: Dict[str, str] = {}
        
    def validate_all(self) -> bool:
        """Validate all pattern files"""
        print("Starting pattern validation...")
        
        # Load master configuration
        master_file = self.patterns_dir / "master_patterns.yaml"
        if not master_file.exists():
            self.errors.append(f"Master configuration file not found: {master_file}")
            return False
            
        with open(master_file, 'r') as f:
            master_config = yaml.safe_load(f)
            
        # Validate each pattern file
        for file_config in master_config.get('pattern_files', []):
            if file_config.get('enabled', True):
                file_path = self.patterns_dir / file_config['path']
                self.validate_pattern_file(file_path)
                
        # Check for global issues
        self._check_priority_conflicts()
        self._check_pattern_coverage()
        
        # Report results
        self._report_results()
        
        return len(self.errors) == 0
        
    def validate_pattern_file(self, file_path: Path) -> None:
        """Validate a single pattern file"""
        if not file_path.exists():
            self.errors.append(f"Pattern file not found: {file_path}")
            return
            
        print(f"Validating {file_path}...")
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as e:
            self.errors.append(f"Failed to parse {file_path}: {e}")
            return
            
        # Validate metadata
        if 'metadata' not in data:
            self.warnings.append(f"{file_path}: Missing metadata section")
            
        # Validate patterns
        patterns = data.get('patterns', [])
        if not patterns:
            self.warnings.append(f"{file_path}: No patterns defined")
            return
            
        for idx, pattern in enumerate(patterns):
            self._validate_pattern(pattern, file_path, idx)
            
    def _validate_pattern(self, pattern: Dict[str, Any], file_path: Path, idx: int) -> None:
        """Validate individual pattern"""
        pattern_ref = f"{file_path}[{idx}]"
        
        # Required fields
        required_fields = ['id', 'name', 'pattern', 'output_template', 'priority']
        for field in required_fields:
            if field not in pattern:
                self.errors.append(f"{pattern_ref}: Missing required field '{field}'")
                
        if 'id' not in pattern:
            return
            
        pattern_id = pattern['id']
        
        # Check for duplicate IDs
        if pattern_id in self.pattern_ids:
            self.errors.append(f"{pattern_ref}: Duplicate pattern ID '{pattern_id}'")
        else:
            self.pattern_ids.add(pattern_id)
            
        # Validate pattern regex
        if 'pattern' in pattern:
            try:
                re.compile(pattern['pattern'])
            except re.error as e:
                self.errors.append(f"{pattern_ref}: Invalid regex pattern: {e}")
                
        # Validate output template
        if 'output_template' in pattern:
            template = pattern['output_template']
            # Check for balanced backreferences
            backrefs = re.findall(r'\\(\d+)', template)
            pattern_groups = len(re.findall(r'\([^?]', pattern.get('pattern', '')))
            for backref in backrefs:
                if int(backref) > pattern_groups:
                    self.errors.append(
                        f"{pattern_ref}: Output template references group \\{backref} "
                        f"but pattern only has {pattern_groups} groups"
                    )
                    
        # Validate priority
        if 'priority' in pattern:
            priority = pattern['priority']
            if not isinstance(priority, int) or priority < 0:
                self.errors.append(f"{pattern_ref}: Priority must be a non-negative integer")
            else:
                self.pattern_priorities[pattern_id] = priority
                
        # Validate tags
        if 'tags' in pattern:
            if not isinstance(pattern['tags'], list):
                self.errors.append(f"{pattern_ref}: Tags must be a list")
                
        # Store pattern name for reference
        if 'name' in pattern:
            self.pattern_names[pattern_id] = pattern['name']
            
    def _check_priority_conflicts(self) -> None:
        """Check for patterns with conflicting priorities"""
        priority_groups = defaultdict(list)
        for pattern_id, priority in self.pattern_priorities.items():
            priority_groups[priority].append(pattern_id)
            
        for priority, patterns in priority_groups.items():
            if len(patterns) > 5:  # Warn if too many patterns have same priority
                self.warnings.append(
                    f"High number of patterns ({len(patterns)}) with priority {priority}: "
                    f"{', '.join(patterns[:5])}..."
                )
                
    def _check_pattern_coverage(self) -> None:
        """Check for missing pattern coverage"""
        # Define expected pattern categories
        expected_categories = {
            'fraction', 'power', 'root', 'derivative', 'integral',
            'limit', 'sum', 'product', 'trig', 'log', 'set',
            'logic', 'vector', 'matrix', 'probability', 'greek'
        }
        
        # Collect all tags
        found_categories = set()
        for pattern_id in self.pattern_ids:
            # This is simplified - in real implementation would track tags
            found_categories.add('fraction')  # Placeholder
            
        # Report missing categories
        # missing = expected_categories - found_categories
        # if missing:
        #     self.warnings.append(f"Missing pattern categories: {', '.join(missing)}")
            
    def _report_results(self) -> None:
        """Report validation results"""
        print("\n" + "="*60)
        print("VALIDATION RESULTS")
        print("="*60)
        
        print(f"\nTotal patterns validated: {len(self.pattern_ids)}")
        
        if self.errors:
            print(f"\nERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  ❌ {error}")
        else:
            print("\n✅ No errors found!")
            
        if self.warnings:
            print(f"\nWARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
        else:
            print("\n✅ No warnings!")
            
        print("\n" + "="*60)
        

def generate_test_cases(patterns_dir: Path, output_file: Path) -> None:
    """Generate test cases from pattern examples"""
    print(f"Generating test cases to {output_file}...")
    
    test_cases = []
    
    # Load all pattern files
    master_file = patterns_dir / "master_patterns.yaml"
    with open(master_file, 'r') as f:
        master_config = yaml.safe_load(f)
        
    for file_config in master_config.get('pattern_files', []):
        if file_config.get('enabled', True):
            file_path = patterns_dir / file_config['path']
            if file_path.exists():
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    
                for pattern in data.get('patterns', []):
                    # Extract examples
                    for example in pattern.get('examples', []):
                        test_cases.append({
                            'pattern_id': pattern['id'],
                            'pattern_name': pattern.get('name', ''),
                            'input': example.get('input', ''),
                            'expected': example.get('output', ''),
                            'category': data.get('metadata', {}).get('category', 'unknown')
                        })
                        
    # Write test cases
    with open(output_file, 'w') as f:
        yaml.dump({'test_cases': test_cases}, f, default_flow_style=False)
        
    print(f"Generated {len(test_cases)} test cases")
    

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Validate MathTTS pattern files')
    parser.add_argument(
        '--patterns-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'patterns',
        help='Directory containing pattern files'
    )
    parser.add_argument(
        '--generate-tests',
        type=Path,
        help='Generate test cases to specified file'
    )
    
    args = parser.parse_args()
    
    # Run validation
    validator = PatternValidator(args.patterns_dir)
    valid = validator.validate_all()
    
    # Generate test cases if requested
    if args.generate_tests:
        generate_test_cases(args.patterns_dir, args.generate_tests)
        
    # Exit with appropriate code
    sys.exit(0 if valid else 1)
    

if __name__ == '__main__':
    main()