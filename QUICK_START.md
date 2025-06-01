# MathTTSVer3 Quick Start Guide

## 🚀 Installation & Setup

1. **Prerequisites**:
   - Python 3.7+
   - PyYAML: `pip install pyyaml`

2. **Project Structure**:
   ```
   MathTTSVer3/
   ├── convert_latex.py      # Main converter script
   ├── patterns/             # Conversion patterns (733 patterns)
   ├── example_math.tex      # Example LaTeX document
   └── USER_GUIDE.md        # Detailed documentation
   ```

## 💻 Basic Usage

### Convert a LaTeX Document:
```bash
python convert_latex.py your_document.tex
```

### Convert with Output File:
```bash
python convert_latex.py your_document.tex -o speech_output.txt
```

### Verbose Mode (Show Full Expressions):
```bash
python convert_latex.py your_document.tex -v
```

## 📄 Supported File Types

| File Type | Extension | Example |
|-----------|-----------|---------|
| LaTeX | `.tex` | `\begin{equation} x^2 \end{equation}` |
| Markdown | `.md` | `The equation $x^2 + y^2 = 1$ represents...` |
| Plain Text | `.txt` | `Formula: $E = mc^2$` |

## 🎯 Example Conversions

### Simple Examples:
| LaTeX | Natural Speech |
|-------|----------------|
| `$x^2$` | "x squared" |
| `$\frac{a}{b}$` | "the fraction a over b" |
| `$\int_0^1 x dx$` | "the integral from 0 to 1 of x with respect to x" |
| `$\frac{dy}{dx}$` | "the derivative of y with respect to x" |

### Complex Examples:
| LaTeX | Natural Speech |
|-------|----------------|
| `$e^{i\pi} + 1 = 0$` | "Euler's remarkable identity shows us that e raised to the power of i pi plus 1 equals zero, beautifully connecting five fundamental mathematical constants" |
| `$x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$` | "the solutions to our quadratic equation are given by x equals negative b plus or minus the square root of the discriminant b squared minus 4ac, all divided by 2a" |

## 🔧 Command Line Options

```bash
python convert_latex.py [options] input_file

Options:
  -h, --help            Show help message
  -o OUTPUT, --output OUTPUT
                        Output file for speech text
  -v, --verbose         Show full expressions and conversions
  -p PATTERNS_DIR       Custom patterns directory (default: patterns)
```

## 📝 Creating Test Documents

### LaTeX Example (`test.tex`):
```latex
\documentclass{article}
\begin{document}
The derivative of $f(x) = x^2$ is $f'(x) = 2x$.

The quadratic formula:
\begin{equation}
x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}
\end{equation}
\end{document}
```

### Markdown Example (`test.md`):
```markdown
# Mathematics

The area of a circle is $A = \pi r^2$.

For integration:
$$\int_0^\infty e^{-x} dx = 1$$
```

### Plain Text Example (`test.txt`):
```
Euler's formula: $e^{i\theta} = \cos(\theta) + i\sin(\theta)$
When $\theta = \pi$, we get $e^{i\pi} + 1 = 0$.
```

## ✨ Features

- **733 conversion patterns** covering:
  - Basic arithmetic and algebra
  - Calculus (derivatives, integrals, limits)
  - Greek letters and special symbols
  - Complex expressions and theorems
  - Professor-style explanations

- **Intelligent conversion** with:
  - Context-aware processing
  - Audience-appropriate language
  - Mathematical storytelling
  - Natural speech flow

## 🎓 Tips for Best Results

1. **Use standard LaTeX notation** - The system recognizes common patterns better
2. **Delimit math properly** - Use `$...$` for inline, `$$...$$` or `\begin{equation}` for display
3. **Keep expressions readable** - Very complex nested expressions may need manual adjustment
4. **Test incrementally** - Start with simple expressions to verify setup

## 🚨 Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No patterns loaded" | Ensure `patterns/` directory exists in the same location as `convert_latex.py` |
| Low conversion rate | Complex or unusual LaTeX may use fallback conversion - this is normal |
| Encoding errors | Ensure your LaTeX file is UTF-8 encoded |

## 🔗 Next Steps

1. **Test with example**: `python convert_latex.py example_math.tex`
2. **Try your own documents**: Start with simple LaTeX files
3. **Integrate with TTS**: Pipe output to text-to-speech engine:
   ```python
   # Example with pyttsx3
   import pyttsx3
   engine = pyttsx3.init()
   engine.say(speech_text)
   engine.runAndWait()
   ```

## 📚 More Information

See `USER_GUIDE.md` for:
- Detailed pattern documentation
- Advanced usage examples
- Integration with TTS engines
- Customization options

---

**Quick Test**: Run `python convert_latex.py example_math.tex` to see the system in action!