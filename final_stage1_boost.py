#!/usr/bin/env python3
"""
Final boost to reach 60% naturalness for Stage 1
"""

def enhance_remaining_symbols():
    """Add natural enhancements to remaining symbol patterns"""
    
    # Read Greek symbols file
    with open('patterns/special/symbols_greek.yaml', 'r') as f:
        content = f.read()
    
    # Add more natural descriptions to remaining Greek letters
    replacements = [
        ('output_template: "zeta"', 'output_template: "the Greek letter zeta"'),
        ('output_template: "eta"', 'output_template: "the Greek letter eta"'),
        ('output_template: "theta"', 'output_template: "the Greek letter theta"'),
        ('output_template: "iota"', 'output_template: "the Greek letter iota"'),
        ('output_template: "kappa"', 'output_template: "the Greek letter kappa"'),
        ('output_template: "lambda"', 'output_template: "the Greek letter lambda"'),
        ('output_template: "mu"', 'output_template: "the Greek letter mu"'),
        ('output_template: "nu"', 'output_template: "the Greek letter nu"'),
        ('output_template: "xi"', 'output_template: "the Greek letter xi"'),
        ('output_template: "omicron"', 'output_template: "the Greek letter omicron"'),
        ('output_template: "pi"', 'output_template: "the Greek letter pi"'),
        ('output_template: "rho"', 'output_template: "the Greek letter rho"'),
        ('output_template: "sigma"', 'output_template: "the Greek letter sigma"'),
        ('output_template: "tau"', 'output_template: "the Greek letter tau"'),
        ('output_template: "upsilon"', 'output_template: "the Greek letter upsilon"'),
        ('output_template: "phi"', 'output_template: "the Greek letter phi"'),
        ('output_template: "chi"', 'output_template: "the Greek letter chi"'),
        ('output_template: "psi"', 'output_template: "the Greek letter psi"'),
        ('output_template: "omega"', 'output_template: "the Greek letter omega"'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write back
    with open('patterns/special/symbols_greek.yaml', 'w') as f:
        f.write(content)
    
    print("Enhanced remaining Greek letters")

def enhance_algebra_patterns():
    """Enhance algebra patterns"""
    
    with open('patterns/algebra/equations.yaml', 'r') as f:
        content = f.read()
    
    # Enhance more algebra patterns  
    replacements = [
        ('output_template: "\\\\1 \\\\2 \\\\3"', 'output_template: "the inequality \\\\1 \\\\2 \\\\3"'),
        ('output_template: "\\\\1 transpose"', 'output_template: "the transpose of matrix \\\\1"'),
        ('output_template: "\\\\1 inverse"', 'output_template: "the inverse of matrix \\\\1"'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open('patterns/algebra/equations.yaml', 'w') as f:
        f.write(content)
        
    print("Enhanced algebra patterns")

def enhance_more_basic_patterns():
    """Enhance more basic math patterns"""
    
    # Powers and roots
    with open('patterns/basic/powers_roots.yaml', 'r') as f:
        content = f.read()
    
    # Add more natural language to roots
    enhancements = [
        ('output_template: "square root of \\\\1"', 'output_template: "the square root of \\\\1"'),
        ('output_template: "cube root of \\\\1"', 'output_template: "the cube root of \\\\1"'),
        ('output_template: "\\\\2 root of \\\\1"', 'output_template: "the \\\\2 root of \\\\1"'),
    ]
    
    for old, new in enhancements:
        content = content.replace(old, new)
    
    with open('patterns/basic/powers_roots.yaml', 'w') as f:
        f.write(content)
    
    print("Enhanced roots patterns")

if __name__ == "__main__":
    enhance_remaining_symbols()
    enhance_algebra_patterns()
    enhance_more_basic_patterns()
    print("Final Stage 1 enhancement complete!")