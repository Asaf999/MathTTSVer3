# MathTTS Pattern Domain-Specific Language (DSL)

## Overview

The MathTTS Pattern DSL provides a declarative way to define mathematical pattern transformations. Patterns are defined in YAML format with a rich set of features for controlling pronunciation, context, and application rules.

## Pattern Structure

### Basic Pattern

```yaml
pattern:
  id: "fraction_half"
  name: "Special Fraction 1/2"
  pattern: "\\frac{1}{2}"
  output_template: "one half"
  priority: 1500
  domain: "general"
```

### Complete Pattern

```yaml
pattern:
  # Identification
  id: "derivative_chain_rule"
  name: "Chain Rule Derivative"
  description: "Derivative of composite function using chain rule"
  version: "1.0.0"
  author: "math_team"
  
  # Pattern matching
  pattern: "\\frac{d}{dx}\\s*f\\(g\\(x\\)\\)"
  pattern_type: "REGEX"  # REGEX, LITERAL, TEMPLATE, COMPOSITE
  
  # Output generation
  output_template: "the derivative of f of g of x with respect to x"
  
  # Processing control
  priority: 1400  # 0-2000, higher = processed first
  domain: "calculus"  # Mathematical domain
  contexts: ["inline", "equation"]  # Where pattern applies
  active: true  # Enable/disable pattern
  
  # Conditional application
  conditions:
    - type: "preceding"
      value: "="
      negate: false
    - type: "context"
      value: "theorem"
      negate: true
  
  # Pronunciation control
  pronunciation_hints:
    emphasis: "derivative"  # Word to emphasize
    pause_before: 200  # Milliseconds
    pause_after: 100
    rate: 0.9  # Speaking rate (0.5-2.0)
    pitch: 1.1  # Pitch adjustment
    volume: 1.0  # Volume level
  
  # Examples for testing
  examples:
    - input: "\\frac{d}{dx} f(g(x))"
      output: "the derivative of f of g of x with respect to x"
    - input: "y = \\frac{d}{dx} f(g(x))"
      output: "y equals the derivative of f of g of x with respect to x"
  
  # Categorization
  tags: ["derivative", "chain-rule", "calculus", "advanced"]
```

## Pattern Types

### 1. REGEX Patterns

Most flexible, using regular expressions with capture groups:

```yaml
pattern: "\\sum_{([^}]+)}^{([^}]+)}\\s*([^{]+)"
output_template: "the sum from \\1 to \\2 of \\3"
```

### 2. LITERAL Patterns

Simple string matching:

```yaml
pattern_type: "LITERAL"
pattern: "\\pi"
output_template: "pi"
```

### 3. TEMPLATE Patterns

Use template variables (future feature):

```yaml
pattern_type: "TEMPLATE"
pattern: "{{fraction}}"
output_template: "{{numerator}} over {{denominator}}"
```

### 4. COMPOSITE Patterns

Combine multiple patterns (future feature):

```yaml
pattern_type: "COMPOSITE"
components:
  - ref: "integral_bounds"
  - ref: "integral_expression"
```

## Priority System

Patterns are processed in priority order:

- **1500-2000**: Critical patterns (special cases)
- **1000-1499**: High priority (domain-specific)
- **500-999**: Medium priority (general patterns)
- **0-499**: Low priority (fallbacks)

```yaml
# Special fraction - highest priority
pattern:
  pattern: "\\frac{1}{2}"
  priority: 1500
  
# General fraction - lower priority
pattern:
  pattern: "\\frac{([^}]+)}{([^}]+)}"
  priority: 1000
```

## Domains

Mathematical domains for pattern organization:

- `general`: Common mathematical notation
- `algebra`: Algebraic expressions
- `calculus`: Derivatives, integrals, limits
- `linear_algebra`: Matrices, vectors
- `statistics`: Probability, statistics
- `set_theory`: Sets, relations
- `logic`: Logical expressions
- `number_theory`: Number theoretic notation

## Contexts

Where patterns should be applied:

- `inline`: Inline math ($...$)
- `display`: Display math ($$...$$)
- `equation`: Numbered equations
- `theorem`: Inside theorem environments
- `proof`: Inside proofs
- `ANY`: Apply in any context

```yaml
contexts: ["inline", "display"]  # Only in inline or display math
```

## Conditions

Control when patterns are applied:

### Preceding Text

```yaml
conditions:
  - type: "preceding"
    value: "where"
    negate: false  # Apply if preceded by "where"
```

### Following Text

```yaml
conditions:
  - type: "following"
    value: "."
    negate: true  # Don't apply if followed by period
```

### Contains

```yaml
conditions:
  - type: "contains"
    value: "\\begin{array}"
    negate: true  # Don't apply if expression contains array
```

### Context Type

```yaml
conditions:
  - type: "context"
    value: "definition"
    negate: false  # Only apply in definitions
```

## Pronunciation Hints

Fine-tune speech output:

```yaml
pronunciation_hints:
  # Emphasis on specific words
  emphasis: "important"
  
  # Timing control (milliseconds)
  pause_before: 200
  pause_after: 100
  
  # Voice modulation
  rate: 0.9      # Slower speech (default: 1.0)
  pitch: 1.1     # Higher pitch (default: 1.0)
  volume: 1.2    # Louder (default: 1.0)
  
  # Additional SSML hints
  say_as: "ordinal"  # Interpret as ordinal number
  phoneme: "təˈmeɪtoʊ"  # IPA pronunciation
```

## Advanced Features

### Pattern References

Reference other patterns:

```yaml
pattern:
  id: "derivative_fraction"
  pattern: "\\frac{d{{content}}}{dx}"
  output_template: "the derivative of {{content}} with respect to x"
  references:
    content: "fraction_general"  # Use another pattern for content
```

### Pattern Inheritance

Extend existing patterns:

```yaml
pattern:
  id: "derivative_second_special"
  extends: "derivative_second"
  output_template: "the second derivative of \\1"  # Override
  priority: 1600  # Higher priority than parent
```

### Conditional Output

Different outputs based on conditions:

```yaml
output_variants:
  - condition: 
      type: "audience"
      value: "elementary"
    output: "\\1 divided by \\2"
  - condition:
      type: "audience" 
      value: "research"
    output: "\\1 over \\2"
  - output: "\\1 over \\2"  # Default
```

### ML Confidence

Machine learning integration:

```yaml
ml_hints:
  min_confidence: 0.8  # Only apply if ML confidence > 0.8
  training_examples: 50  # Number of examples for training
  allow_learning: true  # Allow pattern to be updated by ML
```

## Pattern Organization

### File Structure

```
patterns/
├── core/
│   ├── fractions.yaml
│   ├── operations.yaml
│   └── symbols.yaml
├── domains/
│   ├── calculus.yaml
│   ├── linear_algebra.yaml
│   └── statistics.yaml
├── languages/
│   ├── en_US.yaml
│   └── en_GB.yaml
└── custom/
    └── user_patterns.yaml
```

### Pattern Collections

Group related patterns:

```yaml
collection:
  name: "Calculus Essentials"
  description: "Core calculus patterns"
  version: "2.0.0"
  patterns:
    - ref: "derivative_basic"
    - ref: "integral_basic"
    - ref: "limit_basic"
```

## Testing Patterns

### Pattern Test File

```yaml
pattern_tests:
  - pattern_id: "fraction_half"
    tests:
      - input: "\\frac{1}{2}"
        expected: "one half"
      - input: "x = \\frac{1}{2}"
        expected: "x equals one half"
    contexts:
      - type: "inline"
      - type: "display"
```

### Performance Benchmarks

```yaml
benchmarks:
  - pattern_id: "complex_integral"
    max_time_ms: 0.5
    test_expressions: 1000
```

## Best Practices

1. **Specificity First**: Create specific patterns for common cases
2. **Priority Ordering**: Higher priority for more specific patterns
3. **Clear Names**: Use descriptive pattern names
4. **Test Coverage**: Include examples for all major cases
5. **Documentation**: Add descriptions for complex patterns
6. **Version Control**: Track pattern versions
7. **Performance**: Avoid overly complex regex
8. **Modularity**: One pattern per concept

## Pattern Validation

Patterns are validated for:

- Valid regex syntax
- Matching capture groups in output
- Priority range (0-2000)
- Valid domain
- At least one context
- Non-empty output template

## Future DSL Extensions

Planned enhancements:

1. **Pattern Macros**: Reusable pattern fragments
2. **Pattern Functions**: Transform capture groups
3. **Conditional Capture**: Context-aware groups
4. **Pattern Composition**: Build complex from simple
5. **Pattern Analytics**: Usage statistics
6. **A/B Testing**: Compare pattern variants
7. **User Feedback**: Rating integration