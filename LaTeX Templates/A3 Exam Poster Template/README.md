# A3 Cheat Sheet LaTeX Template

A modern, creative LaTeX template for A3 portrait cheat sheets with light and dark modes using a harmonized color palette and Helvetica font.

## Features

- A3 portrait format (297mm × 420mm)
- Four-column layout for maximum content density
- Light and dark mode color schemes with harmonized colors (switchable within the same file)
- Helvetica font family for clean, professional appearance
- Custom environments for formulas, notes, and information boxes
- Special highlighted elements for key points, warnings, and tips
- Logo support in the banner/header
- Easy image insertion within sections

## Usage

1. Place the `a3cheatsheet.cls` file in the same directory as your LaTeX document.
2. Open `template.tex` and choose your mode by modifying the `\documentclass` line:

   **For Light Mode (default):**
   ```latex
   \documentclass{a3cheatsheet}
   ```

   **For Dark Mode:**
   ```latex
   \documentclass[darkmode]{a3cheatsheet}
   ```

3. The template includes clear instructions at the top for easy mode switching.

### Adding a Logo

To add a logo to the banner, use the optional parameter in the title command:

```latex
% With logo
\cheatsheettitle[logo.png]{Main Title}{Subtitle}

% Without logo (default)
\cheatsheettitle{Main Title}{Subtitle}
```

The logo will be automatically sized to 1cm height and positioned on the right side of the banner. The subtitle is positioned below the main title to prevent overlap with the logo.

### Adding Images in Sections

Use the `\sectionimage` command to insert images within sections:

```latex
% Basic usage with default width (30% of column width)
\sectionimage{diagram.png}{Caption text}

% Custom width (50% of column width)
\sectionimage[0.5]{diagram.png}{Caption text}

% Image without caption
\sectionimage{diagram.png}{}
```

Images are automatically centered and scaled appropriately for the column layout.

## Color Schemes (Harmonized Palette)

The template uses a carefully balanced color palette designed for optimal readability and visual harmony.

### Light Mode (Default)
- **Primary Color**: Viridis Teal (#35b779) - for sections and main elements
- **Secondary Color**: Viridis Blue (#31688e) - for subsections and formula boxes
- **Accent Color**: Viridis Dark Purple (#440154) - for highlights and text
- **Background**: Very Light Gray (#fafafa)
- **Text**: Viridis Dark Purple (#440154)

### Dark Mode
- **Primary Color**: Soft Teal-Green (#66c2a5) - for sections and main elements
- **Secondary Color**: Warm Coral (#fc8d62) - for subsections and formula boxes
- **Accent Color**: Soft Blue-Purple (#8da0cb) - for highlights
- **Background**: Warm Dark Gray (#1c1c23)
- **Text**: White (#ffffff) - for optimal readability

## Template Structure

The unified template includes:
- Clear mode selection instructions at the top
- Sample content demonstrating all available environments
- Usage notes explaining compilation and customization options

## Compilation

### Windows
```
compile.bat template
```

### Unix/Linux/macOS
```
chmod +x compile.sh  # First time only
./compile.sh template
```

For A3 paper size enforcement:
```
compile_a3.bat template  # Windows
./compile_a3.sh template  # Unix/Linux/macOS
```

## Quick Start

1. Copy `template.tex` to create your new cheat sheet
2. Rename it to your desired filename
3. Choose light or dark mode by uncommenting the appropriate `\documentclass` line
4. Replace the sample content with your own
5. Compile using the provided scripts 