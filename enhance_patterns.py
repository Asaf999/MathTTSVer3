#!/usr/bin/env python3
"""
Quick pattern enhancement script for Stage 1
"""

import re

def enhance_greek_patterns():
    """Enhance Greek letter patterns to be more natural"""
    
    # Read the file
    with open('patterns/special/symbols_greek.yaml', 'r') as f:
        content = f.read()
    
    # Greek letters to enhance (that aren't already enhanced)
    greek_letters = [
        'zeta', 'eta', 'theta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 
        'omicron', 'pi', 'rho', 'sigma', 'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega'
    ]
    
    for letter in greek_letters:
        # Find the pattern and replace the simple output with more natural one
        pattern = rf'(pattern: "\\\\{letter}"\s*\n\s*output_template: ")({letter})(")'
        replacement = rf'\1the Greek letter {letter}\3'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Write back
    with open('patterns/special/symbols_greek.yaml', 'w') as f:
        f.write(content)
    
    print("Enhanced Greek letter patterns")

def enhance_fraction_patterns():
    """Enhance more fraction patterns"""
    
    with open('patterns/basic/fractions.yaml', 'r') as f:
        content = f.read()
    
    # Add "the" to more fraction patterns
    patterns_to_enhance = [
        ('output_template: "\\\\1 over \\\\2"', 'output_template: "the fraction \\\\1 over \\\\2"'),
        ('output_template: "one half"', 'output_template: "the fraction one half"'),
        ('output_template: "one third"', 'output_template: "the fraction one third"'),
        ('output_template: "one quarter"', 'output_template: "the fraction one quarter"'),
    ]
    
    for old, new in patterns_to_enhance:
        content = content.replace(old, new)
    
    with open('patterns/basic/fractions.yaml', 'w') as f:
        f.write(content)
        
    print("Enhanced fraction patterns")

def enhance_power_patterns():
    """Enhance power patterns"""
    
    with open('patterns/basic/powers_roots.yaml', 'r') as f:
        content = f.read()
    
    # Enhance some power patterns
    enhancements = [
        ('output_template: "\\\\1 to the \\\\2"', 'output_template: "\\\\1 raised to the power of \\\\2"'),
        ('output_template: "\\\\1 to the negative \\\\2"', 'output_template: "\\\\1 raised to the negative power of \\\\2"'),
    ]
    
    for old, new in enhancements:
        content = content.replace(old, new)
    
    with open('patterns/basic/powers_roots.yaml', 'w') as f:
        f.write(content)
        
    print("Enhanced power patterns")

if __name__ == "__main__":
    enhance_greek_patterns()
    enhance_fraction_patterns()
    enhance_power_patterns()
    print("Pattern enhancement complete!")