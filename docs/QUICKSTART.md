# Quick Start Guide

## Running the Application

### Option 1: Run from source (Recommended for development)
```bash
python markdown_viewer_robust.py
```

### Option 2: Open a file directly
```bash
python markdown_viewer_robust.py sample.md
```

### Option 3: Install as package
```bash
pip install -e .
mdviewer
```

## First Steps

1. **Open a file**
   - Press `Ctrl+O`
   - Navigate to `sample.md`
   - Click Open

2. **Toggle Edit Mode**
   - Press `Ctrl+E`
   - You'll now see two panes:
     - Left: Editor
     - Right: Live preview

3. **Edit and Watch**
   - Type in the editor
   - See changes render instantly

4. **Save Your Work**
   - Press `Ctrl+S`
   - Your changes are saved

5. **Export HTML**
   - Press `Ctrl+Shift+E`
   - Choose a location
   - Get a standalone HTML file

## Tips

- **Recent Files**: Access via File → Open Recent
- **Status Bar**: Shows cursor position (line, column)
- **Unsaved Indicator**: An asterisk (*) appears in title when modified
- **Help**: Press F1 for in-app help

## Keyboard Shortcuts Cheat Sheet

| Action | Shortcut |
|--------|----------|
| Open | Ctrl+O |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| Toggle Edit | Ctrl+E |
| Export HTML | Ctrl+Shift+E |
| Help | F1 |
| Quit | Ctrl+Q |

## Building Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build
./build.sh  # On Unix/Mac
# or
python build_spec.py  # Cross-platform
```

Executable will be in `dist/` folder.

## Troubleshooting

**Application won't start**
- Ensure Python 3.8+ is installed
- Check all dependencies are installed: `pip install -r requirements.txt`

**File won't open**
- Check file permissions
- Ensure file is valid UTF-8 encoded text

**Preview not updating**
- Wait 300ms after typing (debounce delay)
- Check for syntax errors in markdown

**Can't save file**
- Check write permissions
- Ensure disk space available

For more issues, check the log output or open an issue on GitHub.
