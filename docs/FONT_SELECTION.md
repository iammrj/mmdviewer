# Font Selection Feature

## Overview

The Markdown & Mermaid Viewer now supports custom font selection for the reader pane, allowing you to choose your preferred reading font from available system fonts.

## How to Change Font

### Via Menu
1. Open the application
2. Go to **View → Reader Font**
3. Select your preferred font from the menu
4. The document will automatically re-render with the new font

### Keyboard Navigation
- Open menu: `Alt+V` (View menu)
- Navigate with arrow keys
- Press `Enter` to select

## Available Fonts

The application includes these popular reading fonts (if installed on your system):

### Serif Fonts (Traditional)
- **Georgia** - Classic web-safe serif, excellent readability
- **Charter** - Apple's reading-optimized serif
- **Iowan Old Style** - Traditional book-style font (macOS)
- **Palatino** - Elegant serif, great for long-form content
- **Times New Roman** - Standard serif font

### Sans-Serif Fonts (Modern)
- **Default (System)** - Uses system font stack
- **San Francisco** - Apple's modern UI font (macOS)
- **Helvetica Neue** / **Helvetica** - Clean, neutral
- **Arial** - Web-safe sans-serif
- **Avenir** - Elegant geometric sans-serif
- **Calibri** - Microsoft's modern sans-serif
- **Verdana** - Web-optimized for screen reading
- **Trebuchet MS** - Humanist sans-serif

### Monospace Fonts (Code-Style)
- **Courier New** - Classic typewriter font
- **Monaco** - macOS terminal font
- **Menlo** - Apple's programming font
- **Source Code Pro** - Adobe's coding font
- **JetBrains Mono** - Modern coding font

## Font Persistence

Your font selection is automatically saved and will be:
- ✅ Remembered across app restarts
- ✅ Applied to all markdown documents
- ✅ Used in both viewer and edit modes
- ✅ Saved in your system preferences

## Recommendations

### For Long-Form Reading
- **Georgia** - Warm, readable serif
- **Charter** - Optimized for extended reading
- **Iowan Old Style** - Book-like experience

### For Technical Documents
- **Default (System)** - Clean, modern
- **San Francisco** - Apple's optimized UI font
- **Calibri** - Microsoft's screen-optimized font

### For Code-Heavy Content
- **Monaco** - Clear monospace
- **Menlo** - Programming-friendly
- **Source Code Pro** - Adobe's open-source coding font

## Font Preview

To preview how a font looks:
1. Open any markdown file
2. Select **View → Reader Font**
3. Click on different fonts
4. The document re-renders immediately

## Technical Details

### Font Stack
When you select a font, the CSS uses:
```css
font-family: 'Your Selected Font', -apple-system, BlinkMacSystemFont, serif;
```

This ensures:
- Your selected font is used if available
- Falls back to system fonts if unavailable
- Always maintains readability

### Code Blocks
Code blocks always use monospace fonts:
```css
font-family: 'Courier New', Courier, monospace;
```

This ensures code remains readable regardless of body font selection.

### Mermaid Diagrams
Mermaid diagrams use their own font settings and are not affected by reader font selection.

## Troubleshooting

### Font Not Appearing in Menu?
The font must be installed on your system. The app only shows fonts that are actually available.

### Font Looks Different Than Expected?
Some fonts render differently at different sizes. Try:
- Zooming in/out (Cmd +/-)
- Using a different font
- Checking if the font is properly installed

### Reset to Default
1. Go to **View → Reader Font**
2. Select **Default (System)**
3. This restores the original font stack

## Adding Custom Fonts

To add your own fonts:
1. Install the font on your system
2. Restart the application
3. If the font is in the popular fonts list, it will appear automatically

Popular fonts checked:
- Georgia, Charter, Iowan Old Style, Palatino, Times New Roman
- Helvetica Neue, Helvetica, Arial, San Francisco, Avenir
- Calibri, Verdana, Trebuchet MS
- Courier New, Monaco, Menlo, Source Code Pro, JetBrains Mono

## Examples

### Before (Default Font)
Uses system font stack for consistent cross-platform appearance.

### After (Georgia)
Classic serif font provides a traditional reading experience, similar to printed books.

### After (San Francisco)
Modern sans-serif optimized for screen reading on macOS.

## Settings Location

Font preference is saved in:
- **macOS**: `~/Library/Preferences/com.MDViewer.UnifiedViewer.plist`
- **Linux**: `~/.config/MDViewer/UnifiedViewer.conf`
- **Windows**: Registry under `HKEY_CURRENT_USER\Software\MDViewer\UnifiedViewer`

Key: `viewer_font`
Value: Font name (e.g., "Georgia", "Default (System)")

## Future Enhancements

Planned features:
- Font size adjustment
- Line height customization
- Font weight options
- Custom font favorites
- Import additional fonts
- Per-file font preferences

---

💡 **Tip**: Try different fonts to find what works best for your reading style!
