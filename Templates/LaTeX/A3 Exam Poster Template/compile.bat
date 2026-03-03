@echo off
echo A3 Cheat Sheet Template Compiler
echo ================================

if "%1"=="" (
    echo Usage: compile.bat [filename]
    echo Example: compile.bat vortex_filament_model
    echo.
    echo Available templates:
    echo - vortex_filament_model
    echo - template
    goto :EOF
)

echo Compiling %1.tex...
pdflatex -interaction=nonstopmode -papersize=a3 %1.tex

if %ERRORLEVEL% neq 0 (
    echo.
    echo Compilation failed! 
    echo.
    echo Common issues:
    echo 1. Make sure you have the tcolorbox package with the [most] option installed.
    echo    For TeX Live: tlmgr install tcolorbox
    echo    For MiKTeX: Use the MiKTeX Console to install the tcolorbox package
    echo 2. Make sure all required packages are installed.
    echo 3. Check for syntax errors in your LaTeX file.
    goto :EOF
)

echo.
echo Compilation successful! Created %1.pdf
echo. 