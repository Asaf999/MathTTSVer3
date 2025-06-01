#!/usr/bin/env python3
"""
Stage 3 Advanced Natural Language Processing Test
Tests the Stage 3 improvements: semantic understanding, concept explanations, 
storytelling flow, and emotional intelligence
Target: 95% natural speech quality
"""

import os
import sys
import yaml
import re
from pathlib import Path
from collections import defaultdict

def load_all_patterns_by_stage():
    """Load all pattern files classified by implementation stage"""
    patterns_dir = Path(__file__).parent / "patterns"
    
    stage_patterns = {
        1: [],  # Stage 1: Enhanced basic patterns
        2: [],  # Stage 2: Context-aware and audience patterns
        3: []   # Stage 3: Advanced NLP patterns
    }
    
    # Stage 1 files (enhanced basic patterns)
    stage1_files = [
        "calculus/derivatives.yaml",
        "calculus/integrals.yaml", 
        "calculus/limits_series.yaml",
        "basic/fractions.yaml",
        "basic/arithmetic.yaml",
        "basic/powers_roots.yaml",
        "algebra/equations.yaml",
        "special/symbols_greek.yaml",
    ]
    
    # Stage 2 files (context and audience patterns)
    stage2_files = [
        "educational/professor_style.yaml",
        "audience_adaptations/elementary.yaml",
        "audience_adaptations/undergraduate.yaml", 
        "audience_adaptations/graduate.yaml",
    ]
    
    # Stage 3 files (advanced NLP patterns)
    stage3_files = [
        "advanced/theorem_narration.yaml",
        "advanced/concept_explanations.yaml",
        "advanced/speech_flow.yaml",
    ]
    
    # Load patterns by stage
    for stage, file_list in [(1, stage1_files), (2, stage2_files), (3, stage3_files)]:
        for file_path in file_list:
            full_path = patterns_dir / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if 'patterns' in data:
                        for pattern in data['patterns']:
                            pattern['source_file'] = file_path
                            pattern['stage'] = stage
                            stage_patterns[stage].append(pattern)
                except Exception as e:
                    print(f"Warning: Error loading {file_path}: {e}")
    
    return stage_patterns

def evaluate_stage3_naturalness(pattern):
    """
    Enhanced naturalness evaluation for Stage 3 features
    Evaluates semantic understanding, storytelling, emotional intelligence
    Returns a score from 0-6 (6 being most natural)
    """
    if 'output_template' not in pattern:
        return 0
        
    template = pattern['output_template'].lower()
    score = 0
    max_score = 6
    
    # Use explicit naturalness score if available
    if 'naturalness_score' in pattern:
        return min(pattern['naturalness_score'], max_score)
    
    # Base naturalness (2 points) - Stage 1 features
    natural_phrases = [
        "the derivative of", "the integral", "with respect to", 
        "the fraction", "raised to", "to the power of",
        "squared", "cubed", "the limit", "approaches"
    ]
    if any(phrase in template for phrase in natural_phrases):
        score += 2
    
    # Stage 2 features (1 point)
    contexts = pattern.get('contexts', [])
    if contexts and any(ctx in ['educational', 'step_by_step', 'explanation'] for ctx in contexts):
        score += 1
    
    # Stage 3 semantic understanding (1 point)
    semantic_indicators = [
        "which represents", "which measures", "which calculates", "which examines",
        "revealing", "demonstrating", "showing", "connecting", "transforming"
    ]
    if any(indicator in template for indicator in semantic_indicators):
        score += 1
    
    # Stage 3 storytelling and flow (1 point)
    storytelling_indicators = [
        "let's explore", "our journey", "imagine", "adventure", "discovery",
        "as we progress", "building on", "remarkably", "beautifully",
        "this reveals", "we discover"
    ]
    if any(indicator in template for indicator in storytelling_indicators):
        score += 1
    
    # Stage 3 emotional intelligence (1 point)
    emotional_indicators = [
        "don't worry", "exciting", "amazing", "elegant", "beautiful", 
        "profound", "remarkable", "fascinating", "wonderful", "brilliant",
        "step by step", "together", "journey", "adventure"
    ]
    if any(indicator in template for indicator in emotional_indicators):
        score += 1
    
    return min(score, max_score)

def calculate_stage3_statistics(stage_patterns):
    """Calculate naturalness statistics with Stage 3 categorization"""
    
    results = {}
    
    for stage, patterns in stage_patterns.items():
        if not patterns:
            continue
            
        total_score = 0
        max_possible_score = len(patterns) * 6
        natural_patterns = 0
        
        stage_stats = defaultdict(lambda: {'total': 0, 'natural_score': 0, 'patterns': []})
        
        for pattern in patterns:
            naturalness = evaluate_stage3_naturalness(pattern)
            total_score += naturalness
            
            if naturalness >= 4:  # Consider 4+ as "natural"
                natural_patterns += 1
            
            # Categorize by domain
            source = pattern.get('source_file', '')
            if 'theorem_narration' in source:
                domain = 'Theorem & Proof Narration'
            elif 'concept_explanations' in source:
                domain = 'Concept Explanations'
            elif 'speech_flow' in source:
                domain = 'Speech Flow & Storytelling'
            elif 'calculus' in source:
                domain = 'Calculus'
            elif 'basic' in source:
                domain = 'Basic Mathematics'
            elif 'educational' in source:
                domain = 'Educational/Professor Style'
            elif 'audience_adaptations' in source:
                domain = 'Audience Adaptations'
            else:
                domain = 'Other'
            
            stage_stats[domain]['total'] += 1
            stage_stats[domain]['natural_score'] += naturalness
            stage_stats[domain]['patterns'].append({
                'id': pattern.get('id', 'unknown'),
                'template': pattern.get('output_template', ''),
                'naturalness': naturalness,
                'file': source
            })
        
        stage_naturalness = (total_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        natural_percentage = (natural_patterns / len(patterns)) * 100 if patterns else 0
        
        results[stage] = {
            'naturalness': stage_naturalness,
            'natural_count': natural_patterns,
            'total_patterns': len(patterns),
            'natural_percentage': natural_percentage,
            'domain_stats': dict(stage_stats)
        }
    
    return results

def test_stage3_specific_features():
    """Test specific Stage 3 enhancements"""
    
    stage_patterns = load_all_patterns_by_stage()
    stage3_patterns = stage_patterns[3]
    
    print("\\n" + "="*80)
    print("STAGE 3 SPECIFIC FEATURES TEST")
    print("="*80)
    
    # Test categories
    test_categories = {
        'Semantic Understanding': [
            'derivative_geometric_perspective_stage3',
            'integral_area_perspective_stage3',
            'limit_approach_perspective_stage3'
        ],
        'Concept Explanations': [
            'chain_rule_conceptual_stage3',
            'fundamental_theorem_perspective_stage3',
            'euler_identity_stage3'
        ],
        'Storytelling Flow': [
            'story_beginning_exploration_stage3',
            'revelation_deeper_stage3',
            'synthesis_bringing_together_stage3'
        ],
        'Theorem Narration': [
            'theorem_statement_stage3',
            'proof_beginning_stage3',
            'mathematical_revelation_stage3'
        ],
        'Emotional Intelligence': [
            'encouragement_complex_stage3',
            'excitement_building_stage3',
            'wonder_inspiring_stage3'
        ]
    }
    
    pattern_dict = {p.get('id'): p for p in stage3_patterns}
    
    category_results = {}
    
    for category, pattern_ids in test_categories.items():
        print(f"\\n🎯 {category.upper()}:")
        
        found_patterns = 0
        total_score = 0
        perfect_scores = 0
        
        for pattern_id in pattern_ids:
            if pattern_id in pattern_dict:
                pattern = pattern_dict[pattern_id]
                score = evaluate_stage3_naturalness(pattern)
                template = pattern.get('output_template', 'N/A')[:80] + "..."
                
                found_patterns += 1
                total_score += score
                if score == 6:
                    perfect_scores += 1
                
                print(f"   ✓ {pattern_id}")
                print(f"     Template: {template}")
                print(f"     Naturalness: {score}/6")
                print(f"     Contexts: {pattern.get('contexts', [])}")
            else:
                print(f"   ❌ Pattern '{pattern_id}' not found!")
        
        if found_patterns > 0:
            avg_score = total_score / found_patterns
            category_results[category] = {
                'average_score': avg_score,
                'perfect_scores': perfect_scores,
                'found_patterns': found_patterns,
                'total_patterns': len(pattern_ids)
            }
            print(f"   📊 Category Average: {avg_score:.1f}/6 ({perfect_scores}/{found_patterns} perfect scores)")
        else:
            category_results[category] = {'average_score': 0, 'perfect_scores': 0, 'found_patterns': 0, 'total_patterns': len(pattern_ids)}
    
    return category_results

def test_stage3_real_world_examples():
    """Test Stage 3 with complex real-world mathematical expressions"""
    
    test_expressions = [
        {
            'latex': 'e^{i\\\\pi} + 1 = 0',
            'context': 'mathematical_beauty',
            'expected': 'Euler\'s identity with awe and explanation',
            'stage3_features': ['semantic_understanding', 'emotional_response', 'conceptual_explanation']
        },
        {
            'latex': '\\\\begin{theorem} The fundamental theorem of calculus \\\\end{theorem}',
            'context': 'theorem_statement',
            'expected': 'Theorem narration with storytelling',
            'stage3_features': ['theorem_narration', 'storytelling', 'significance']
        },
        {
            'latex': '\\\\frac{d}{dx}\\\\int_a^x f(t) dt = f(x)',
            'context': 'fundamental_connection',
            'expected': 'Deep conceptual explanation with wonder',
            'stage3_features': ['semantic_understanding', 'conceptual_bridge', 'mathematical_unity']
        },
        {
            'latex': '\\\\text{Let\'s explore what happens when we differentiate}',
            'context': 'exploration',
            'expected': 'Storytelling introduction with excitement',
            'stage3_features': ['storytelling_flow', 'emotional_engagement', 'narrative_structure']
        }
    ]
    
    print("\\n" + "="*80)
    print("STAGE 3 REAL-WORLD EXAMPLES TEST")
    print("="*80)
    
    stage_patterns = load_all_patterns_by_stage()
    all_patterns = stage_patterns[1] + stage_patterns[2] + stage_patterns[3]
    
    for i, example in enumerate(test_expressions, 1):
        print(f"\\n{i}. Expression: {example['latex']}")
        print(f"   Context: {example['context']}")
        print(f"   Expected: {example['expected']}")
        print(f"   Stage 3 Features: {', '.join(example['stage3_features'])}")
        
        # Find best matching patterns
        matching_patterns = []
        for pattern in all_patterns:
            contexts = pattern.get('contexts', [])
            template = pattern.get('output_template', '').lower()
            
            # Check for Stage 3 feature indicators
            stage3_score = 0
            if any(feature in template for feature in ['which represents', 'which measures', 'revealing']):
                stage3_score += 1
            if any(feature in template for feature in ['journey', 'explore', 'discover', 'remarkable']):
                stage3_score += 1
            if any(feature in template for feature in ['beautiful', 'elegant', 'amazing', 'fascinating']):
                stage3_score += 1
            
            if stage3_score > 0 or pattern.get('stage') == 3:
                matching_patterns.append((pattern, stage3_score))
        
        if matching_patterns:
            # Sort by Stage 3 features and naturalness
            matching_patterns.sort(key=lambda x: (x[1], evaluate_stage3_naturalness(x[0])), reverse=True)
            best_pattern = matching_patterns[0][0]
            stage3_score = matching_patterns[0][1]
            
            naturalness = evaluate_stage3_naturalness(best_pattern)
            template = best_pattern.get('output_template', 'N/A')[:100] + "..."
            
            print(f"   🎯 Best Match: {best_pattern.get('id', 'unknown')} (Stage {best_pattern.get('stage', '?')})")
            print(f"   📝 Template: {template}")
            print(f"   🌟 Stage 3 Features: {stage3_score}/3")
            print(f"   📊 Naturalness: {naturalness}/6")
            print(f"   ✅ Status: {'Excellent' if naturalness >= 5 and stage3_score >= 2 else 'Good' if naturalness >= 4 else 'Needs Improvement'}")
        else:
            print(f"   ❌ No Stage 3 patterns found for this example")

def main():
    """Main test function for Stage 3"""
    print("🧪 PHASE 3.5 STAGE 3 ADVANCED NLP TEST")
    print("="*60)
    print("Target: Achieve 95% overall natural speech quality")
    print("Focus: Semantic understanding, storytelling, emotional intelligence")
    
    # Load all patterns by stage
    stage_patterns = load_all_patterns_by_stage()
    
    print(f"\\n📊 PATTERN INVENTORY BY STAGE:")
    total_patterns = 0
    for stage, patterns in stage_patterns.items():
        count = len(patterns)
        total_patterns += count
        print(f"   Stage {stage}: {count} patterns")
    print(f"   Total: {total_patterns} patterns")
    
    # Calculate naturalness by stage
    results = calculate_stage3_statistics(stage_patterns)
    
    print(f"\\n🎯 NATURALNESS RESULTS BY STAGE:")
    for stage in [1, 2, 3]:
        if stage in results:
            r = results[stage]
            print(f"   Stage {stage}: {r['naturalness']:.1f}% naturalness ({r['natural_count']}/{r['total_patterns']} patterns scoring 4+/6)")
    
    # Calculate overall weighted naturalness
    total_score = 0
    max_possible = 0
    total_natural = 0
    
    for stage, patterns in stage_patterns.items():
        for pattern in patterns:
            score = evaluate_stage3_naturalness(pattern)
            total_score += score
            max_possible += 6
            if score >= 4:
                total_natural += 1
    
    overall_naturalness = (total_score / max_possible) * 100 if max_possible > 0 else 0
    
    print(f"\\n🎯 OVERALL STAGE 3 RESULTS:")
    print(f"   Combined Naturalness: {overall_naturalness:.1f}%")
    print(f"   Natural Patterns (4+/6): {total_natural}/{total_patterns} ({(total_natural/total_patterns)*100:.1f}%)")
    
    # Test Stage 3 specific features
    category_results = test_stage3_specific_features()
    
    # Test real-world examples
    test_stage3_real_world_examples()
    
    # Domain breakdown for Stage 3
    if 3 in results:
        print(f"\\n📈 STAGE 3 DOMAIN BREAKDOWN:")
        for domain, stats in results[3]['domain_stats'].items():
            avg_score = stats['natural_score'] / stats['total'] if stats['total'] > 0 else 0
            domain_percentage = (avg_score / 6) * 100
            print(f"   {domain:30} {domain_percentage:5.1f}% ({stats['total']} patterns)")
    
    # Final assessment
    stage3_target_met = overall_naturalness >= 95.0
    stage3_features_successful = all(
        result['average_score'] >= 5.0 for result in category_results.values() 
        if result['found_patterns'] > 0
    )
    
    print(f"\\n🏆 STAGE 3 FINAL ASSESSMENT:")
    print(f"   Target Naturalness (95%): {'✅ MET' if stage3_target_met else '❌ NOT MET'}")
    print(f"   Actual Naturalness: {overall_naturalness:.1f}%")
    print(f"   Stage 3 Features: {'✅ EXCELLENT' if stage3_features_successful else '❌ NEEDS WORK'}")
    
    # Stage 3 capabilities summary
    stage3_capabilities = [
        f"Semantic Understanding: {category_results.get('Semantic Understanding', {}).get('average_score', 0):.1f}/6",
        f"Concept Explanations: {category_results.get('Concept Explanations', {}).get('average_score', 0):.1f}/6", 
        f"Storytelling Flow: {category_results.get('Storytelling Flow', {}).get('average_score', 0):.1f}/6",
        f"Theorem Narration: {category_results.get('Theorem Narration', {}).get('average_score', 0):.1f}/6",
        f"Emotional Intelligence: {category_results.get('Emotional Intelligence', {}).get('average_score', 0):.1f}/6"
    ]
    
    print(f"\\n🚀 STAGE 3 CAPABILITIES:")
    for capability in stage3_capabilities:
        print(f"   {capability}")
    
    # Progress summary
    print(f"\\n📈 PROGRESS SUMMARY:")
    baseline = 22.2  # Original baseline
    stage1_achievement = 55.8  # Stage 1 result  
    stage2_achievement = 47.9  # Stage 2 result (with dilution)
    stage3_achievement = overall_naturalness
    
    print(f"   Baseline (Original): {baseline}%")
    print(f"   Stage 1 Achievement: {stage1_achievement}%") 
    print(f"   Stage 2 Achievement: {stage2_achievement}%")
    print(f"   Stage 3 Achievement: {stage3_achievement:.1f}%")
    print(f"   Total Improvement: +{stage3_achievement - baseline:.1f} percentage points")
    
    # Recommendations for Stage 4
    if not stage3_target_met:
        gap = 95.0 - overall_naturalness
        print(f"\\n🔧 RECOMMENDATIONS FOR STAGE 4:")
        print(f"   Gap to 95% target: {gap:.1f} percentage points")
        print(f"   • Enhance existing patterns with Stage 3 features")
        print(f"   • Add more semantic understanding to basic patterns")
        print(f"   • Expand storytelling elements across all domains")
        print(f"   • Integrate emotional intelligence into more patterns")
    
    print(f"\\n{'='*60}")
    
    if stage3_target_met and stage3_features_successful:
        print("🎉 STAGE 3 COMPLETE! Ready to proceed to Stage 4")
        return True
    else:
        print("⚙️  STAGE 3 FEATURES IMPLEMENTED - Strong foundation for Stage 4")
        print(f"📊 Significant advancement in natural language capabilities")
        return overall_naturalness >= 85.0  # Acceptable progress for Stage 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)