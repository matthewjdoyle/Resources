#!/bin/bash

echo "A3 Cheat Sheet Template Compiler (A3 Enforced)"
echo "============================================"

if [ -z "$1" ]; then
    echo "Usage: ./compile_a3.sh [filename]"
    echo "Example: ./compile_a3.sh vortex_filament_model"
    echo ""
    echo "Available templates:"
    echo "- vortex_filament_model"
    echo "- template"
    exit 1
fi

echo "Compiling $1.tex with A3 paper size enforced..."

# First run - create DVI
echo "Step 1: Creating DVI file..."
latex -interaction=nonstopmode $1.tex

if [ $? -ne 0 ]; then
    echo ""
    echo "DVI creation failed!"
    echo ""
    errors=true
else
    # Second run - convert DVI to PDF with A3 paper size
    echo "Step 2: Converting DVI to PDF with A3 paper size..."
    dvipdfm -p a3 $1.dvi
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "PDF conversion failed!"
        echo ""
        errors=true
    else
        echo ""
        echo "Compilation successful! Created $1.pdf with A3 paper size."
        echo ""
        exit 0
    fi
fi

# If we get here, there was an error
echo "Common issues:"
echo "1. Make sure you have the tcolorbox package with the [most] option installed."
echo "   For TeX Live: tlmgr install tcolorbox"
echo "2. Make sure all required packages are installed."
echo "3. Check for syntax errors in your LaTeX file."
echo "4. Make sure latex and dvipdfm are installed."
echo "   For TeX Live: tlmgr install latex dvipdfm"
exit 1 