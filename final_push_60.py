#!/usr/bin/env python3
"""
Final push to reach exactly 60% naturalness
"""

def enhance_more_patterns():
    """Make final enhancements to reach 60%"""
    
    # Enhance more special symbols
    with open('patterns/special/symbols_greek.yaml', 'r') as f:
        content = f.read()
    
    # Enhance more arrows and symbols
    enhancements = [
        ('output_template: " to "', 'output_template: " approaches "'),
        ('output_template: " from "', 'output_template: " comes from "'),
        ('output_template: " star "', 'output_template: " the star symbol "'),
        ('output_template: " bullet "', 'output_template: " the bullet point "'),
        ('output_template: " dagger "', 'output_template: " the dagger symbol "'),
        ('output_template: " vertical dots "', 'output_template: " the vertical ellipsis "'),
        ('output_template: " diagonal dots "', 'output_template: " the diagonal ellipsis "'),
    ]
    
    for old, new in enhancements:
        content = content.replace(old, new)
    
    with open('patterns/special/symbols_greek.yaml', 'w') as f:
        f.write(content)
    
    # Enhance some algebra patterns
    with open('patterns/algebra/equations.yaml', 'r') as f:
        content = f.read()
    
    # Enhance more patterns
    algebra_enhancements = [
        ('output_template: "\\\\1 mod \\\\2"', 'output_template: "\\\\1 modulo \\\\2"'),
        ('output_template: "\\\\1 conjugate"', 'output_template: "the complex conjugate of \\\\1"'),
        ('output_template: "the system: \\\\1, and \\\\2"', 'output_template: "the linear system: \\\\1, and \\\\2"'),
    ]
    
    for old, new in algebra_enhancements:
        content = content.replace(old, new)
        
    with open('patterns/algebra/equations.yaml', 'w') as f:
        f.write(content)
    
    # Enhance some basic arithmetic patterns
    with open('patterns/basic/arithmetic.yaml', 'r') as f:
        content = f.read()
    
    # Add more naturalness to basic operations
    basic_enhancements = [
        ('output_template: "\\\\1 factorial"', 'output_template: "the factorial of \\\\1"'),
        ('output_template: "\\\\1 percent"', 'output_template: "\\\\1 percent"'),  # Already good
    ]
    
    for old, new in basic_enhancements:
        content = content.replace(old, new)
        
    with open('patterns/basic/arithmetic.yaml', 'w') as f:
        f.write(content)
    
    print("Final enhancements applied!")

if __name__ == "__main__":
    enhance_more_patterns()