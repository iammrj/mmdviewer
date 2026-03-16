# Markdown & Mermaid Viewer v2.0 - Features

## Overview

A powerful desktop application for viewing and editing Markdown documents and Mermaid diagrams with extensive customization options.

## Core Features

### 📝 Dual Format Support
- **Markdown** (.md, .markdown, .mdown, .mkd)
  - GitHub-flavored markdown
  - Code highlighting
  - Tables, lists, blockquotes
  - Table of contents
  - Fenced code blocks

- **Mermaid** (.mmd, .mermaid)
  - Flowcharts
  - Sequence diagrams
  - Gantt charts
  - Class diagrams
  - ER diagrams

### 🎨 Font Customization **NEW!**
Choose from 19 popular reading fonts:

**Serif Fonts** (Traditional reading)
- Georgia
- Charter
- Iowan Old Style
- Palatino
- Times New Roman

**Sans-Serif Fonts** (Modern)
- Default (System)
- San Francisco
- Helvetica Neue / Helvetica
- Arial
- Avenir
- Calibri
- Verdana
- Trebuchet MS

**Monospace Fonts** (Code style)
- Courier New
- Monaco
- Menlo
- Source Code Pro
- JetBrains Mono

Access via: **View → Reader Font**

### ✏️ Edit Mode
- Split-pane view
- Real-time preview (300ms debounce)
- Syntax-aware editing
- Line/column indicator
- Auto-save preferences

### 📤 Export Options
- **HTML** - Standalone with embedded CSS
- **PNG** - High-quality images (Mermaid diagrams)
- **PDF** - Print-ready documents

### 💾 File Management
- Recent files (last 10)
- Drag & drop support
- Auto-save unsaved changes prompt
- Remember last directory

### ⚙️ Settings Persistence
- Window size and position
- Edit mode state
- Selected font
- Recent files list

## User Interface

### Menu Bar
- **File**: Open, Save, Export, Recent files
- **View**: Edit mode toggle, Font selection
- **Help**: Documentation, About

### Toolbar
- Quick access buttons
- Visual feedback
- Tooltips

### Status Bar
- File type indicator
- Cursor position
- Status messages

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open file | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Toggle Edit Mode | `Ctrl+E` |
| Export HTML | `Ctrl+Shift+H` |
| Export PNG | `Ctrl+Shift+P` |
| Export PDF | `Ctrl+Shift+D` |
| Show Help | `F1` |
| Quit | `Ctrl+Q` |

## Technical Specifications

### Built With
- **PyQt5** - Cross-platform GUI
- **PyQtWebEngine** - HTML/CSS rendering
- **Python Markdown** - Markdown processing
- **Mermaid.js** - Diagram rendering
- **Pygments** - Syntax highlighting

### Platform Support
- macOS (11.0+)
- Linux
- Windows 10/11

### File Associations
Automatically opens:
- .md, .markdown, .mdown, .mkd files
- .mmd, .mermaid files

### Performance
- Lightweight (< 100MB installed)
- Fast startup
- Efficient memory usage
- Smooth rendering

## Customization

### Appearance
- ✅ Reader font selection (19 options)
- ✅ GitHub-style markdown rendering
- ✅ Syntax highlighting themes
- ⏳ Dark mode (planned)
- ⏳ Custom CSS (planned)

### Behavior
- ✅ Auto-save preferences
- ✅ Remember window state
- ✅ Recent files tracking
- ✅ Unsaved changes detection

## Installation

### Direct Download
- Download `.dmg` (macOS)
- Mount and drag to Applications
- Launch from Applications folder

### From Source
```bash
git clone <repository>
cd MDViewer
pip install -r requirements.txt
python unified_viewer.py
```

### Build From Source
```bash
./build_dmg.sh  # macOS
python build_spec.py  # All platforms
```

## Usage Examples

### Basic Viewing
1. Launch app
2. File → Open (or Ctrl+O)
3. Select markdown file
4. View rendered content

### Editing
1. Open file
2. View → Edit Mode (or Ctrl+E)
3. Edit in left pane
4. See live preview in right pane
5. Save with Ctrl+S

### Changing Font
1. View → Reader Font
2. Select preferred font
3. Document re-renders immediately
4. Selection is saved

### Exporting
1. Open document
2. File → Export
3. Choose format (HTML/PNG/PDF)
4. Select destination
5. Done!

## Version History

### v2.0.0 (Current)
- ✨ Added font selection (19 fonts)
- ✨ Enhanced help system
- 🐛 Fixed Gantt chart rendering
- 🐛 Fixed PNG export clipping
- 🎨 Improved UI feedback
- 📚 Added comprehensive documentation

### v1.0.0
- Initial release
- Markdown & Mermaid support
- Basic export functionality
- Edit mode with live preview

## Future Roadmap

### v2.1 (Planned)
- [ ] Font size adjustment
- [ ] Line height customization
- [ ] Dark mode
- [ ] Custom themes

### v2.2 (Planned)
- [ ] Markdown syntax highlighting in editor
- [ ] Find & replace
- [ ] Spell checker
- [ ] Print support

### v3.0 (Future)
- [ ] Multiple tabs
- [ ] Plugin system
- [ ] Git integration
- [ ] Cloud sync

## Support

### Documentation
- `FONT_SELECTION.md` - Font feature guide
- `GANTT_GUIDE.md` - Gantt chart best practices
- `QUICKSTART.md` - Getting started
- `UNIFIED_README.md` - Complete guide

### Help
- Press `F1` in app
- Help → Documentation
- GitHub Issues (if open source)

## License

MIT License - See LICENSE file

## Credits

- Developed by Jilani Shaik
- Built with PyQt5 and Python
- Mermaid.js for diagrams
- Python Markdown for rendering

---

**Markdown & Mermaid Viewer** - Your professional markdown editor
