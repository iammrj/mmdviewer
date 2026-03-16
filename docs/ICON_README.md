# App Icon

## Design

The Markdown & Mermaid Viewer icon features:

- **Blue gradient background** - Professional, modern look
- **White "M↓" symbol** - Represents Markdown with down arrow
- **Yellow arrow** - Highlights the "down" part of Markdown
- **Flowchart elements** - Subtle references to Mermaid diagrams
- **Rounded corners** - macOS standard design

## Files

- `icon_source.svg` - Source SVG (1024x1024)
- `icon.icns` - macOS icon bundle (all sizes)
- `icon_preview.png` - 512x512 preview
- `generate_icon.py` - Icon generation script

## Sizes Included

The `.icns` file contains all required macOS icon sizes:
- 16x16, 16x16@2x (32x32)
- 32x32, 32x32@2x (64x64)
- 128x128, 128x128@2x (256x256)
- 256x256, 256x256@2x (512x512)
- 512x512, 512x512@2x (1024x1024)

## Regenerating the Icon

If you modify `icon_source.svg`, regenerate the icon:

```bash
python generate_icon.py
```

Requirements:
```bash
pip install pillow cairosvg
```

## Usage in Build

The icon is automatically included when building:

```bash
./build_dmg.sh
```

It will appear:
- In Finder as the app icon
- In the Dock when running
- In Applications folder
- In the DMG window
