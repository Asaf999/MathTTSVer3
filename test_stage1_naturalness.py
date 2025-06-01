#!/usr/bin/env python3
"""
Stage 1 Natural Speech Quality Test
Tests the improvements made in Phase 3.5 Stage 1 implementation
Target: 60% natural speech quality
"""

import os
import sys
import yaml
import re
from pathlib import Path
from collections import defaultdict

def load_all_patterns():
    """Load all pattern files and extract patterns with their templates"""
    patterns_dir = Path(__file__).parent / "patterns"
    all_patterns = []
    
    # Pattern files to analyze
    pattern_files = [
        "calculus/derivatives.yaml",
        "calculus/integrals.yaml", 
        "calculus/limits_series.yaml",
        "basic/fractions.yaml",
        "basic/arithmetic.yaml",
        "basic/powers_roots.yaml",
        "algebra/equations.yaml",
        "special/symbols_greek.yaml",
    ]
    
    for file_path in pattern_files:
        full_path = patterns_dir / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    
                if 'patterns' in data:
                    for pattern in data['patterns']:
                        pattern['source_file'] = file_path
                        all_patterns.append(pattern)
                        
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                
    return all_patterns

def evaluate_naturalness(pattern):
    """
    Evaluate the naturalness of a single pattern based on multiple criteria
    Returns a score from 0-6 (6 being most natural)
    """
    if 'output_template' not in pattern:
        return 0
        
    template = pattern['output_template'].lower()
    score = 0
    max_score = 6
    
    # 1. Uses natural mathematical language (2 points)
    natural_phrases = [
        "the derivative of", "the integral", "with respect to", 
        "the fraction", "raised to", "to the power of",
        "squared", "cubed", "the limit", "approaches"
    ]
    if any(phrase in template for phrase in natural_phrases):
        score += 2
    
    # 2. Has connecting phrases/articles (1 point)
    connecting_words = ["the", "of", "with", "to", "from", "and", "or"]
    if any(word in template for word in connecting_words):
        score += 1
        
    # 3. Avoids raw symbols/robotic speech (1 point)
    robotic_patterns = ["d \\", " d ", "partial \\", "\\1 \\2", "^", "{", "}"]
    if not any(pattern in template for pattern in robotic_patterns):
        score += 1
        
    # 4. Professor-style explanations (1 point)
    professor_style = [
        "the derivative", "the integral", "the second derivative",
        "the partial derivative", "evaluated at", "the limit as"
    ]
    if any(phrase in template for phrase in professor_style):
        score += 1
        
    # 5. Natural flow and readability (1 point)
    if len(template.split()) >= 3 and not re.search(r'\\[0-9]\\[0-9]', template):
        score += 1
    
    return min(score, max_score)

def calculate_domain_statistics(patterns):
    """Calculate naturalness statistics by mathematical domain"""
    domain_stats = defaultdict(lambda: {'total': 0, 'natural_score': 0, 'patterns': []})
    
    for pattern in patterns:
        # Determine domain from source file
        source = pattern.get('source_file', '')
        if 'calculus' in source:
            domain = 'Calculus'
        elif 'basic' in source:
            domain = 'Basic Math'
        elif 'algebra' in source:
            domain = 'Algebra'
        elif 'special' in source:
            domain = 'Special Symbols'
        else:
            domain = 'Other'
            
        naturalness = evaluate_naturalness(pattern)
        
        domain_stats[domain]['total'] += 1
        domain_stats[domain]['natural_score'] += naturalness
        domain_stats[domain]['patterns'].append({
            'id': pattern.get('id', 'unknown'),
            'template': pattern.get('output_template', ''),
            'naturalness': naturalness,
            'file': source
        })
        
    return domain_stats

def test_specific_improvements():
    """Test specific patterns that were improved in Stage 1"""
    test_cases = [
        {
            'description': 'Basic derivative (Leibniz notation)',
            'pattern_id': 'derivative_leibniz',
            'expected_improvement': 'Should say "the derivative of X with respect to Y"',
            'target_score': 5
        },
        {
            'description': 'Basic integral',
            'pattern_id': 'integral_indefinite_basic', 
            'expected_improvement': 'Should say "the integral of X with respect to Y"',
            'target_score': 5
        },
        {
            'description': 'Numeric fraction',
            'pattern_id': 'fraction_numeric',
            'expected_improvement': 'Should say "the fraction X over Y"',
            'target_score': 4
        },
        {
            'description': 'Partial derivative',
            'pattern_id': 'partial_derivative_basic',
            'expected_improvement': 'Should say "the partial derivative of X with respect to Y"',
            'target_score': 5
        }
    ]
    
    patterns = load_all_patterns()
    pattern_dict = {p.get('id'): p for p in patterns}
    
    print("\n" + "="*80)
    print("STAGE 1 SPECIFIC IMPROVEMENTS TEST")
    print("="*80)
    
    improvements_successful = 0
    total_tests = len(test_cases)
    
    for test in test_cases:
        pattern_id = test['pattern_id']
        target_score = test['target_score']
        
        if pattern_id in pattern_dict:
            pattern = pattern_dict[pattern_id]
            actual_score = evaluate_naturalness(pattern)
            template = pattern.get('output_template', 'N/A')
            
            success = actual_score >= target_score
            if success:
                improvements_successful += 1
                
            print(f"\n✓ {test['description']}")
            print(f"   Pattern ID: {pattern_id}")
            print(f"   Template: '{template}'")
            print(f"   Naturalness Score: {actual_score}/6 (target: {target_score})")
            print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"   Expected: {test['expected_improvement']}")
        else:
            print(f"\n❌ Pattern '{pattern_id}' not found!")
            
    success_rate = (improvements_successful / total_tests) * 100
    print(f"\nStage 1 Improvements Success Rate: {success_rate:.1f}% ({improvements_successful}/{total_tests})")
    
    return success_rate >= 80  # 80% of specific improvements should pass

def main():
    """Main test function"""
    print("🧪 PHASE 3.5 STAGE 1 NATURALNESS TEST")
    print("="*60)
    print("Target: Achieve 60% overall natural speech quality")
    print("Focus: Enhanced derivatives, integrals, fractions, and basic operations")
    
    # Load all patterns
    patterns = load_all_patterns()
    print(f"\n📊 Loaded {len(patterns)} patterns from {len(set(p.get('source_file', '') for p in patterns))} files")
    
    # Calculate overall naturalness
    total_score = 0
    max_possible_score = len(patterns) * 6
    natural_patterns = 0
    
    for pattern in patterns:
        score = evaluate_naturalness(pattern)
        total_score += score
        if score >= 4:  # Consider 4+ as "natural"
            natural_patterns += 1
    
    overall_naturalness = (total_score / max_possible_score) * 100
    natural_percentage = (natural_patterns / len(patterns)) * 100
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Total Naturalness Score: {overall_naturalness:.1f}%")
    print(f"   Patterns Scoring 4+/6: {natural_percentage:.1f}% ({natural_patterns}/{len(patterns)})")
    
    # Domain breakdown
    domain_stats = calculate_domain_statistics(patterns)
    
    print(f"\n📈 DOMAIN BREAKDOWN:")
    for domain, stats in domain_stats.items():
        avg_score = stats['natural_score'] / stats['total'] if stats['total'] > 0 else 0
        domain_percentage = (avg_score / 6) * 100
        print(f"   {domain:15} {domain_percentage:5.1f}% ({stats['total']} patterns)")
    
    # Test specific improvements
    specific_improvements_pass = test_specific_improvements()
    
    # Final assessment
    print(f"\n🏆 STAGE 1 ASSESSMENT:")
    stage1_target_met = overall_naturalness >= 60.0
    print(f"   Target Naturalness (60%): {'✅ MET' if stage1_target_met else '❌ NOT MET'}")
    print(f"   Actual Naturalness: {overall_naturalness:.1f}%")
    print(f"   Specific Improvements: {'✅ PASS' if specific_improvements_pass else '❌ FAIL'}")
    
    # Detailed recommendations
    if not stage1_target_met:
        print(f"\n🔧 RECOMMENDATIONS FOR IMPROVEMENT:")
        
        # Find lowest scoring domains
        lowest_domains = sorted(domain_stats.items(), 
                              key=lambda x: x[1]['natural_score']/x[1]['total'])[:2]
        
        for domain, stats in lowest_domains:
            avg_score = stats['natural_score'] / stats['total']
            print(f"   • Focus on {domain} domain (current: {(avg_score/6)*100:.1f}%)")
            
            # Show worst patterns in this domain
            worst_patterns = sorted(stats['patterns'], key=lambda x: x['naturalness'])[:3]
            for p in worst_patterns:
                if p['naturalness'] < 3:
                    print(f"     - Improve '{p['id']}': '{p['template']}'")
    
    print(f"\n{'='*60}")
    
    if stage1_target_met and specific_improvements_pass:
        print("🎉 STAGE 1 COMPLETE! Ready to proceed to Stage 2")
        return True
    else:
        print("⚠️  STAGE 1 NEEDS MORE WORK")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)