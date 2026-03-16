#!/usr/bin/env python3
"""
Markdown & Mermaid Viewer
Main entry point for the application
"""

import sys
import os

# Suppress Qt warnings
os.environ['QT_LOGGING_RULES'] = '*.debug=false;qt.webenginecontext.debug=false'

from PyQt5.QtWidgets import QApplication
from mdviewer import UnifiedViewer, __app_name__, __version__


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)

    viewer = UnifiedViewer()

    # Open file from command line if provided
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        viewer.open_file(sys.argv[1])

    viewer.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
