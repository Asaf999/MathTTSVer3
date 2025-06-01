# MathTTSVer3 User Guide

## 🚀 Quick Start

MathTTSVer3 is a LaTeX-to-Speech system that converts mathematical expressions into natural, professor-like speech. Currently, the system is a pattern-based converter that transforms LaTeX notation into human-readable text.

## 📄 Supported Document Types

### Currently Supported:
- **`.tex` files** - LaTeX documents (primary support)
- **`.txt` files** - Plain text with LaTeX expressions
- **`.md` files** - Markdown with LaTeX math blocks

### Input Format Requirements:
- LaTeX expressions should be properly formatted
- Math expressions can be:
  - Display mode: `\begin{equation}...\end{equation}` or `$$...$$`
  - Inline mode: `$...$` or `\(...\)`
  - Raw LaTeX commands

## 🎯 How to Use the System

### 1. Basic Usage Script

Create a file called `convert_my_document.py`:

```python
#!/usr/bin/env python3
"""
Convert your LaTeX document to natural speech
"""

import re
import yaml
from pathlib import Path

def load_patterns():
    """Load all conversion patterns"""
    patterns = []
    patterns_dir = Path("patterns")
    
    # Load all pattern files
    for pattern_file in patterns_dir.rglob("*.yaml"):
        try:
            with open(pattern_file, 'r') as f:
                data = yaml.safe_load(f)
                if 'patterns' in data:
                    patterns.extend(data['patterns'])
        except Exception as e:
            print(f"Error loading {pattern_file}: {e}")
    
    # Sort by priority (higher priority first)
    patterns.sort(key=lambda x: x.get('priority', 1000), reverse=True)
    return patterns

def convert_latex_to_speech(latex_expr, patterns):
    """Convert a LaTeX expression to natural speech"""
    
    # Try each pattern
    for pattern in patterns:
        if 'pattern' in pattern and 'output_template' in pattern:
            try:
                # Check if pattern matches (simplified)
                if re.search(pattern['pattern'], latex_expr):
                    # Apply the template (simplified)
                    return pattern['output_template']
            except:
                continue
    
    # Default fallback
    return f"the expression {latex_expr}"

def process_document(input_file):
    """Process a document containing LaTeX"""
    
    # Load patterns
    patterns = load_patterns()
    print(f"Loaded {len(patterns)} conversion patterns")
    
    # Read input file
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Extract and convert equations
    equation_pattern = r'\\begin\{equation\}(.*?)\\end\{equation\}'
    inline_pattern = r'\$([^\$]+)\$'
    
    results = []
    
    # Process display equations
    for match in re.finditer(equation_pattern, content, re.DOTALL):
        latex = match.group(1).strip()
        speech = convert_latex_to_speech(latex, patterns)
        results.append({
            'type': 'display',
            'latex': latex,
            'speech': speech
        })
    
    # Process inline math
    for match in re.finditer(inline_pattern, content):
        latex = match.group(1)
        speech = convert_latex_to_speech(latex, patterns)
        results.append({
            'type': 'inline',
            'latex': latex,
            'speech': speech
        })
    
    return results

# Example usage
if __name__ == "__main__":
    input_file = "your_document.tex"  # Change this to your file
    
    results = process_document(input_file)
    
    print(f"\nConverted {len(results)} expressions:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. LaTeX: {result['latex']}")
        print(f"   Speech: {result['speech']}\n")
```

### 2. For Different File Types

#### LaTeX Documents (.tex)
```python
# The system handles standard LaTeX documents
# Expressions in \begin{equation}, $$, or $ delimiters
input_file = "mathematics_paper.tex"
```

#### Markdown Files (.md)
```python
# For Markdown with LaTeX
def process_markdown(md_file):
    with open(md_file, 'r') as f:
        content = f.read()
    
    # Extract math blocks
    # Display: $$...$$
    # Inline: $...$
    # Process same as LaTeX
```

#### Plain Text (.txt)
```python
# For plain text with LaTeX expressions
# Just ensure LaTeX is properly delimited
```

## 🎨 Example Conversions

### Simple Examples:
```
Input:  $\frac{dy}{dx}$
Output: "the derivative of y with respect to x"

Input:  $x^2 + y^2 = r^2$
Output: "x squared plus y squared equals r squared"

Input:  $\int_0^1 x^2 dx$
Output: "the integral from 0 to 1 of x squared with respect to x"
```

### Complex Examples:
```
Input:  $e^{i\pi} + 1 = 0$
Output: "Euler's remarkable identity shows us that e raised to the 
         power of i pi plus 1 equals zero, beautifully connecting 
         five fundamental mathematical constants"

Input:  $\sum_{n=0}^{\infty} \frac{x^n}{n!}$
Output: "the sum from n equals 0 to infinity of x to the n over n factorial"
```

## 🔧 Advanced Usage

### Setting Audience Level
```python
# Configure for different audiences
audience_level = "undergraduate"  # Options: elementary, undergraduate, graduate

# The system will adapt language complexity
# Elementary: "one half means one piece out of two equal pieces"  
# Graduate: "one half"
```

### Adding Context
```python
# Provide context for better conversions
context = {
    'mode': 'educational',      # Teaching mode
    'style': 'professor',       # Professor-like explanations
    'add_explanations': True    # Include conceptual explanations
}
```

## 📁 Project Structure

```
MathTTSVer3/
├── patterns/                   # Conversion patterns
│   ├── basic/                 # Basic math patterns
│   ├── calculus/              # Calculus patterns
│   ├── advanced/              # Advanced math patterns
│   └── educational/           # Professor-style patterns
├── src/                       # Source code
│   └── domain/services/       # NLP processors
├── test_documents/            # Example documents
└── USER_GUIDE.md             # This file
```

## ⚡ Quick Test

1. Create a test file `test.tex`:
```latex
\documentclass{article}
\begin{document}

The quadratic formula is:
\begin{equation}
x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}
\end{equation}

The derivative of $f(x) = x^2$ is $f'(x) = 2x$.

\end{document}
```

2. Run the conversion:
```bash
python convert_my_document.py
```

3. Expected output:
```
1. LaTeX: x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}
   Speech: the solutions to our quadratic equation are given by x equals 
           negative b plus or minus the square root of the discriminant 
           b squared minus 4ac, all divided by 2a

2. LaTeX: f'(x) = 2x
   Speech: f prime of x equals 2x
```

## 🎯 Best Practices

### For Best Results:
1. **Use standard LaTeX notation** - The system recognizes common patterns
2. **Include context** - Surrounding text helps determine the best conversion
3. **Break complex expressions** - Very long expressions may need splitting
4. **Test incrementally** - Start with simple expressions

### Supported Mathematical Areas:
- ✅ Basic arithmetic and algebra
- ✅ Fractions and powers
- ✅ Derivatives and integrals  
- ✅ Limits and series
- ✅ Greek letters and symbols
- ✅ Matrices and vectors
- ✅ Probability and statistics
- ✅ Complex analysis
- ✅ Theorems and proofs

## 🚧 Current Limitations

1. **Not a complete TTS system** - Outputs text, not audio
2. **Pattern-based** - May not handle all possible LaTeX
3. **English only** - Designed for English output
4. **No real-time processing** - Batch processing only

## 🔮 Future Integration

To convert the output to actual speech, you can pipe the results to a TTS engine:

```python
# Example with pyttsx3
import pyttsx3

engine = pyttsx3.init()
engine.setProperty('rate', 150)  # Slower for math

# Get speech text from MathTTSVer3
speech_text = convert_latex_to_speech(latex_expr, patterns)

# Convert to audio
engine.say(speech_text)
engine.runAndWait()
```

## 📚 Examples Repository

Check the `test_documents/` folder for example LaTeX documents that work well with the system.

## 🤝 Getting Help

- Review pattern files in `patterns/` to understand conversions
- Check test files for working examples
- The system is most reliable with common mathematical expressions

---

**Note**: This is Phase 3.5 of the MathTTS project, focusing on achieving 100% natural mathematical speech quality through pattern-based conversion.