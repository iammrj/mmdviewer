# MDViewer - Complete Feature List (v2.1)

## All 15 Features Successfully Implemented!

---

## Feature 1: Zoom Controls
**Status:** ✅ Complete

- **Zoom In:** `Ctrl++` or View → Zoom In
- **Zoom Out:** `Ctrl+-` or View → Zoom Out
- **Reset Zoom:** `Ctrl+0` or View → Reset Zoom
- Zoom range: 10% to 300%
- Persists across sessions
- Works on both markdown and mermaid views

---

## Feature 2: Word Count & Statistics
**Status:** ✅ Complete

Displays in status bar:
- **Word count:** Total words in document
- **Character count:** Total characters
- **Reading time:** Estimated reading time (200 words/min)

Example: `1250 words | 7543 chars | ~6 min read`

Updates live as you type in edit mode.

---

## Feature 3: Full-Screen Mode
**Status:** ✅ Complete

- **Toggle:** `F11` or View → Full Screen
- Maximizes viewing area
- Perfect for presentations or focused reading
- Press `F11` again to exit

---

## Feature 4: Copy as HTML
**Status:** ✅ Complete

- **Shortcut:** `Ctrl+Shift+C`
- **Menu:** File → Copy as HTML
- Copies rendered HTML to clipboard
- Includes all styling and formatting
- Paste into email, CMS, or other HTML editors

---

## Feature 5: Markdown Cheat Sheet
**Status:** ✅ Complete

- **Shortcut:** `Ctrl+?`
- **Menu:** Help → Markdown Cheat Sheet
- Quick reference guide for markdown syntax
- Covers: headings, formatting, lists, links, images, code blocks, tables
- Always accessible when you need it

---

## Feature 6: Dark Mode
**Status:** ✅ Complete

- **Toggle:** `Ctrl+D` or View → Dark Mode
- **Colors:**
  - Background: #1e1e1e (dark gray)
  - Text: #d4d4d4 (light gray)
  - Code blocks: #2d2d2d
  - Links: #4fc3f7 (light blue)
- Applies to all rendered markdown
- Persists across sessions
- Easy on the eyes for night work

---

## Feature 7: Find/Search
**Status:** ✅ Complete

- **Open dialog:** `Ctrl+F` or File → Find
- **Options:**
  - Case sensitive search
  - Whole words only
  - Find next / Find previous
- Highlights matches in editor
- Works only in edit mode
- Navigate through results easily

---

## Feature 8: Line Numbers
**Status:** ✅ Complete

- **Toggle:** `Ctrl+L` or View → Show Line Numbers
- Shows current line and column in status bar
- Example: `Line 42, Col 15`
- Useful for referencing specific locations
- Updates as cursor moves

---

## Feature 9: Auto-Save & Draft Recovery
**Status:** ✅ Complete

### Auto-Save
- **Toggle:** `Ctrl+Shift+A` or View → Auto-Save
- Saves drafts every 60 seconds (configurable)
- Only saves when file is modified and in edit mode
- Status bar shows: "Auto-saved at [time]"
- Drafts stored in: `~/.mdviewer/drafts/`

### Draft Recovery
- Automatic on app startup
- Shows dialog if drafts found
- Options:
  - Recover draft (restores content)
  - Delete draft (removes backup)
  - Cancel (leave drafts)
- Prevents data loss from crashes
- Drafts cleaned up after successful manual save

---

## Feature 10: Reading Time Estimate
**Status:** ✅ Complete (Integrated in Feature 2)

- Calculates based on 200 words per minute
- Displays in status bar: `~X min read`
- Updates live as you edit
- Helps gauge content length
- Rounds up to nearest minute (minimum 1 min)

---

## Feature 11: Table of Contents (TOC)
**Status:** ✅ Complete

- **Toggle:** `Ctrl+T` or View → Table of Contents
- **Features:**
  - Dockable sidebar panel (right side)
  - Automatically parses markdown headings (H1-H6)
  - Hierarchical tree structure
  - Click heading to jump to that line in editor
  - Auto-updates when content changes
  - Collapsible/expandable sections
- **Only for markdown files** (not mermaid)
- Persists visibility state

---

## Feature 12: Favorites/Bookmarks
**Status:** ✅ Complete

### Add/Remove Favorites
- **Toggle:** `Ctrl+B` or File → Add to Favorites
- Button shows:
  - `★ Add to Favorites` (when not favorited)
  - `☆ Remove from Favorites` (when favorited)

### Access Favorites
- **Menu:** File → Favorites
- Shows list with ★ prefix
- Click to open file
- "Manage Favorites..." option

### Manage Favorites Dialog
- View all favorite files
- Open selected favorite
- Remove from favorites
- Files with full path tooltips
- Persists across sessions

---

## Feature 13: Markdown Templates
**Status:** ✅ Complete

**Access:** File → Templates

### Available Templates:

1. **README**
   - Project documentation structure
   - Features, installation, usage sections
   - License and contact info

2. **Blog Post**
   - Article template with metadata
   - Introduction, main content, conclusion
   - Tags and publish date

3. **Meeting Notes**
   - Structured agenda and action items
   - Attendees, decisions, next meeting
   - Checkbox action items

4. **Project Documentation**
   - Comprehensive docs template
   - Architecture, setup, API reference
   - Examples and contributing guidelines

5. **TODO List**
   - Prioritized task list
   - High/Normal/Ideas sections
   - Completed items tracking

6. **Changelog**
   - Semantic versioning format
   - Added/Changed/Fixed sections
   - Follows Keep a Changelog standard

### Using Templates:
- Select template from menu
- Loads into editor in edit mode
- Prompts if current file has unsaved changes
- Fill in placeholder text
- Save as new file

---

## Feature 14: Print Preview
**Status:** ✅ Complete

- **Shortcut:** `Ctrl+Shift+V`
- **Menu:** File → Print Preview
- **Features:**
  - High-resolution preview
  - Page layout options
  - Letter size with margins (15mm)
  - See exactly how document will print
  - Print directly from preview
- Works with both markdown and mermaid diagrams

---

## Feature 15: Image Paste Support
**Status:** ✅ Complete

### How to Use:
1. Save your markdown document first
2. Copy an image to clipboard (screenshot, image file, etc.)
3. In edit mode, press `Ctrl+V` at desired location
4. Image automatically:
   - Saves to `images/` folder (next to markdown file)
   - Named with timestamp: `pasted_image_YYYYMMDD_HHMMSS.png`
   - Inserts markdown syntax: `![Image](images/filename.png)`

### Features:
- Automatic folder creation
- No manual file management needed
- Relative paths (portable documents)
- Status bar confirmation
- Prevents orphaned images (requires saved file)

---

## Keyboard Shortcuts Summary

| Action | Shortcut |
|--------|----------|
| Open File | `Ctrl+O` |
| Save | `Ctrl+S` |
| Save As | `Ctrl+Shift+S` |
| Toggle Edit Mode | `Ctrl+E` |
| **Add to Favorites** | `Ctrl+B` |
| **Find** | `Ctrl+F` |
| Copy as HTML | `Ctrl+Shift+C` |
| Export HTML | `Ctrl+Shift+H` |
| Export PNG | `Ctrl+Shift+P` |
| Export PDF | `Ctrl+Shift+D` |
| **Print Preview** | `Ctrl+Shift+V` |
| **Zoom In** | `Ctrl++` |
| **Zoom Out** | `Ctrl+-` |
| **Reset Zoom** | `Ctrl+0` |
| **Full Screen** | `F11` |
| **Dark Mode** | `Ctrl+D` |
| **Line Numbers** | `Ctrl+L` |
| **Auto-Save Toggle** | `Ctrl+Shift+A` |
| **Table of Contents** | `Ctrl+T` |
| **Markdown Cheat Sheet** | `Ctrl+?` |
| Documentation | `F1` |
| Quit | `Ctrl+Q` |

---

## Settings Persistence

The following settings are remembered across sessions:
- Window size and position
- Edit mode state
- Selected viewer font
- Zoom level
- Dark mode enabled/disabled
- Auto-save enabled/disabled
- Table of Contents visibility
- Recent files list (last 10)
- Favorites list
- Last opened directory

---

## Technical Details

### Storage Locations:
- **Settings:** System-specific (QSettings)
  - macOS: `~/Library/Preferences/com.MDViewer.UnifiedViewer.plist`
  - Linux: `~/.config/MDViewer/UnifiedViewer.conf`
  - Windows: Registry
- **Drafts:** `~/.mdviewer/drafts/`
- **Pasted Images:** `images/` folder next to markdown file

### Auto-Save:
- **Interval:** 60 seconds (configurable in code)
- **Trigger:** Only when modified and in edit mode
- **Storage:** Draft file + metadata file
- **Cleanup:** Automatic on successful save

---

## Usage Tips

1. **Quick Start:**
   - Open a markdown file (`Ctrl+O`)
   - Toggle edit mode (`Ctrl+E`)
   - Enable auto-save (`Ctrl+Shift+A`)
   - Show TOC (`Ctrl+T`) for easy navigation

2. **Dark Mode Workflow:**
   - Enable dark mode (`Ctrl+D`)
   - Choose a suitable font (View → Reader Font → Georgia)
   - Adjust zoom if needed (`Ctrl++/Ctrl+-`)

3. **Template Workflow:**
   - File → Templates → Select template
   - Fill in placeholders
   - Save as new file
   - Add to favorites (`Ctrl+B`)

4. **Image Workflow:**
   - Save document first
   - Take screenshot or copy image
   - Paste in editor (`Ctrl+V`)
   - Image automatically saved and linked

5. **Presentation Mode:**
   - Enable full screen (`F11`)
   - Disable edit mode (viewer only)
   - Use zoom to adjust size
   - Dark mode optional

---

## Version History

### v2.1 (Current)
- ✅ Feature 9: Auto-Save & Draft Recovery
- ✅ Feature 10: Reading Time Estimate
- ✅ Feature 11: Table of Contents
- ✅ Feature 12: Favorites/Bookmarks
- ✅ Feature 13: Markdown Templates
- ✅ Feature 14: Print Preview
- ✅ Feature 15: Image Paste Support

### v2.0
- ✅ Feature 1: Zoom Controls
- ✅ Feature 2: Word Count & Statistics
- ✅ Feature 3: Full-Screen Mode
- ✅ Feature 4: Copy as HTML
- ✅ Feature 5: Markdown Cheat Sheet
- ✅ Feature 6: Dark Mode
- ✅ Feature 7: Find/Search
- ✅ Feature 8: Line Numbers
- ✅ Font Selection (19 fonts)
- ✅ Gantt Chart Fixes
- ✅ App Icon & Branding

### v1.0
- Initial release
- Markdown & Mermaid support
- Edit mode with live preview
- Export to HTML/PNG/PDF

---

## What's Next?

All 15 requested features are now complete! The application is fully functional with:
- Professional editing experience
- Powerful viewing capabilities
- Data safety (auto-save)
- Organization tools (favorites, TOC)
- Productivity features (templates, image paste)
- Customization (fonts, dark mode, zoom)

Enjoy your enhanced Markdown & Mermaid Viewer!
