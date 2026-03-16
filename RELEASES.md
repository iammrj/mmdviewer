# Release History

## v2.1.0 (2026-03-16) - Feature Complete Edition

### New Features
- ✨ Auto-save with draft recovery (every 60 seconds)
- ✨ Table of Contents sidebar with navigation
- ✨ Favorites/Bookmarks system
- ✨ 6 Markdown templates (README, Blog, Meeting Notes, etc.)
- ✨ Print preview with page layout options
- ✨ Image paste from clipboard
- ✨ Line numbers in editor gutter
- ✨ Word count, character count, and reading time estimate

### Improvements
- 🎨 Project restructured following best practices
- 🎨 Organized into proper package structure (mdviewer/)
- 🎨 Separated documentation into docs/ directory
- 🎨 Created centralized assets/ directory
- 🎨 Added main.py as clean entry point

### Technical
- 📦 Refactored imports for package structure
- 📦 Created proper __init__.py files
- 📦 Updated .gitignore with comprehensive exclusions

---

## v2.0.0 (2026-03-11) - Productivity Edition

### New Features
- ✨ Zoom controls (10%-300%)
- ✨ Full-screen mode
- ✨ Dark mode with custom color scheme
- ✨ Find & search with advanced options
- ✨ Copy as HTML to clipboard
- ✨ Markdown cheat sheet (Ctrl+?)
- ✨ Font selection (19 popular reading fonts)
- ✨ Professional app icon with .icns format

### Bug Fixes
- 🐛 Fixed Gantt chart rendering issues
- 🐛 Fixed PNG export clipping problems
- 🐛 Fixed Mermaid.js compatibility (downgraded to 9.4.3)
- 🐛 Added structuredClone polyfill for QtWebEngine

### Documentation
- 📚 Added FEATURES_v2.md with complete feature list
- 📚 Added FONT_SELECTION.md guide
- 📚 Added GANTT_GUIDE.md with best practices
- 📚 Added ICON_README.md with icon generation instructions

---

## v1.0.0 (2026-03-10) - Initial Release

### Core Features
- 📝 Markdown viewer with GitHub-style rendering
- 📝 Mermaid diagram support (flowcharts, sequence, Gantt, class, ER)
- ✏️ Edit mode with split-pane and real-time preview
- 📤 Export to HTML, PNG, PDF
- 💾 Recent files tracking
- ⚙️ Settings persistence (window size, position, edit mode)
- 🎨 Syntax highlighting with Pygments
- 📊 Status bar with file type and cursor position

### Markdown Extensions
- extra (tables, footnotes, etc.)
- codehilite (syntax highlighting)
- toc (table of contents)
- tables
- fenced_code
- nl2br (newline to break)

### Supported File Types
- .md, .markdown, .mdown, .mkd (Markdown)
- .mmd, .mermaid (Mermaid diagrams)

---

## Roadmap

### v2.2 (Planned)
- [ ] Font size adjustment
- [ ] Line height customization
- [ ] Custom CSS themes
- [ ] Spell checker
- [ ] Print support (direct print, not preview)

### v2.3 (Planned)
- [ ] Markdown syntax highlighting in editor
- [ ] Multiple tab support
- [ ] Git integration
- [ ] Plugin system

### v3.0 (Future)
- [ ] Cloud sync
- [ ] Collaborative editing
- [ ] Mobile companion app
- [ ] Web version

---

**Note:** Version numbers follow [Semantic Versioning](https://semver.org/)
