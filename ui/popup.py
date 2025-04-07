"""
Clipboard Popup Module

This module implements the quick paste popup that appears when Ctrl+V is pressed.
"""
import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame,
    QScrollArea, QSizePolicy, QToolButton
)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QFont, QColor, QKeySequence, QCursor
from PyQt5.QtCore import (
    Qt, QSize, QEvent, QObject, pyqtSignal, QPoint, QRect, QTimer
)

from database import DatabaseManager
from clipboard_manager import ClipboardManager
from utils import resource_path, limit_text_length, format_timestamp

logger = logging.getLogger(__name__)

class GlobalEventFilter(QObject):
    """
    Global event filter to detect keyboard shortcuts
    """
    def __init__(self, parent, popup):
        super().__init__(parent)
        self.popup = popup
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            # Check for Ctrl+V
            if event.key() == Qt.Key_V and event.modifiers() == Qt.ControlModifier:
                self.popup.show_popup()
                return True
        return False

class ClipboardPopup(QWidget):
    """
    Quick paste popup showing the last 5 clipboard items
    """
    item_selected = pyqtSignal(dict)
    
    def __init__(self, db_manager, clipboard_manager):
        super().__init__()
        self.db_manager = db_manager
        self.clipboard_manager = clipboard_manager
        self.clipboard_items = []
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self.hide)
        
        # Install global event filter to capture Ctrl+V
        self.event_filter = GlobalEventFilter(QApplication.instance(), self)
        QApplication.instance().installEventFilter(self.event_filter)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Quick Paste")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup | Qt.WindowStaysOnTopHint)
        
        # Set size and style
        self.setFixedWidth(400)
        self.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QLabel {
                padding: 5px;
                font-weight: bold;
            }
            QPushButton {
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Header with title and close button
        header_layout = QHBoxLayout()
        title_label = QLabel("Recent Clipboard Items")
        title_label.setStyleSheet("font-size: 14px;")
        
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.clicked.connect(self.hide)
        close_button.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_button)
        
        # Clipboard items list
        self.items_widget = QWidget()
        self.items_layout = QVBoxLayout(self.items_widget)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(2)
        
        # View more button
        self.view_more_button = QPushButton("View History")
        self.view_more_button.clicked.connect(self.on_view_more)
        
        # Add widgets to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.items_widget)
        main_layout.addWidget(self.view_more_button)
        
        self.setLayout(main_layout)
        
    def show_popup(self):
        """Show the popup with the latest clipboard items"""
        # Load recent items from database
        self.clipboard_items = self.db_manager.get_recent_items(limit=5)
        
        # Clear previous items
        self.clear_items()
        
        # Add items to the UI
        for item in self.clipboard_items:
            self.add_item_widget(item)
        
        # Adjust height based on number of items
        height = 80 + min(len(self.clipboard_items), 5) * 60
        self.setFixedHeight(height)
        
        # Position the popup in the center of the screen
        screen_geometry = QApplication.desktop().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        # Show the popup
        self.show()
        self.activateWindow()
        
        # Start auto-hide timer (10 seconds)
        self.auto_hide_timer.start(10000)
    
    def clear_items(self):
        """Clear all items from the layout"""
        while self.items_layout.count():
            item = self.items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_item_widget(self, item):
        """Add a clipboard item to the UI"""
        item_frame = QFrame()
        item_frame.setFrameShape(QFrame.StyledPanel)
        item_frame.setStyleSheet("""
            QFrame {
                background-color: #f9f9f9;
                border-radius: 3px;
                padding: 5px;
            }
            QFrame:hover {
                background-color: #f0f0f0;
            }
        """)
        
        item_layout = QHBoxLayout(item_frame)
        item_layout.setContentsMargins(5, 5, 5, 5)
        
        # Content preview
        content_label = QLabel()
        
        if item['type'] == 'text':
            # For text, show a preview
            preview_text = item['content']
            if len(preview_text) > 50:
                preview_text = preview_text[:47] + "..."
            content_label.setText(preview_text)
        else:
            # For image, show a small preview
            image = QImage()
            image.loadFromData(item['content'])
            pixmap = QPixmap.fromImage(image).scaled(
                40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            content_label.setPixmap(pixmap)
        
        content_label.setWordWrap(True)
        
        # Delete button
        delete_button = QPushButton("×")
        delete_button.setFixedSize(20, 20)
        delete_button.setToolTip("Delete")
        delete_button.clicked.connect(lambda _, id=item['id']: self.on_delete_item(id))
        
        # Add widgets to layout
        item_layout.addWidget(content_label, 1)
        item_layout.addWidget(delete_button)
        
        # Make the frame clickable to select this item
        item_frame.mousePressEvent = lambda _, item=item: self.on_item_selected(item)
        
        # Add to the main layout
        self.items_layout.addWidget(item_frame)
    
    def on_item_selected(self, item):
        """Handle item selection"""
        # Set clipboard content to the selected item
        self.clipboard_manager.set_clipboard_content(item)
        self.item_selected.emit(item)
        
        # Hide the popup
        self.hide()
    
    def on_delete_item(self, item_id):
        """Handle item deletion"""
        # Delete from database
        self.db_manager.delete_item(item_id)
        
        # Refresh the popup
        self.show_popup()
    
    def on_view_more(self):
        """Open the full history viewer"""
        from ui.history_viewer import HistoryViewer
        
        # Hide the popup
        self.hide()
        
        # Signal to open history viewer
        QApplication.instance().history_viewer.show()
        QApplication.instance().history_viewer.activateWindow()
