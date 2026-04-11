import sys
import os
import logging
import re
import html
import textwrap
from pathlib import Path
from typing import Optional, Dict, Tuple
import markdown
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QAction, QFileDialog,
                             QSplitter, QToolBar, QWidget, QVBoxLayout, QMessageBox,
                             QMenu, QStatusBar, QLabel, QActionGroup, QApplication as QApp,
                             QDialog, QLineEdit, QPushButton, QHBoxLayout, QCheckBox, QListWidget, QListWidgetItem,
                             QDockWidget, QTreeWidget, QTreeWidgetItem, QDialogButtonBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtCore import Qt, QTimer, QSettings, QSize, QUrl, QRect, QTime
from PyQt5.QtGui import QFont, QKeySequence, QCloseEvent, QFontDatabase, QTextCursor, QPainter, QColor, QImage, QIcon, QPixmap
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from . import __version__, __app_name__

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

MERMAID_FENCE_PATTERN = re.compile(
    r'^(?P<indent>[ \t]{0,3})(?P<fence>`{3,}|~{3,})[ \t]*mermaid(?:[^\n]*)\n(?P<code>.*?)(?:\n(?P=indent)(?P=fence)[ \t]*$)',
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)


class EditorWithLineNumbers(QTextEdit):
    """Custom text editor with line numbers"""
    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize line number area manually
        from .widgets.line_numbers import LineNumberArea
        self.line_number_area = LineNumberArea(self)
        self.show_line_numbers = False

        # Connect signals after QTextEdit is fully initialized
        # Note: QPlainTextEdit uses blockCountChanged, but QTextEdit uses document().blockCountChanged
        self.document().blockCountChanged.connect(self.update_line_number_area_width)
        self.verticalScrollBar().valueChanged.connect(lambda: self.line_number_area.update())

    def line_number_area_width(self):
        if not self.show_line_numbers:
            return 0

        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _=None):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self):
        """Update the line number area"""
        self.line_number_area.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(240, 240, 240))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor(100, 100, 100))
                painter.drawText(0, int(top), self.line_number_area.width() - 5,
                               self.fontMetrics().height(), Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def toggle_line_numbers(self, show):
        self.show_line_numbers = show
        self.update_line_number_area_width()
        self.line_number_area.setVisible(show)


class UnifiedViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file: Optional[str] = None
        self.file_type: Optional[str] = None  # 'markdown' or 'mermaid'
        self.edit_mode = False
        self.is_modified = False
        self.settings = QSettings("MDViewer", "UnifiedViewer")

        self.md_converter = markdown.Markdown(extensions=[
            'extra', 'codehilite', 'toc', 'tables', 'fenced_code', 'nl2br'
        ])

        # Default font for viewer
        self.viewer_font = self.settings.value("viewer_font", "Default (System)")

        # Zoom level (percentage)
        self.zoom_level = self.settings.value("zoom_level", 100, type=int)

        # Dark mode
        self.dark_mode = self.settings.value("dark_mode", False, type=bool)

        # Auto-save settings
        self.auto_save_enabled = self.settings.value("auto_save_enabled", True, type=bool)
        self.auto_save_interval = self.settings.value("auto_save_interval", 60, type=int)  # seconds
        self.draft_dir = Path.home() / ".mdviewer" / "drafts"
        self.draft_dir.mkdir(parents=True, exist_ok=True)

        # TOC settings
        self.toc_visible = self.settings.value("toc_visible", False, type=bool)

        # Favorites settings
        self.favorites = self.settings.value("favorites", [], type=list)

        # Image paste directory
        self.images_dir = None  # Will be set when file is opened

        self.init_ui()
        self.restore_settings()
        self.setup_auto_save()
        self.check_draft_recovery()
        logger.info(f"{__app_name__} v{__version__} started")

    def init_ui(self):
        self.setWindowTitle(__app_name__)
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(QSize(800, 600))

        # Set application icon
        icon_path = Path(__file__).parent.parent / "assets" / "icons" / "icon_preview.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Horizontal)

        self.editor = EditorWithLineNumbers()
        self.editor.setFont(QFont('Courier New', 11))
        self.editor.textChanged.connect(self.on_text_changed)
        self.editor.setPlaceholderText("Enter markdown or mermaid diagram here...")
        self.editor.hide()

        # Install event filter for image paste support
        self.editor.installEventFilter(self)

        self.viewer = QWebEngineView()

        # Configure WebEngine settings
        settings = self.viewer.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)

        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.viewer)
        self.splitter.setSizes([600, 600])

        layout.addWidget(self.splitter)

        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.create_toc_panel()

        self.render_timer = QTimer()
        self.render_timer.setSingleShot(True)
        self.render_timer.timeout.connect(self.render_content)

        self.show_welcome_message()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('&File')

        open_action = QAction('&Open...', self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        self.recent_menu = QMenu('Open &Recent', self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_files_menu()

        self.favorites_menu = QMenu('&Favorites', self)
        file_menu.addMenu(self.favorites_menu)
        self.update_favorites_menu()

        # Toggle favorite for current file
        self.favorite_action = QAction('★ Add to Favorites', self)
        self.favorite_action.setShortcut('Ctrl+B')
        self.favorite_action.triggered.connect(self.toggle_favorite)
        self.favorite_action.setEnabled(False)
        file_menu.addAction(self.favorite_action)

        file_menu.addSeparator()

        # Templates menu
        templates_menu = QMenu('&Templates', self)
        file_menu.addMenu(templates_menu)
        self.create_templates_menu(templates_menu)

        file_menu.addSeparator()

        self.save_action = QAction('&Save', self)
        self.save_action.setShortcut(QKeySequence.Save)
        self.save_action.triggered.connect(self.save_file)
        self.save_action.setEnabled(False)
        file_menu.addAction(self.save_action)

        save_as_action = QAction('Save &As...', self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        self.export_menu = QMenu('&Export', self)

        export_html_action = QAction('Export as &HTML...', self)
        export_html_action.setShortcut('Ctrl+Shift+H')
        export_html_action.triggered.connect(self.export_html)
        self.export_menu.addAction(export_html_action)

        self.export_png_action = QAction('Export as &PNG...', self)
        self.export_png_action.setShortcut('Ctrl+Shift+P')
        self.export_png_action.triggered.connect(self.export_png)
        self.export_menu.addAction(self.export_png_action)

        self.export_pdf_action = QAction('Export as P&DF...', self)
        self.export_pdf_action.setShortcut('Ctrl+Shift+D')
        self.export_pdf_action.triggered.connect(self.export_pdf)
        self.export_menu.addAction(self.export_pdf_action)

        file_menu.addMenu(self.export_menu)

        file_menu.addSeparator()

        # Print Preview
        print_preview_action = QAction('Print Pre&view...', self)
        print_preview_action.setShortcut('Ctrl+Shift+V')
        print_preview_action.triggered.connect(self.show_print_preview)
        file_menu.addAction(print_preview_action)

        file_menu.addSeparator()

        # Copy as HTML
        copy_html_action = QAction('Copy as &HTML', self)
        copy_html_action.setShortcut('Ctrl+Shift+C')
        copy_html_action.triggered.connect(self.copy_as_html)
        file_menu.addAction(copy_html_action)

        file_menu.addSeparator()

        # Find
        find_action = QAction('&Find...', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.show_find_dialog)
        file_menu.addAction(find_action)

        file_menu.addSeparator()

        quit_action = QAction('&Quit', self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # View menu
        view_menu = menubar.addMenu('&View')

        self.toggle_action = QAction('&Edit Mode', self)
        self.toggle_action.setShortcut('Ctrl+E')
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.toggle_edit_mode)
        view_menu.addAction(self.toggle_action)

        view_menu.addSeparator()

        # Font menu
        self.font_menu = QMenu('&Reader Font', self)
        view_menu.addMenu(self.font_menu)
        self.create_font_menu()

        view_menu.addSeparator()

        # Zoom menu
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction('&Reset Zoom', self)
        reset_zoom_action.setShortcut('Ctrl+0')
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        view_menu.addSeparator()

        # Full screen
        self.fullscreen_action = QAction('&Full Screen', self)
        self.fullscreen_action.setShortcut('F11')
        self.fullscreen_action.setCheckable(True)
        self.fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.fullscreen_action)

        view_menu.addSeparator()

        # Dark mode
        self.dark_mode_action = QAction('&Dark Mode', self)
        self.dark_mode_action.setShortcut('Ctrl+D')
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)

        view_menu.addSeparator()

        # Line numbers
        self.line_numbers_action = QAction('Show Line &Numbers', self)
        self.line_numbers_action.setShortcut('Ctrl+L')
        self.line_numbers_action.setCheckable(True)
        self.line_numbers_action.setChecked(False)
        self.line_numbers_action.triggered.connect(self.toggle_line_numbers)
        view_menu.addAction(self.line_numbers_action)

        view_menu.addSeparator()

        # Auto-save
        self.auto_save_action = QAction('&Auto-Save', self)
        self.auto_save_action.setShortcut('Ctrl+Shift+A')
        self.auto_save_action.setCheckable(True)
        self.auto_save_action.setChecked(self.auto_save_enabled)
        self.auto_save_action.triggered.connect(self.toggle_auto_save)
        view_menu.addAction(self.auto_save_action)

        view_menu.addSeparator()

        # Table of Contents
        self.toc_action = QAction('&Table of Contents', self)
        self.toc_action.setShortcut('Ctrl+T')
        self.toc_action.setCheckable(True)
        self.toc_action.setChecked(self.toc_visible)
        self.toc_action.triggered.connect(self.toggle_toc)
        view_menu.addAction(self.toc_action)

        # Help menu
        help_menu = menubar.addMenu('&Help')

        help_action = QAction('&Documentation', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        cheatsheet_action = QAction('Markdown &Cheat Sheet', self)
        cheatsheet_action.setShortcut('Ctrl+?')
        cheatsheet_action.triggered.connect(self.show_cheatsheet)
        help_menu.addAction(cheatsheet_action)

        help_menu.addSeparator()

        about_action = QAction('&About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        open_action = QAction('Open', self)
        open_action.setToolTip('Open file (Ctrl+O)')
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)

        save_btn = QAction('Save', self)
        save_btn.setToolTip('Save file (Ctrl+S)')
        save_btn.triggered.connect(self.save_file)
        save_btn.setEnabled(False)
        toolbar.addAction(save_btn)
        self.save_toolbar_action = save_btn

        toolbar.addSeparator()

        toggle_btn = QAction('Edit Mode', self)
        toggle_btn.setToolTip('Toggle edit mode (Ctrl+E)')
        toggle_btn.setCheckable(True)
        toggle_btn.triggered.connect(self.toggle_edit_mode)
        toolbar.addAction(toggle_btn)
        self.toggle_toolbar_action = toggle_btn

    def create_status_bar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        self.status_label = QLabel("Ready")
        self.statusbar.addWidget(self.status_label)

        self.file_type_label = QLabel("")
        self.statusbar.addPermanentWidget(self.file_type_label)

        self.word_count_label = QLabel("")
        self.statusbar.addPermanentWidget(self.word_count_label)

        self.line_col_label = QLabel("")
        self.statusbar.addPermanentWidget(self.line_col_label)

        self.editor.cursorPositionChanged.connect(self.update_cursor_position)
        self.editor.textChanged.connect(self.update_word_count)

    def update_cursor_position(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.line_col_label.setText(f"Line {line}, Col {col}")

    def update_word_count(self):
        """Update word count and statistics in status bar"""
        if self.file_type == 'mermaid':
            self.word_count_label.setText("")
            return

        text = self.editor.toPlainText()
        if not text.strip():
            self.word_count_label.setText("")
            return

        # Calculate statistics
        words = len(text.split())
        chars = len(text)
        chars_no_spaces = len(text.replace(" ", "").replace("\n", "").replace("\t", ""))

        # Estimate reading time (average 200 words per minute)
        reading_time = max(1, round(words / 200))

        stats = f"{words} words | {chars} chars | ~{reading_time} min read"
        self.word_count_label.setText(stats)

    def create_toc_panel(self):
        """Create Table of Contents panel as dockable widget"""
        self.toc_dock = QDockWidget("Table of Contents", self)
        self.toc_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.toc_tree = QTreeWidget()
        self.toc_tree.setHeaderHidden(True)
        self.toc_tree.itemClicked.connect(self.on_toc_item_clicked)

        self.toc_dock.setWidget(self.toc_tree)
        self.addDockWidget(Qt.RightDockWidgetArea, self.toc_dock)
        self.toc_dock.setVisible(self.toc_visible)

    def update_toc(self):
        """Update Table of Contents based on markdown headings"""
        self.toc_tree.clear()

        if self.file_type != 'markdown' or not self.current_file:
            return

        text = self.editor.toPlainText() if self.edit_mode else ""
        if not text and self.current_file:
            try:
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    text = f.read()
            except:
                return

        if not text:
            return

        import re
        # Parse markdown headings
        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        headings = []

        for match in heading_pattern.finditer(text):
            level = len(match.group(1))
            title = match.group(2).strip()
            line_num = text[:match.start()].count('\n') + 1
            headings.append((level, title, line_num))

        # Build tree structure
        root_items = []
        stack = [(0, None)]  # (level, item)

        for level, title, line_num in headings:
            item = QTreeWidgetItem([title])
            item.setData(0, Qt.UserRole, line_num)

            # Find parent
            while stack and stack[-1][0] >= level:
                stack.pop()

            if stack[-1][1] is None:
                root_items.append(item)
            else:
                stack[-1][1].addChild(item)

            stack.append((level, item))

        self.toc_tree.addTopLevelItems(root_items)
        self.toc_tree.expandAll()

    def on_toc_item_clicked(self, item, column):
        """Handle TOC item click - scroll to heading in editor"""
        if not self.edit_mode:
            return

        line_num = item.data(0, Qt.UserRole)
        if line_num:
            # Move cursor to line
            cursor = self.editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_num - 1)
            self.editor.setTextCursor(cursor)
            self.editor.setFocus()

    def toggle_toc(self):
        """Toggle Table of Contents visibility"""
        self.toc_visible = not self.toc_visible
        self.toc_dock.setVisible(self.toc_visible)
        self.toc_action.setChecked(self.toc_visible)
        self.settings.setValue("toc_visible", self.toc_visible)

        if self.toc_visible:
            self.update_toc()
            self.status_label.setText("Table of Contents shown")
        else:
            self.status_label.setText("Table of Contents hidden")

    def create_font_menu(self):
        """Create font selection menu with popular reading fonts"""
        # Popular fonts for reading
        popular_fonts = [
            "Default (System)",
            "Georgia",
            "Charter",
            "Iowan Old Style",
            "Palatino",
            "Times New Roman",
            "Helvetica Neue",
            "Helvetica",
            "Arial",
            "San Francisco",
            "Avenir",
            "Calibri",
            "Verdana",
            "Trebuchet MS",
            "Courier New",
            "Monaco",
            "Menlo",
            "Source Code Pro",
            "JetBrains Mono"
        ]

        # Get available system fonts
        font_database = QFontDatabase()
        system_fonts = font_database.families()

        # Filter to only available fonts
        available_fonts = ["Default (System)"]
        for font in popular_fonts[1:]:  # Skip "Default" since we added it
            if font in system_fonts:
                available_fonts.append(font)

        # Create action group for radio button behavior
        font_group = QActionGroup(self)
        font_group.setExclusive(True)

        for font_name in available_fonts:
            action = QAction(font_name, self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, f=font_name: self.change_viewer_font(f))

            if font_name == self.viewer_font:
                action.setChecked(True)

            font_group.addAction(action)
            self.font_menu.addAction(action)

    def change_viewer_font(self, font_name: str):
        """Change the font used in the markdown viewer"""
        self.viewer_font = font_name
        self.settings.setValue("viewer_font", font_name)

        # Re-render current content with new font
        if self.current_file or self.editor.toPlainText():
            self.render_content()

        self.status_label.setText(f"Font changed to: {font_name}")
        logger.info(f"Viewer font changed to: {font_name}")

    def zoom_in(self):
        """Increase zoom level by 10%"""
        self.zoom_level = min(self.zoom_level + 10, 300)  # Max 300%
        self.apply_zoom()
        self.settings.setValue("zoom_level", self.zoom_level)
        self.status_label.setText(f"Zoom: {self.zoom_level}%")

    def zoom_out(self):
        """Decrease zoom level by 10%"""
        self.zoom_level = max(self.zoom_level - 10, 50)  # Min 50%
        self.apply_zoom()
        self.settings.setValue("zoom_level", self.zoom_level)
        self.status_label.setText(f"Zoom: {self.zoom_level}%")

    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_level = 100
        self.apply_zoom()
        self.settings.setValue("zoom_level", self.zoom_level)
        self.status_label.setText("Zoom reset to 100%")

    def apply_zoom(self):
        """Apply current zoom level to viewer"""
        zoom_factor = self.zoom_level / 100.0
        self.viewer.setZoomFactor(zoom_factor)
        logger.info(f"Zoom level: {self.zoom_level}%")

    def toggle_fullscreen(self):
        """Toggle full screen mode"""
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_action.setChecked(False)
            self.status_label.setText("Exited full screen")
        else:
            self.showFullScreen()
            self.fullscreen_action.setChecked(True)
            self.status_label.setText("Full screen mode (F11 to exit)")
        logger.info(f"Full screen: {self.isFullScreen()}")

    def toggle_dark_mode(self):
        """Toggle dark mode"""
        self.dark_mode = not self.dark_mode
        self.settings.setValue("dark_mode", self.dark_mode)
        self.dark_mode_action.setChecked(self.dark_mode)

        # Re-render content with new theme
        if self.current_file or self.editor.toPlainText():
            self.render_content()

        mode = "Dark" if self.dark_mode else "Light"
        self.status_label.setText(f"{mode} mode enabled")
        logger.info(f"Dark mode: {self.dark_mode}")

    def show_find_dialog(self):
        """Show find dialog"""
        if not self.edit_mode:
            QMessageBox.information(self, "Find", "Find is only available in Edit Mode.\n\nPress Ctrl+E to enable Edit Mode.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Find")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Search input
        search_layout = QHBoxLayout()
        search_label = QLabel("Find:")
        self.search_input = QLineEdit()
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Options
        options_layout = QHBoxLayout()
        self.case_sensitive_cb = QCheckBox("Case sensitive")
        self.whole_word_cb = QCheckBox("Whole words")
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        layout.addLayout(options_layout)

        # Buttons
        button_layout = QHBoxLayout()
        find_next_btn = QPushButton("Find Next")
        find_prev_btn = QPushButton("Find Previous")
        close_btn = QPushButton("Close")

        find_next_btn.clicked.connect(lambda: self.find_text(forward=True))
        find_prev_btn.clicked.connect(lambda: self.find_text(forward=False))
        close_btn.clicked.connect(dialog.close)

        button_layout.addWidget(find_prev_btn)
        button_layout.addWidget(find_next_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        self.search_input.setFocus()
        dialog.show()

    def find_text(self, forward=True):
        """Find text in editor"""
        search_text = self.search_input.text()
        if not search_text:
            return

        flags = QTextCursor.FindFlags()
        if not forward:
            flags |= QTextCursor.FindBackward
        if self.case_sensitive_cb.isChecked():
            flags |= QTextCursor.FindCaseSensitively
        if self.whole_word_cb.isChecked():
            flags |= QTextCursor.FindWholeWords

        found = self.editor.find(search_text, flags)

        if not found:
            # Wrap around
            cursor = self.editor.textCursor()
            if forward:
                cursor.movePosition(QTextCursor.Start)
            else:
                cursor.movePosition(QTextCursor.End)
            self.editor.setTextCursor(cursor)
            found = self.editor.find(search_text, flags)

        if found:
            self.status_label.setText(f"Found: {search_text}")
        else:
            self.status_label.setText(f"Not found: {search_text}")

    def toggle_line_numbers(self):
        """Toggle line numbers in editor"""
        show = self.line_numbers_action.isChecked()
        self.editor.toggle_line_numbers(show)
        if show:
            self.status_label.setText("Line numbers shown")
        else:
            self.status_label.setText("Line numbers hidden")
        logger.info(f"Line numbers: {show}")

    def detect_file_type(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.mmd', '.mermaid']:
            return 'mermaid'
        return 'markdown'

    def open_file(self, file_path: str = None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Open File', self.get_last_directory(),
                'All Supported (*.md *.markdown *.mmd *.mermaid);;'
                'Markdown Files (*.md *.markdown);;'
                'Mermaid Files (*.mmd *.mermaid);;'
                'All Files (*)'
            )

        if not file_path:
            return

        if not self.check_save_changes():
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.current_file = file_path
            self.file_type = self.detect_file_type(file_path)
            self.editor.setText(content)
            self.is_modified = False
            self.render_content()
            self.save_action.setEnabled(True)
            self.save_toolbar_action.setEnabled(True)
            self.setWindowTitle(f'{__app_name__} - {os.path.basename(file_path)}')
            self.status_label.setText(f"Opened: {file_path}")
            self.file_type_label.setText(f"Type: {self.file_type.upper()}")
            self.update_word_count()  # Update word count on file open
            self.add_recent_file(file_path)
            self.update_favorite_button()  # Update favorite button state
            self.settings.setValue("last_directory", os.path.dirname(file_path))
            logger.info(f"Opened {self.file_type} file: {file_path}")

        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            QMessageBox.critical(self, "Error", f"Could not open file:\n{str(e)}")

    def save_file(self):
        if not self.current_file:
            self.save_file_as()
            return

        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())

            self.is_modified = False
            self.update_window_title()
            self.status_label.setText(f"Saved: {self.current_file}")
            logger.info(f"Saved file: {self.current_file}")

            # Clean up draft after successful save
            self.cleanup_draft()

        except Exception as e:
            logger.error(f"Error saving file: {e}")
            QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")

    def save_file_as(self):
        if self.file_type == 'mermaid':
            filter_str = 'Mermaid Files (*.mmd);;All Files (*)'
        else:
            filter_str = 'Markdown Files (*.md);;All Files (*)'

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Save File', self.get_last_directory(), filter_str
        )

        if file_path:
            self.current_file = file_path
            self.file_type = self.detect_file_type(file_path)
            self.save_file()
            self.save_action.setEnabled(True)
            self.save_toolbar_action.setEnabled(True)
            self.add_recent_file(file_path)

    def copy_as_html(self):
        """Copy rendered HTML to clipboard"""
        if not self.current_file and not self.editor.toPlainText():
            QMessageBox.warning(self, "Warning", "No content to copy")
            return

        try:
            html_content = self.generate_export_html()
            clipboard = QApplication.clipboard()
            clipboard.setText(html_content)
            self.status_label.setText("HTML copied to clipboard")
            logger.info("HTML copied to clipboard")
            QMessageBox.information(self, "Success", "HTML copied to clipboard!\n\nYou can now paste it into emails, blogs, or other applications.")
        except Exception as e:
            logger.error(f"Error copying HTML: {e}")
            QMessageBox.critical(self, "Error", f"Could not copy HTML:\n{str(e)}")

    def export_html(self):
        if not self.current_file and not self.editor.toPlainText():
            QMessageBox.warning(self, "Warning", "No content to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export HTML', self.get_last_directory(),
            'HTML Files (*.html);;All Files (*)'
        )

        if file_path:
            try:
                html_content = self.generate_export_html()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                self.status_label.setText(f"Exported HTML: {file_path}")
                logger.info(f"Exported HTML: {file_path}")
                QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")

            except Exception as e:
                logger.error(f"Error exporting HTML: {e}")
                QMessageBox.critical(self, "Error", f"Could not export:\n{str(e)}")

    def export_png(self):
        if self.file_type != 'mermaid':
            QMessageBox.warning(self, "Warning", "PNG export is only available for Mermaid diagrams")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export PNG', self.get_last_directory(),
            'PNG Files (*.png);;All Files (*)'
        )

        if file_path:
            self.capture_screenshot(file_path, 'png')

    def export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Export PDF', self.get_last_directory(),
            'PDF Files (*.pdf);;All Files (*)'
        )

        if file_path:
            try:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)

                self.viewer.page().printToPdf(file_path)

                self.status_label.setText(f"Exported PDF: {file_path}")
                logger.info(f"Exported PDF: {file_path}")
                QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")

            except Exception as e:
                logger.error(f"Error exporting PDF: {e}")
                QMessageBox.critical(self, "Error", f"Could not export PDF:\n{str(e)}")

    def show_print_preview(self):
        """Show print preview dialog"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            printer.setPageSize(QPrinter.Letter)
            printer.setPageMargins(15, 15, 15, 15, QPrinter.Millimeter)

            preview = QPrintPreviewDialog(printer, self)
            preview.setWindowTitle("Print Preview")
            preview.paintRequested.connect(self.handle_print_requested)
            preview.exec_()

            self.status_label.setText("Print preview closed")

        except Exception as e:
            logger.error(f"Error showing print preview: {e}")
            QMessageBox.critical(self, "Error", f"Could not show print preview:\n{str(e)}")

    def handle_print_requested(self, printer):
        """Handle print request from preview dialog"""
        try:
            # Print the web view content
            self.viewer.page().print(printer, lambda success: None)
        except Exception as e:
            logger.error(f"Error printing: {e}")

    def capture_screenshot(self, file_path: str, format_type: str):
        # Use JavaScript to capture the full SVG and convert to canvas
        js_code = """
        (function() {
            var svg = document.querySelector('svg');
            if (!svg) return null;

            var canvas = document.createElement('canvas');
            var bbox = svg.getBBox();
            var padding = 40;

            canvas.width = bbox.width + (padding * 2);
            canvas.height = bbox.height + (padding * 2);

            var ctx = canvas.getContext('2d');
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            var data = new XMLSerializer().serializeToString(svg);
            var img = new Image();
            var svgBlob = new Blob([data], {type: 'image/svg+xml;charset=utf-8'});
            var url = URL.createObjectURL(svgBlob);

            return new Promise(function(resolve) {
                img.onload = function() {
                    ctx.drawImage(img, padding, padding);
                    URL.revokeObjectURL(url);
                    resolve(canvas.toDataURL('image/png'));
                };
                img.src = url;
            });
        })();
        """

        def handle_result(result):
            try:
                if result and result.startswith('data:image/png;base64,'):
                    import base64
                    img_data = base64.b64decode(result.split(',')[1])
                    with open(file_path, 'wb') as f:
                        f.write(img_data)

                    self.status_label.setText(f"Exported {format_type.upper()}: {file_path}")
                    logger.info(f"Exported {format_type.upper()}: {file_path}")
                    QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
                else:
                    # Fallback to simple screenshot
                    pixmap = self.viewer.grab()
                    if pixmap.save(file_path):
                        self.status_label.setText(f"Exported {format_type.upper()}: {file_path}")
                        logger.info(f"Exported {format_type.upper()}: {file_path}")
                        QMessageBox.information(self, "Success", f"Exported to:\n{file_path}")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to save image")
            except Exception as e:
                logger.error(f"Error saving image: {e}")
                QMessageBox.critical(self, "Error", f"Could not save image:\n{str(e)}")

        self.viewer.page().runJavaScript(js_code, handle_result)

    def check_save_changes(self) -> bool:
        if self.is_modified:
            reply = QMessageBox.question(
                self, 'Unsaved Changes',
                'Do you want to save your changes?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_file()
                return True
            elif reply == QMessageBox.Cancel:
                return False

        return True

    def toggle_edit_mode(self, checked=None):
        if checked is None:
            self.edit_mode = not self.edit_mode
        else:
            self.edit_mode = bool(checked)

        if self.edit_mode:
            self.editor.show()
            self.splitter.setSizes([600, 600])
            self.status_label.setText("Edit mode enabled")
        else:
            self.editor.hide()
            self.status_label.setText("View mode enabled")

        self.toggle_action.setChecked(self.edit_mode)
        self.toggle_toolbar_action.setChecked(self.edit_mode)

    def on_text_changed(self):
        self.is_modified = True
        self.update_window_title()
        self.render_timer.start(300)

    def update_window_title(self):
        title = __app_name__
        if self.current_file:
            title += f" - {os.path.basename(self.current_file)}"
        if self.is_modified:
            title += " *"
        self.setWindowTitle(title)

    def render_content(self):
        if not self.current_file and not self.editor.toPlainText().strip():
            return

        if self.file_type == 'mermaid':
            self.render_mermaid()
        else:
            self.render_markdown()

    def render_markdown(self):
        markdown_text = self.editor.toPlainText()
        html_content, has_mermaid_blocks = self.convert_markdown_to_html(markdown_text)
        full_html = self.generate_markdown_html(html_content, has_mermaid_blocks)
        self.viewer.setHtml(full_html, baseUrl=self.get_base_url())
        self.apply_zoom()  # Reapply zoom after render

        # Update TOC if visible
        if self.toc_visible:
            self.update_toc()

    def render_mermaid(self):
        mermaid_code = self.editor.toPlainText()
        html_content = self.generate_mermaid_html(mermaid_code)
        self.viewer.setHtml(html_content)
        self.apply_zoom()  # Reapply zoom after render

    def convert_markdown_to_html(self, markdown_text: str) -> Tuple[str, bool]:
        markdown_with_placeholders, mermaid_blocks = self.extract_mermaid_blocks(markdown_text)
        html_content = self.md_converter.convert(markdown_with_placeholders)
        self.md_converter.reset()

        def _replace_placeholder(match):
            token = match.group("token")
            return mermaid_blocks.get(token, match.group(0))

        html_content = re.sub(
            r'<div class="mdv-mermaid-placeholder" data-mdv-mermaid="(?P<token>[^"]+)"></div>',
            _replace_placeholder,
            html_content
        )

        has_mermaid_blocks = bool(mermaid_blocks) or 'class="mermaid"' in html_content
        return html_content, has_mermaid_blocks

    def extract_mermaid_blocks(self, markdown_text: str) -> Tuple[str, Dict[str, str]]:
        mermaid_blocks: Dict[str, str] = {}

        def _replace(match):
            code = textwrap.dedent(match.group("code")).strip()
            token = f"mdv-mermaid-{len(mermaid_blocks)}"
            mermaid_blocks[token] = (
                '<div class="mdv-mermaid-block">'
                f'<div class="mermaid">{html.escape(code)}</div>'
                '</div>'
            )
            return (
                f'\n\n<div class="mdv-mermaid-placeholder" '
                f'data-mdv-mermaid="{token}"></div>\n\n'
            )

        markdown_with_tokens = MERMAID_FENCE_PATTERN.sub(_replace, markdown_text)
        return markdown_with_tokens, mermaid_blocks

    def get_pygments_css(self) -> str:
        try:
            from pygments.formatters import HtmlFormatter
            pygments_style = "monokai" if self.dark_mode else "default"
            return HtmlFormatter(style=pygments_style).get_style_defs('.codehilite')
        except Exception:
            return ""

    def generate_markdown_html(self, content: str, has_mermaid_blocks: bool = False) -> str:
        # Get font family based on selection
        if self.viewer_font == "Default (System)":
            font_family = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"
        else:
            # Use selected font with fallbacks
            font_family = f"'{self.viewer_font}', -apple-system, BlinkMacSystemFont, serif"

        # Theme colors
        if self.dark_mode:
            bg_color = "#1e1e1e"
            text_color = "#d4d4d4"
            border_color = "#404040"
            code_bg = "#2d2d2d"
            link_color = "#4fc3f7"
            blockquote_color = "#a0a0a0"
        else:
            bg_color = "#ffffff"
            text_color = "#24292e"
            border_color = "#eaecef"
            code_bg = "#f6f8fa"
            link_color = "#0366d6"
            blockquote_color = "#6a737d"

        pygments_css = self.get_pygments_css()
        mermaid_theme = "dark" if self.dark_mode else "default"
        mermaid_assets = ""

        if has_mermaid_blocks:
            mermaid_assets = f"""
    <script src="https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js"></script>
    <script>
        (function() {{
            function renderMermaidBlocks() {{
                if (typeof mermaid === 'undefined') {{
                    return;
                }}

                try {{
                    mermaid.initialize({{
                        startOnLoad: false,
                        securityLevel: 'loose',
                        theme: '{mermaid_theme}'
                    }});
                    mermaid.init(undefined, document.querySelectorAll('.mdv-mermaid-block .mermaid'));
                }} catch (error) {{
                    console.error('Mermaid render error:', error);
                }}
            }}

            if (document.readyState === 'loading') {{
                document.addEventListener('DOMContentLoaded', renderMermaidBlocks);
            }} else {{
                renderMermaidBlocks();
            }}
        }})();
    </script>
"""

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: {font_family};
            line-height: 1.6;
            padding: 20px 40px;
            max-width: 900px;
            margin: 0 auto;
            background-color: {bg_color};
            color: {text_color};
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
        }}
        h1 {{ font-size: 2em; border-bottom: 1px solid {border_color}; padding-bottom: 0.3em; }}
        h2 {{ font-size: 1.5em; border-bottom: 1px solid {border_color}; padding-bottom: 0.3em; }}
        code {{
            background-color: {code_bg};
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 85%;
            color: {text_color};
        }}
        pre {{
            background-color: {code_bg};
            padding: 16px;
            border-radius: 6px;
            overflow: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
            border-radius: 0;
            font-size: inherit;
            color: inherit;
        }}
        .codehilite {{
            background-color: {code_bg};
            margin: 0 0 16px 0;
            border-radius: 6px;
            overflow: auto;
            padding: 16px;
        }}
        .codehilite pre {{
            margin: 0;
            padding: 0;
            background: transparent;
            border-radius: 0;
        }}
        .mdv-mermaid-block {{
            margin: 16px 0;
            padding: 16px;
            border: 1px solid {border_color};
            border-radius: 6px;
            background: {code_bg};
            overflow-x: auto;
        }}
        .mdv-mermaid-block .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}
        blockquote {{
            padding: 0 1em;
            color: {blockquote_color};
            border-left: 0.25em solid {border_color};
            margin: 0 0 16px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }}
        table th, table td {{
            padding: 6px 13px;
            border: 1px solid {border_color};
        }}
        table tr:nth-child(2n) {{ background-color: {code_bg}; }}
        a {{ color: {link_color}; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        img {{ max-width: 100%; height: auto; }}
        {pygments_css}
    </style>
</head>
<body>{content}{mermaid_assets}</body>
</html>'''

    def generate_mermaid_html(self, mermaid_code: str) -> str:
        # Escape code properly for JavaScript
        js_safe_code = mermaid_code.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$')

        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>
        // Polyfill for structuredClone (for older browsers)
        if (typeof structuredClone === 'undefined') {{
            window.structuredClone = function(obj) {{
                return JSON.parse(JSON.stringify(obj));
            }};
        }}
    </script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@9.4.3/dist/mermaid.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: auto;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        #mermaid-container {{
            background-color: white;
            padding: 30px 40px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow-x: auto;
            overflow-y: auto;
            width: calc(100% - 40px);
            max-width: none;
            box-sizing: border-box;
        }}
        #diagram {{
            min-width: max-content;
            overflow: visible;
            display: block;
        }}
        /* Basic Mermaid styles */
        .mermaid svg {{
            max-width: 100%;
            height: auto;
        }}
        .error {{
            color: #dc3545;
            padding: 20px;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
        }}
        .loading {{
            padding: 20px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div id="mermaid-container">
        <div id="diagram" class="loading">Loading diagram...</div>
    </div>

    <script>
        // Wait for mermaid to be available
        if (typeof mermaid === 'undefined') {{
            document.getElementById('diagram').innerHTML =
                '<div class="error">Mermaid library failed to load. Check internet connection.</div>';
        }} else {{
            mermaid.initialize({{
                startOnLoad: false,
                theme: 'default',
                securityLevel: 'loose',
                logLevel: 'error',
                flowchart: {{
                    htmlLabels: true,
                    curve: 'basis',
                    padding: 20
                }},
                gantt: {{
                    titleTopMargin: 25,
                    barHeight: 30,
                    barGap: 8,
                    topPadding: 50,
                    leftPadding: 175,
                    rightPadding: 40,
                    gridLineStartPadding: 75,
                    fontSize: 12,
                    sectionFontSize: 13,
                    numberSectionStyles: 4,
                    axisFormat: '%m/%d',
                    tickInterval: '1week',
                    weekday: 'monday'
                }},
                sequence: {{
                    wrap: true,
                    mirrorActors: true,
                    width: 150
                }}
            }});

            var code = `{js_safe_code}`;

            try {{
                // Mermaid 9.x API uses callback-based render
                mermaid.mermaidAPI.render('mermaid-diagram', code, function(svgCode) {{
                    document.getElementById('diagram').innerHTML = svgCode;
                    console.log('Mermaid diagram rendered successfully');
                }}, document.getElementById('diagram'));
            }} catch(error) {{
                console.error('Mermaid error:', error);
                document.getElementById('diagram').innerHTML =
                    '<div class="error"><strong>Error rendering diagram:</strong><br>' +
                    (error.message || error.toString()) + '</div>';
            }}
        }}
    </script>
</body>
</html>'''

    def generate_export_html(self) -> str:
        if self.file_type == 'mermaid':
            return self.generate_mermaid_html(self.editor.toPlainText())
        else:
            content, has_mermaid_blocks = self.convert_markdown_to_html(self.editor.toPlainText())
            return self.generate_markdown_html(content, has_mermaid_blocks)

    def get_base_url(self):
        if self.current_file:
            return QUrl.fromLocalFile(os.path.dirname(self.current_file) + "/")
        return QUrl()

    def get_last_directory(self) -> str:
        last_dir = self.settings.value("last_directory", "")
        return last_dir if last_dir and os.path.exists(last_dir) else str(Path.home())

    def add_recent_file(self, file_path: str):
        recent_files = self.settings.value("recent_files", [])
        if not isinstance(recent_files, list):
            recent_files = []

        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        recent_files = recent_files[:10]

        self.settings.setValue("recent_files", recent_files)
        self.update_recent_files_menu()

    def update_recent_files_menu(self):
        self.recent_menu.clear()
        recent_files = self.settings.value("recent_files", [])

        if not recent_files:
            action = QAction("No recent files", self)
            action.setEnabled(False)
            self.recent_menu.addAction(action)
            return

        for file_path in recent_files:
            if os.path.exists(file_path):
                action = QAction(os.path.basename(file_path), self)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, f=file_path: self.open_file(f))
                self.recent_menu.addAction(action)

    def update_favorites_menu(self):
        """Update favorites menu"""
        self.favorites_menu.clear()

        if not self.favorites:
            action = QAction("No favorites", self)
            action.setEnabled(False)
            self.favorites_menu.addAction(action)
            return

        for file_path in self.favorites:
            if os.path.exists(file_path):
                action = QAction(f"★ {os.path.basename(file_path)}", self)
                action.setToolTip(file_path)
                action.triggered.connect(lambda checked, f=file_path: self.open_file(f))
                self.favorites_menu.addAction(action)

        # Add manage favorites option
        self.favorites_menu.addSeparator()
        manage_action = QAction("Manage Favorites...", self)
        manage_action.triggered.connect(self.show_manage_favorites)
        self.favorites_menu.addAction(manage_action)

    def toggle_favorite(self):
        """Toggle current file as favorite"""
        if not self.current_file:
            return

        if self.current_file in self.favorites:
            self.favorites.remove(self.current_file)
            self.favorite_action.setText("★ Add to Favorites")
            self.status_label.setText("Removed from favorites")
        else:
            self.favorites.append(self.current_file)
            self.favorite_action.setText("☆ Remove from Favorites")
            self.status_label.setText("Added to favorites")

        self.settings.setValue("favorites", self.favorites)
        self.update_favorites_menu()

    def update_favorite_button(self):
        """Update favorite button text based on current file"""
        if not self.current_file:
            self.favorite_action.setEnabled(False)
            return

        self.favorite_action.setEnabled(True)
        if self.current_file in self.favorites:
            self.favorite_action.setText("☆ Remove from Favorites")
        else:
            self.favorite_action.setText("★ Add to Favorites")

    def show_manage_favorites(self):
        """Show dialog to manage favorites"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Favorites")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        label = QLabel("Your favorite files:")
        layout.addWidget(label)

        list_widget = QListWidget()
        for fav in self.favorites:
            if os.path.exists(fav):
                item = QListWidgetItem(f"★ {fav}")
                item.setData(Qt.UserRole, fav)
                list_widget.addItem(item)

        layout.addWidget(list_widget)

        # Buttons
        button_layout = QHBoxLayout()
        open_btn = QPushButton("Open")
        remove_btn = QPushButton("Remove")
        close_btn = QPushButton("Close")

        def open_favorite():
            current = list_widget.currentItem()
            if current:
                file_path = current.data(Qt.UserRole)
                dialog.accept()
                self.open_file(file_path)

        def remove_favorite():
            current = list_widget.currentItem()
            if current:
                file_path = current.data(Qt.UserRole)
                self.favorites.remove(file_path)
                self.settings.setValue("favorites", self.favorites)
                list_widget.takeItem(list_widget.row(current))
                self.update_favorites_menu()
                self.update_favorite_button()

        open_btn.clicked.connect(open_favorite)
        remove_btn.clicked.connect(remove_favorite)
        close_btn.clicked.connect(dialog.accept)

        button_layout.addWidget(open_btn)
        button_layout.addWidget(remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        dialog.exec_()

    def create_templates_menu(self, templates_menu):
        """Create templates menu with pre-built markdown templates"""
        templates = {
            "README": self.template_readme,
            "Blog Post": self.template_blog,
            "Meeting Notes": self.template_meeting,
            "Project Documentation": self.template_project_docs,
            "TODO List": self.template_todo,
            "Changelog": self.template_changelog,
        }

        for name, template_func in templates.items():
            action = QAction(name, self)
            action.triggered.connect(template_func)
            templates_menu.addAction(action)

    def apply_template(self, template_content, filename="untitled.md"):
        """Apply a template to the editor"""
        if self.is_modified and self.current_file:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Current file has unsaved changes. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.current_file = None
        self.file_type = 'markdown'
        self.editor.setPlainText(template_content)
        self.is_modified = True
        self.toggle_edit_mode(True)
        self.render_content()
        self.setWindowTitle(f"{__app_name__} - {filename} *")
        self.status_label.setText(f"Template loaded: {filename}")

    def template_readme(self):
        """README template"""
        template = """# Project Name

## Description

A brief description of your project.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation

```bash
# Installation commands
npm install
```

## Usage

```python
# Usage example
import module
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Contact

- Author: Your Name
- Email: your.email@example.com
- GitHub: [@username](https://github.com/username)
"""
        self.apply_template(template, "README.md")

    def template_blog(self):
        """Blog post template"""
        template = """# Post Title

*Published on: [Date]*
*Author: [Your Name]*
*Tags: #tag1 #tag2 #tag3*

---

## Introduction

Write your introduction here. Hook the reader with an interesting opening.

## Main Content

### Section 1

Your main content goes here.

### Section 2

Continue your story or explanation.

### Section 3

More details and insights.

## Conclusion

Wrap up your post with key takeaways.

---

## Comments

What do you think? Leave a comment below!
"""
        self.apply_template(template, "blog-post.md")

    def template_meeting(self):
        """Meeting notes template"""
        template = """# Meeting Notes - [Topic]

**Date:** [Date]
**Time:** [Time]
**Location:** [Location/Virtual]
**Attendees:**
- [Name 1]
- [Name 2]
- [Name 3]

---

## Agenda

1. Topic 1
2. Topic 2
3. Topic 3

## Discussion Points

### Topic 1
- Point 1
- Point 2

### Topic 2
- Point 1
- Point 2

## Decisions Made

- [ ] Decision 1
- [ ] Decision 2

## Action Items

- [ ] Task 1 - Assigned to: [Name] - Due: [Date]
- [ ] Task 2 - Assigned to: [Name] - Due: [Date]
- [ ] Task 3 - Assigned to: [Name] - Due: [Date]

## Next Meeting

**Date:** [Date]
**Time:** [Time]
**Topics:** [Topics to discuss]
"""
        self.apply_template(template, "meeting-notes.md")

    def template_project_docs(self):
        """Project documentation template"""
        template = """# Project Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup](#setup)
4. [API Reference](#api-reference)
5. [Examples](#examples)

## Overview

### Purpose
Describe the purpose of this project.

### Key Features
- Feature 1
- Feature 2
- Feature 3

## Architecture

### System Design
```
[Add architecture diagram or description]
```

### Components
- **Component 1**: Description
- **Component 2**: Description
- **Component 3**: Description

## Setup

### Prerequisites
- Requirement 1
- Requirement 2

### Installation

```bash
# Clone repository
git clone https://github.com/username/repo.git

# Install dependencies
npm install

# Run application
npm start
```

## API Reference

### Endpoint 1

```
GET /api/endpoint
```

**Parameters:**
- `param1` (string): Description
- `param2` (number): Description

**Response:**
```json
{
  "status": "success",
  "data": {}
}
```

## Examples

### Example 1

```python
# Code example
def example():
    pass
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
"""
        self.apply_template(template, "documentation.md")

    def template_todo(self):
        """TODO list template"""
        template = """# TODO List

## 🎯 High Priority

- [ ] Important task 1
- [ ] Important task 2
- [ ] Important task 3

## 📋 Normal Priority

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

## 💡 Ideas / Future

- [ ] Idea 1
- [ ] Idea 2
- [ ] Idea 3

## ✅ Completed

- [x] Completed task 1
- [x] Completed task 2

---

**Last Updated:** [Date]
"""
        self.apply_template(template, "todo.md")

    def template_changelog(self):
        """Changelog template"""
        template = """# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New feature 1
- New feature 2

### Changed
- Changed behavior 1

### Fixed
- Bug fix 1

## [1.0.0] - 2024-01-01

### Added
- Initial release
- Core functionality
- Documentation

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

[Unreleased]: https://github.com/username/repo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/username/repo/releases/tag/v1.0.0
"""
        self.apply_template(template, "CHANGELOG.md")

    def restore_settings(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        edit_mode = self.settings.value("edit_mode", False, type=bool)
        if edit_mode:
            self.toggle_edit_mode(True)

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("edit_mode", self.edit_mode)

    def closeEvent(self, event: QCloseEvent):
        if not self.check_save_changes():
            event.ignore()
            return

        self.save_settings()
        logger.info(f"{__app_name__} closed")
        event.accept()

    def eventFilter(self, obj, event):
        """Event filter to handle image paste"""
        if obj == self.editor and event.type() == event.KeyPress:
            # Check for Ctrl+V (paste)
            if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
                if self.handle_image_paste():
                    return True  # Event handled, don't pass to editor
        return super().eventFilter(obj, event)

    def handle_image_paste(self):
        """Handle pasting images from clipboard"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()

        # Check if clipboard contains an image
        if mime_data.hasImage():
            image = clipboard.image()
            if not image.isNull():
                self.insert_image_from_clipboard(image)
                return True
        return False

    def insert_image_from_clipboard(self, image):
        """Insert image from clipboard into editor"""
        try:
            # Setup images directory
            if not self.current_file:
                QMessageBox.warning(
                    self, "No File Open",
                    "Please save the document first before pasting images."
                )
                return

            # Create images directory next to the markdown file
            file_dir = Path(self.current_file).parent
            self.images_dir = file_dir / "images"
            self.images_dir.mkdir(exist_ok=True)

            # Generate unique filename
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"pasted_image_{timestamp}.png"
            image_path = self.images_dir / image_filename

            # Save image
            image.save(str(image_path), "PNG")

            # Insert markdown image syntax
            relative_path = f"images/{image_filename}"
            markdown_syntax = f"![Image]({relative_path})"

            cursor = self.editor.textCursor()
            cursor.insertText(markdown_syntax)

            self.status_label.setText(f"Image pasted: {image_filename}")
            logger.info(f"Image pasted and saved: {image_path}")

        except Exception as e:
            logger.error(f"Error pasting image: {e}")
            QMessageBox.critical(self, "Error", f"Could not paste image:\n{str(e)}")

    def show_welcome_message(self):
        self.viewer.setHtml(f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f6f8fa;
        }}
        .welcome {{
            text-align: center;
            color: #586069;
        }}
        .welcome h1 {{ color: #24292e; margin-bottom: 20px; }}
        .welcome p {{ font-size: 16px; margin: 10px 0; }}
        .shortcut {{
            background-color: #ffffff;
            padding: 4px 8px;
            border-radius: 3px;
            border: 1px solid #d1d5da;
            font-family: monospace;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="welcome">
        <h1>{__app_name__}</h1>
        <p>Open a markdown (.md) or mermaid (.mmd) file</p>
        <p><span class="shortcut">Ctrl+O</span> - Open File</p>
        <p><span class="shortcut">Ctrl+E</span> - Toggle Edit Mode</p>
        <p><span class="shortcut">Ctrl+S</span> - Save</p>
        <p class="version" style="margin-top:30px;font-size:12px;color:#959da5;">Version {__version__}</p>
    </div>
</body>
</html>''')

    def show_help(self):
        self.viewer.setHtml(f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1, h2 {{ color: #24292e; }}
        .shortcut {{
            background-color: #f6f8fa;
            padding: 4px 8px;
            border-radius: 3px;
            border: 1px solid #d1d5da;
            font-family: monospace;
            font-size: 14px;
        }}
        ul {{ line-height: 2; }}
    </style>
</head>
<body>
    <h1>{__app_name__} Help</h1>
    <h2>Supported Formats</h2>
    <ul>
        <li><b>Markdown</b> (.md, .markdown) - Text formatting with GitHub style</li>
        <li><b>Mermaid</b> (.mmd, .mermaid) - Diagram and chart rendering</li>
    </ul>
    <h2>Features</h2>
    <ul>
        <li><b>Reader Font Selection</b> - Choose from 19 popular fonts (View → Reader Font)</li>
        <li><b>Live Preview</b> - Real-time rendering in edit mode</li>
        <li><b>Export Options</b> - HTML, PNG (diagrams), and PDF</li>
        <li><b>Recent Files</b> - Quick access to last 10 files</li>
    </ul>
    <h2>Keyboard Shortcuts</h2>
    <ul>
        <li><span class="shortcut">Ctrl+O</span> - Open file</li>
        <li><span class="shortcut">Ctrl+S</span> - Save</li>
        <li><span class="shortcut">Ctrl+E</span> - Toggle edit mode</li>
        <li><span class="shortcut">Ctrl+Shift+H</span> - Export HTML</li>
        <li><span class="shortcut">Ctrl+Shift+P</span> - Export PNG (Mermaid only)</li>
        <li><span class="shortcut">Ctrl+Shift+D</span> - Export PDF</li>
    </ul>
    <h2>Customization</h2>
    <ul>
        <li>Change reader font via View → Reader Font</li>
        <li>Toggle between viewer-only and split edit/preview modes</li>
        <li>All preferences are automatically saved</li>
    </ul>
</body>
</html>''')

    def show_cheatsheet(self):
        """Show Markdown cheat sheet"""
        cheatsheet_html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            padding: 30px;
            max-width: 1000px;
            margin: 0 auto;
            line-height: 1.6;
        }
        h1 { color: #24292e; border-bottom: 2px solid #eaecef; padding-bottom: 10px; }
        h2 { color: #24292e; margin-top: 30px; border-bottom: 1px solid #eaecef; padding-bottom: 8px; }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }
        th, td {
            border: 1px solid #dfe2e5;
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        code {
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 85%;
        }
        pre {
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
        }
        .example {
            color: #0366d6;
        }
    </style>
</head>
<body>
    <h1>📝 Markdown Cheat Sheet</h1>

    <h2>Headings</h2>
    <table>
        <tr><th>Syntax</th><th>Result</th></tr>
        <tr><td><code># Heading 1</code></td><td><strong>Heading 1</strong> (largest)</td></tr>
        <tr><td><code>## Heading 2</code></td><td><strong>Heading 2</strong></td></tr>
        <tr><td><code>### Heading 3</code></td><td><strong>Heading 3</strong></td></tr>
    </table>

    <h2>Text Formatting</h2>
    <table>
        <tr><th>Syntax</th><th>Result</th></tr>
        <tr><td><code>*italic* or _italic_</code></td><td><em>italic</em></td></tr>
        <tr><td><code>**bold** or __bold__</code></td><td><strong>bold</strong></td></tr>
        <tr><td><code>***bold italic***</code></td><td><strong><em>bold italic</em></strong></td></tr>
        <tr><td><code>~~strikethrough~~</code></td><td><del>strikethrough</del></td></tr>
        <tr><td><code>`inline code`</code></td><td><code>inline code</code></td></tr>
    </table>

    <h2>Lists</h2>
    <table>
        <tr><th>Syntax</th><th>Type</th></tr>
        <tr><td><pre>- Item 1
- Item 2
  - Nested item</pre></td><td>Unordered list</td></tr>
        <tr><td><pre>1. First item
2. Second item
3. Third item</pre></td><td>Ordered list</td></tr>
        <tr><td><pre>- [ ] Unchecked
- [x] Checked</pre></td><td>Task list</td></tr>
    </table>

    <h2>Links & Images</h2>
    <table>
        <tr><th>Syntax</th><th>Result</th></tr>
        <tr><td><code>[Link text](https://example.com)</code></td><td>Link</td></tr>
        <tr><td><code>[Link with title](https://example.com "Title")</code></td><td>Link with hover title</td></tr>
        <tr><td><code>![Alt text](image.jpg)</code></td><td>Image</td></tr>
    </table>

    <h2>Code Blocks</h2>
    <pre>```python
def hello():
    print("Hello, World!")
```</pre>

    <h2>Blockquotes</h2>
    <pre>> This is a quote
> It can span multiple lines</pre>

    <h2>Tables</h2>
    <pre>| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |</pre>

    <h2>Horizontal Rule</h2>
    <pre>---
or
***
or
___</pre>

    <h2>Inline HTML</h2>
    <p>You can use HTML tags: <code>&lt;br&gt;</code>, <code>&lt;kbd&gt;</code>, <code>&lt;sub&gt;</code>, <code>&lt;sup&gt;</code></p>

    <h2>Escaping Characters</h2>
    <p>Use backslash to escape: <code>\\*not italic\\*</code></p>

    <h2>Tips</h2>
    <ul>
        <li>💡 Leave blank lines between paragraphs</li>
        <li>💡 Use 2+ spaces at line end for line break</li>
        <li>💡 Indent code blocks with 4 spaces</li>
        <li>💡 Combine formatting: <code>**bold _and italic_**</code></li>
    </ul>
</body>
</html>'''
        self.viewer.setHtml(cheatsheet_html)
        self.status_label.setText("Showing Markdown cheat sheet")

    def setup_auto_save(self):
        """Setup auto-save timer"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_file)
        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)  # Convert to milliseconds

    def auto_save_file(self):
        """Auto-save current file to draft location"""
        if not self.current_file or not self.is_modified or not self.edit_mode:
            return

        try:
            draft_path = self.get_draft_path()
            content = self.editor.toPlainText()

            # Save to draft location
            with open(draft_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Save metadata
            metadata_path = draft_path.with_suffix('.meta')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(f"original_file={self.current_file}\n")
                f.write(f"file_type={self.file_type}\n")

            self.status_label.setText(f"Auto-saved at {QTime.currentTime().toString('HH:mm:ss')}")
            logger.info(f"Auto-saved draft: {draft_path}")
        except Exception as e:
            logger.error(f"Auto-save failed: {e}")

    def get_draft_path(self) -> Path:
        """Get draft file path for current file"""
        if self.current_file:
            filename = Path(self.current_file).name
            return self.draft_dir / f"{filename}.draft"
        return self.draft_dir / "untitled.draft"

    def check_draft_recovery(self):
        """Check for draft files and offer recovery"""
        drafts = list(self.draft_dir.glob("*.draft"))
        if not drafts:
            return

        # Find drafts with metadata
        recoverable = []
        for draft_file in drafts:
            metadata_file = draft_file.with_suffix('.meta')
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = dict(line.strip().split('=', 1) for line in f if '=' in line)
                    recoverable.append((draft_file, metadata))
                except:
                    pass

        if recoverable:
            reply = QMessageBox.question(
                self,
                "Draft Recovery",
                f"Found {len(recoverable)} auto-saved draft(s). Would you like to recover them?",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                self.show_draft_recovery_dialog(recoverable)

    def show_draft_recovery_dialog(self, recoverable):
        """Show dialog to select draft to recover"""
        if not recoverable:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Recover Drafts")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)

        label = QLabel("Select a draft to recover:")
        layout.addWidget(label)

        # Create list of drafts
        list_widget = QListWidget()

        for draft_file, metadata in recoverable:
            original = metadata.get('original_file', 'Unknown')
            item_text = f"{Path(original).name} (saved: {draft_file.stat().st_mtime})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, (draft_file, metadata))
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        # Buttons
        button_layout = QHBoxLayout()
        recover_btn = QPushButton("Recover")
        delete_btn = QPushButton("Delete Draft")
        cancel_btn = QPushButton("Cancel")

        def recover_draft():
            current = list_widget.currentItem()
            if current:
                draft_file, metadata = current.data(Qt.UserRole)
                original_file = metadata.get('original_file')

                # Read draft content
                with open(draft_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Load the file
                if original_file and Path(original_file).exists():
                    self.open_file(original_file)
                else:
                    self.current_file = None
                    self.file_type = metadata.get('file_type', 'markdown')

                # Set content
                self.editor.setPlainText(content)
                self.is_modified = True
                self.toggle_edit_mode(True)

                # Clean up draft
                draft_file.unlink()
                draft_file.with_suffix('.meta').unlink()

                dialog.accept()
                self.status_label.setText("Draft recovered successfully")

        def delete_draft():
            current = list_widget.currentItem()
            if current:
                draft_file, metadata = current.data(Qt.UserRole)
                draft_file.unlink()
                draft_file.with_suffix('.meta').unlink()
                list_widget.takeItem(list_widget.row(current))
                self.status_label.setText("Draft deleted")

                if list_widget.count() == 0:
                    dialog.accept()

        recover_btn.clicked.connect(recover_draft)
        delete_btn.clicked.connect(delete_draft)
        cancel_btn.clicked.connect(dialog.reject)

        button_layout.addWidget(recover_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        dialog.exec_()

    def toggle_auto_save(self):
        """Toggle auto-save feature"""
        self.auto_save_enabled = not self.auto_save_enabled
        self.settings.setValue("auto_save_enabled", self.auto_save_enabled)
        self.auto_save_action.setChecked(self.auto_save_enabled)

        if self.auto_save_enabled:
            self.auto_save_timer.start(self.auto_save_interval * 1000)
            self.status_label.setText(f"Auto-save enabled (every {self.auto_save_interval}s)")
        else:
            self.auto_save_timer.stop()
            self.status_label.setText("Auto-save disabled")

        logger.info(f"Auto-save {'enabled' if self.auto_save_enabled else 'disabled'}")

    def cleanup_draft(self):
        """Clean up draft file for current file"""
        try:
            draft_path = self.get_draft_path()
            if draft_path.exists():
                draft_path.unlink()
                logger.info(f"Cleaned up draft: {draft_path}")

            metadata_path = draft_path.with_suffix('.meta')
            if metadata_path.exists():
                metadata_path.unlink()
        except Exception as e:
            logger.error(f"Error cleaning up draft: {e}")

    def show_about(self):
        """Show professional About dialog"""
        dialog = QDialog(self)
        dialog.setObjectName("AboutDialog")
        dialog.setWindowTitle(f"About {__app_name__}")
        dialog.setModal(True)
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # App icon
        icon_pixmap = self.windowIcon().pixmap(64, 64)
        if not icon_pixmap.isNull():
            icon_label = QLabel()
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        # App title
        title_label = QLabel(f"<b>{__app_name__}</b>")
        title_label.setObjectName("AboutTitle")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        layout.addWidget(title_label)

        # Version
        version_label = QLabel(f"Version {__version__}")
        version_label.setObjectName("MetaLabel")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #666; font-size: 10pt;")
        layout.addWidget(version_label)

        layout.addSpacing(8)

        # Description
        desc_label = QLabel(
            "A powerful desktop application for viewing and editing<br>"
            "Markdown documents and Mermaid diagrams with extensive<br>"
            "customization options."
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addSpacing(12)

        # Developer info with links
        dev_label = QLabel(
            '<p style="text-align: center;">'
            'Developed by <b>Jilani Shaik</b><br>'
            '<a href="https://github.com/iammrj">github.com/iammrj</a><br>'
            '</p>'
        )
        dev_label.setTextFormat(Qt.RichText)
        dev_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        dev_label.setOpenExternalLinks(True)
        dev_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_label)

        layout.addSpacing(12)

        # License
        license_label = QLabel(
            '<p style="text-align: center; color: #888; font-size: 8pt;">'
            'Licensed under the MIT License<br>'
            'Copyright © 2026 Jilani Shaik'
            '</p>'
        )
        license_label.setTextFormat(Qt.RichText)
        license_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(license_label)

        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec_()


def main():
    # Suppress Qt warnings
    os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.webenginecontext.debug=false'

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)

    viewer = UnifiedViewer()

    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        viewer.open_file(sys.argv[1])

    viewer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
