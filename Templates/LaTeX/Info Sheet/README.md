# Technical Reference Sheet LaTeX Template

A professional landscape A4 LaTeX template designed specifically for technical interview reference sheets. This template provides a clean, organized layout for quick reference of programming languages, frameworks, and technical concepts during interviews.

## Features

### 🎨 Professional Design
- **Landscape A4 format** - Perfect for single-page reference sheets
- **Modern color scheme** - Professional blue-gray color palette
- **Clean typography** - Sans-serif fonts for excellent readability
- **Syntax highlighting** - Colored code examples and syntax
- **Visual hierarchy** - Clear section organization with color-coded elements

### 📋 Comprehensive Sections
- **Header with technology name and version** - Clear identification
- **Quick reference table** - Essential syntax and data types
- **Basic syntax** - Core language constructs
- **Control structures** - Loops, conditionals, and flow control
- **Data structures** - Lists, dictionaries, sets, etc.
- **Common methods** - Frequently used functions and methods
- **Key concepts** - Important programming concepts and patterns
- **Common patterns** - Error handling, file operations, etc.
- **Important notes** - Best practices and conventions

### 🛠️ Custom Commands
The template includes several custom LaTeX commands for easy customization:

- `\techheader[version]{technology}` - Creates the header with technology name and version
- `\quickref{content}` - Creates a quick reference table
- `\syntaxbox{title}{content}` - Creates syntax information boxes
- `\conceptbox{title}{content}` - Creates concept explanation boxes
- `\codeexample{title}{code}` - Creates code examples with syntax highlighting
- `\method{signature}{description}` - Creates method/function documentation
- `\code{text}` - Inline code formatting
- `\datatype{type}` - Data type formatting
- `\importantnote{content}` - Creates important information boxes

## Quick Start

1. **Compile the document:**
   ```bash
   pdflatex main.tex
   ```

2. **Customize the content:**
   - Edit `main.tex` to replace Python content with your target technology
   - Modify colors in `style.sty` if desired
   - Adjust sections based on the technology you're documenting

3. **Required packages:**
   The template uses standard LaTeX packages. Make sure you have:
   - `fontawesome5` for icons
   - `tikz` for graphics
   - `listings` for code syntax highlighting
   - `multicol` for column layout
   - Other packages are typically included with most LaTeX distributions

## Customization Guide

### Changing Colors
Edit the color definitions in `style.sty`:
```latex
\definecolor{primary}{HTML}{2C3E50}      % Main color
\definecolor{secondary}{HTML}{3498DB}    % Secondary color
\definecolor{accent}{HTML}{E74C3C}       % Accent color
\definecolor{keyword}{HTML}{0066CC}      % Code keyword color
```

### Adding New Sections
Use the existing section structure:
```latex
\section{New Section Name}
\begin{multicols}{2}
  \codeexample{Example Title}{
    // Your code here
  }
\end{multicols}
```

### Modifying Layout
- Use `\begin{multicols}{2}` for two-column layout
- Use `\begin{multicols}{3}` for three-column layout
- Adjust margins in the geometry package settings

### Code Syntax Highlighting
The template includes syntax highlighting for code examples:
```latex
\codeexample{Title}{
def function():
    return "Hello World"
}
```

## Use Cases

This template is perfect for:
- **Technical interviews** - Quick reference during coding interviews
- **Programming language reference** - Syntax and concepts for any language
- **Framework documentation** - API references and usage patterns
- **Algorithm cheat sheets** - Common algorithms and data structures
- **System design reference** - Architecture patterns and concepts

## Example Reference Sheets

You can create reference sheets for:
- **Programming Languages**: Python, JavaScript, Java, C++, Go, Rust
- **Frameworks**: React, Django, Spring, Express.js
- **Databases**: SQL, MongoDB, Redis
- **Tools**: Git, Docker, Kubernetes
- **Concepts**: Algorithms, Data Structures, Design Patterns

## File Structure

```
Info Sheet/
├── main.tex          # Main document with example content
├── style.sty         # Style package with all formatting
└── README.md         # This documentation
```

## Tips for Best Results

1. **Keep content concise** - The template is designed for single-page use
2. **Focus on syntax** - Include common syntax patterns and examples
3. **Prioritize frequently used** - Include the most commonly used methods and concepts
4. **Use code examples** - Show real code snippets, not just descriptions
5. **Include quick reference** - Put essential information in the quick reference section

## Troubleshooting

### Common Issues
- **Missing icons**: Install `fontawesome5` package
- **Code highlighting issues**: Install `listings` package
- **Layout issues**: Ensure you're using landscape orientation
- **Color problems**: Check that `xcolor` package is available

### Compilation
If you encounter compilation errors:
1. Ensure all required packages are installed
2. Compile multiple times if using references
3. Check for special characters in code examples

## License

This template is provided as-is for educational and professional use. Feel free to modify and adapt it for your needs.

---

**Created for technical interview reference sheets and programming language documentation** 