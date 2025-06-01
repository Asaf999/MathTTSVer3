#!/usr/bin/env python3
"""
Stage 2 Natural Speech Quality Test
Tests the Stage 2 improvements: context awareness, professor-style, audience adaptation
Target: 80% natural speech quality
"""

import os
import sys
import yaml
import re
from pathlib import Path
from collections import defaultdict

def load_all_patterns():
    """Load all pattern files including new Stage 2 patterns"""
    patterns_dir = Path(__file__).parent / "patterns"
    all_patterns = []
    
    # Pattern files to analyze (including new Stage 2 files)
    pattern_files = [
        "calculus/derivatives.yaml",
        "calculus/integrals.yaml", 
        "calculus/limits_series.yaml",
        "basic/fractions.yaml",
        "basic/arithmetic.yaml",
        "basic/powers_roots.yaml",
        "algebra/equations.yaml",
        "special/symbols_greek.yaml",
        "educational/professor_style.yaml",  # New Stage 2
        "audience_adaptations/elementary.yaml",  # New Stage 2
        "audience_adaptations/undergraduate.yaml",  # New Stage 2
        "audience_adaptations/graduate.yaml",  # New Stage 2
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
                print(f"Warning: Error loading {file_path}: {e}")
                
    return all_patterns

def evaluate_stage2_naturalness(pattern):
    """
    Enhanced naturalness evaluation for Stage 2 features
    Evaluates context awareness, professor style, and audience adaptation
    Returns a score from 0-6 (6 being most natural)
    """
    if 'output_template' not in pattern:
        return 0
        
    template = pattern['output_template'].lower()
    score = 0
    max_score = 6
    
    # Get existing naturalness score if available
    if 'naturalness_score' in pattern:
        return min(pattern['naturalness_score'], max_score)
    
    # 1. Natural mathematical language (2 points)
    natural_phrases = [
        "the derivative of", "the integral", "with respect to", 
        "the fraction", "raised to", "to the power of",
        "squared", "cubed", "the limit", "approaches",
        "we have", "let us", "consider", "therefore"
    ]
    if any(phrase in template for phrase in natural_phrases):
        score += 2
    
    # 2. Context awareness (1 point)
    contexts = pattern.get('contexts', [])
    if contexts and any(ctx in ['educational', 'step_by_step', 'explanation'] for ctx in contexts):
        score += 1
        
    # 3. Professor-style language (1 point)
    professor_phrases = [
        "we have", "let us", "consider", "we observe", "we define",
        "therefore", "thus", "hence", "we evaluate", "applying"
    ]
    if any(phrase in template for phrase in professor_phrases):
        score += 1
        
    # 4. Audience appropriateness (1 point)
    audience = pattern.get('audience', '')
    if audience or 'audience_' in pattern.get('source_file', ''):
        score += 1
        
    # 5. Advanced natural flow (1 point)
    if len(template.split()) >= 4 and not re.search(r'\\[0-9]\\[0-9]', template):
        score += 1
    
    return min(score, max_score)

def calculate_stage2_statistics(patterns):
    """Calculate naturalness statistics with Stage 2 categorization"""
    domain_stats = defaultdict(lambda: {'total': 0, 'natural_score': 0, 'patterns': []})
    
    for pattern in patterns:
        # Enhanced domain classification for Stage 2
        source = pattern.get('source_file', '')
        
        if 'calculus' in source:
            domain = 'Calculus'
        elif 'basic' in source:
            domain = 'Basic Math'
        elif 'algebra' in source:
            domain = 'Algebra'
        elif 'special' in source:
            domain = 'Special Symbols'
        elif 'educational' in source:
            domain = 'Educational/Professor Style'  # New Stage 2
        elif 'audience_adaptations' in source:
            domain = 'Audience Adaptations'  # New Stage 2
        else:
            domain = 'Other'
            
        naturalness = evaluate_stage2_naturalness(pattern)
        
        domain_stats[domain]['total'] += 1
        domain_stats[domain]['natural_score'] += naturalness
        domain_stats[domain]['patterns'].append({
            'id': pattern.get('id', 'unknown'),
            'template': pattern.get('output_template', ''),
            'naturalness': naturalness,
            'file': source,
            'contexts': pattern.get('contexts', []),
            'audience': pattern.get('audience', '')
        })
        
    return domain_stats

def test_stage2_specific_improvements():
    """Test specific Stage 2 enhancements"""
    test_cases = [
        {
            'description': 'Context-aware Greek letter (Alpha as parameter)',
            'pattern_id': 'alpha_parameter',
            'expected_improvement': 'Should say "the parameter alpha" in statistical contexts',
            'target_score': 6
        },
        {
            'description': 'Professor-style equation introduction',
            'pattern_id': 'equation_introduction',
            'expected_improvement': 'Should say "we have the equation X equals Y"',
            'target_score': 6
        },
        {
            'description': 'Educational definite integral',
            'pattern_id': 'integral_definite_educational',
            'expected_improvement': 'Should say "we evaluate the definite integral..."',
            'target_score': 6
        },
        {
            'description': 'Chain rule educational explanation',
            'pattern_id': 'derivative_chain_rule_educational',
            'expected_improvement': 'Should say "by the chain rule, the derivative..."',
            'target_score': 6
        },
        {
            'description': 'Undergraduate-level derivative explanation',
            'pattern_id': 'derivative_undergraduate_explanation',
            'expected_improvement': 'Should explain rate of change concept',
            'target_score': 6
        }
    ]
    
    patterns = load_all_patterns()
    pattern_dict = {p.get('id'): p for p in patterns}
    
    print("\n" + "="*80)
    print("STAGE 2 SPECIFIC IMPROVEMENTS TEST")
    print("="*80)
    
    improvements_successful = 0
    total_tests = len(test_cases)
    
    for test in test_cases:
        pattern_id = test['pattern_id']
        target_score = test['target_score']
        
        if pattern_id in pattern_dict:
            pattern = pattern_dict[pattern_id]
            actual_score = evaluate_stage2_naturalness(pattern)
            template = pattern.get('output_template', 'N/A')
            contexts = pattern.get('contexts', [])
            audience = pattern.get('audience', 'N/A')
            
            success = actual_score >= target_score
            if success:
                improvements_successful += 1
                
            print(f"\n✓ {test['description']}")
            print(f"   Pattern ID: {pattern_id}")
            print(f"   Template: '{template}'")
            print(f"   Contexts: {contexts}")
            print(f"   Audience: {audience}")
            print(f"   Naturalness Score: {actual_score}/6 (target: {target_score})")
            print(f"   Status: {'✅ PASS' if success else '❌ FAIL'}")
            print(f"   Expected: {test['expected_improvement']}")
        else:
            print(f"\n❌ Pattern '{pattern_id}' not found!")
            
    success_rate = (improvements_successful / total_tests) * 100
    print(f"\nStage 2 Improvements Success Rate: {success_rate:.1f}% ({improvements_successful}/{total_tests})")
    
    return success_rate >= 80  # 80% of specific improvements should pass

def analyze_stage2_features(patterns):
    """Analyze Stage 2 specific features"""
    
    context_aware_patterns = 0
    professor_style_patterns = 0
    audience_adapted_patterns = 0
    educational_patterns = 0
    
    for pattern in patterns:
        contexts = pattern.get('contexts', [])
        template = pattern.get('output_template', '').lower()
        audience = pattern.get('audience', '')
        
        # Count context-aware patterns
        if contexts:
            context_aware_patterns += 1
            
        # Count professor-style patterns
        professor_phrases = ['we have', 'let us', 'consider', 'we observe', 'therefore']
        if any(phrase in template for phrase in professor_phrases):
            professor_style_patterns += 1
            
        # Count audience-adapted patterns
        if audience or 'audience_' in pattern.get('source_file', ''):
            audience_adapted_patterns += 1
            
        # Count educational patterns
        if 'educational' in pattern.get('source_file', '') or 'explanation' in contexts:
            educational_patterns += 1
    
    total_patterns = len(patterns)
    
    print(f"\n📊 STAGE 2 FEATURE ANALYSIS:")
    print(f"   Context-Aware Patterns: {context_aware_patterns}/{total_patterns} ({(context_aware_patterns/total_patterns)*100:.1f}%)")
    print(f"   Professor-Style Patterns: {professor_style_patterns}/{total_patterns} ({(professor_style_patterns/total_patterns)*100:.1f}%)")
    print(f"   Audience-Adapted Patterns: {audience_adapted_patterns}/{total_patterns} ({(audience_adapted_patterns/total_patterns)*100:.1f}%)")
    print(f"   Educational Patterns: {educational_patterns}/{total_patterns} ({(educational_patterns/total_patterns)*100:.1f}%)")

def main():
    """Main test function for Stage 2"""
    print("🧪 PHASE 3.5 STAGE 2 NATURALNESS TEST")
    print("="*60)
    print("Target: Achieve 80% overall natural speech quality")
    print("Focus: Context awareness, professor-style, audience adaptation")
    
    # Load all patterns including Stage 2 additions
    patterns = load_all_patterns()
    print(f"\n📊 Loaded {len(patterns)} patterns from {len(set(p.get('source_file', '') for p in patterns))} files")
    
    # Calculate overall naturalness with Stage 2 evaluation
    total_score = 0
    max_possible_score = len(patterns) * 6
    natural_patterns = 0
    
    for pattern in patterns:
        score = evaluate_stage2_naturalness(pattern)
        total_score += score
        if score >= 4:  # Consider 4+ as "natural"
            natural_patterns += 1
    
    overall_naturalness = (total_score / max_possible_score) * 100
    natural_percentage = (natural_patterns / len(patterns)) * 100
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Total Naturalness Score: {overall_naturalness:.1f}%")
    print(f"   Patterns Scoring 4+/6: {natural_percentage:.1f}% ({natural_patterns}/{len(patterns)})")
    
    # Enhanced domain breakdown
    domain_stats = calculate_stage2_statistics(patterns)
    
    print(f"\n📈 DOMAIN BREAKDOWN:")
    for domain, stats in domain_stats.items():
        avg_score = stats['natural_score'] / stats['total'] if stats['total'] > 0 else 0
        domain_percentage = (avg_score / 6) * 100
        print(f"   {domain:25} {domain_percentage:5.1f}% ({stats['total']} patterns)")
    
    # Analyze Stage 2 specific features
    analyze_stage2_features(patterns)
    
    # Test specific Stage 2 improvements
    specific_improvements_pass = test_stage2_specific_improvements()
    
    # Final assessment
    print(f"\n🏆 STAGE 2 ASSESSMENT:")
    stage2_target_met = overall_naturalness >= 80.0
    print(f"   Target Naturalness (80%): {'✅ MET' if stage2_target_met else '❌ NOT MET'}")
    print(f"   Actual Naturalness: {overall_naturalness:.1f}%")
    print(f"   Specific Improvements: {'✅ PASS' if specific_improvements_pass else '❌ FAIL'}")
    
    # Improvement recommendations
    if not stage2_target_met:
        print(f"\n🔧 RECOMMENDATIONS FOR STAGE 2 IMPROVEMENT:")
        
        # Find domains that need more work
        lowest_domains = sorted(domain_stats.items(), 
                              key=lambda x: x[1]['natural_score']/x[1]['total'])[:2]
        
        for domain, stats in lowest_domains:
            avg_score = stats['natural_score'] / stats['total']
            if avg_score < 4.5:  # Below 75% naturalness
                print(f"   • Enhance {domain} domain (current: {(avg_score/6)*100:.1f}%)")
                
                # Show patterns that need context awareness
                needs_improvement = [p for p in stats['patterns'] if p['naturalness'] < 4][:3]
                for p in needs_improvement:
                    print(f"     - Add context to '{p['id']}': '{p['template']}'")
    
    print(f"\n{'='*60}")
    
    if stage2_target_met and specific_improvements_pass:
        print("🎉 STAGE 2 COMPLETE! Ready to proceed to Stage 3")
        return True
    else:
        print("⚠️  STAGE 2 NEEDS MORE WORK")
        print(f"\nProgress Summary:")
        print(f"   Stage 1 Achievement: 55.8% naturalness")
        print(f"   Stage 2 Achievement: {overall_naturalness:.1f}% naturalness")
        print(f"   Improvement: +{overall_naturalness - 55.8:.1f} percentage points")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)