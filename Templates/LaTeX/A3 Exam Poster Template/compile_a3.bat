@echo off
echo A3 Cheat Sheet Template Compiler (A3 Enforced)
echo ============================================

if "%1"=="" (
    echo Usage: compile_a3.bat [filename]
    echo Example: compile_a3.bat vortex_filament_model
    echo.
    echo Available templates:
    echo - vortex_filament_model
    echo - template
    goto :EOF
)

echo Compiling %1.tex with A3 paper size enforced...

:: First run - create DVI
echo Step 1: Creating DVI file...
latex -interaction=nonstopmode %1.tex

if %ERRORLEVEL% neq 0 (
    echo.
    echo DVI creation failed!
    echo.
    goto :errors
)

:: Second run - convert DVI to PDF with A3 paper size
echo Step 2: Converting DVI to PDF with A3 paper size...
dvipdfm -p a3 %1.dvi

if %ERRORLEVEL% neq 0 (
    echo.
    echo PDF conversion failed!
    echo.
    goto :errors
)

echo.
echo Compilation successful! Created %1.pdf with A3 paper size.
echo.
goto :EOF

:errors
echo Common issues:
echo 1. Make sure you have the tcolorbox package with the [most] option installed.
echo    For TeX Live: tlmgr install tcolorbox
echo 2. Make sure all required packages are installed.
echo 3. Check for syntax errors in your LaTeX file.
echo 4. Make sure latex and dvipdfm are installed.
echo    For TeX Live: tlmgr install latex dvipdfm
echo    For MiKTeX: Use the MiKTeX Console to install these packages 