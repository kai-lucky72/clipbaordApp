"""
History Viewer Module

This module implements the full clipboard history viewer.
"""
import sys
import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QToolBar, QAction, QSplitter, QTextEdit, QFileDialog,
    QCheckBox, QMenu, QMessageBox, QSizePolicy, QAbstractItemView,
    QTabWidget
)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QFont, QColor
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint, QByteArray, QBuffer

from database import DatabaseManager
from clipboard_manager import ClipboardManager
from models import ClipItemType
from utils import format_timestamp, limit_text_length, resource_path

logger = logging.getLogger(__name__)

class HistoryViewer(QMainWindow):
    """
    Full clipboard history viewer window
    """
    def __init__(self, db_manager, clipboard_manager):
        super().__init__()
        self.db_manager = db_manager
        self.clipboard_manager = clipboard_manager
        self.clipboard_items = []
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Clipboard History")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Search and filter bar
        search_layout = QHBoxLayout()
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clipboard history...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        # Filter dropdown
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Items", None)
        self.filter_combo.addItem("Text Only", "text")
        self.filter_combo.addItem("Images Only", "image")
        self.filter_combo.addItem("Favorites", "favorites")
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        
        # Refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_history)
        
        # Clear history button
        clear_button = QPushButton("Clear History")
        clear_button.clicked.connect(self.on_clear_history)
        
        # Add widgets to search layout
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.filter_combo)
        search_layout.addWidget(refresh_button)
        search_layout.addWidget(clear_button)
        
        # Clipboard history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["Content", "Type", "Timestamp", "Actions"])
        self.history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.cellDoubleClicked.connect(self.on_item_double_clicked)
        self.history_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Preview panel
        self.preview_panel = QWidget()
        preview_layout = QVBoxLayout(self.preview_panel)
        
        self.preview_label = QLabel("Select an item to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setVisible(False)
        self.preview_image = QLabel()
        self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setVisible(False)
        
        preview_layout.addWidget(self.preview_label)
        preview_layout.addWidget(self.preview_text)
        preview_layout.addWidget(self.preview_image)
        
        # Create splitter for table and preview
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.history_table)
        splitter.addWidget(self.preview_panel)
        splitter.setSizes([600, 200])
        
        # Add widgets to main layout
        main_layout.addLayout(search_layout)
        main_layout.addWidget(splitter)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Connect signals
        self.history_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Initial load of clipboard history
        self.refresh_history()
    
    def refresh_history(self):
        """Load and display clipboard history"""
        search_text = self.search_input.text()
        filter_idx = self.filter_combo.currentIndex()
        filter_type = self.filter_combo.itemData(filter_idx)
        favorites_only = (filter_type == "favorites")
        
        # Get type filter
        type_filter = None
        if filter_type in ["text", "image"]:
            type_filter = filter_type
        
        # Load items from database
        self.clipboard_items = self.db_manager.get_all_items(
            search_text=search_text,
            filter_type=type_filter,
            favorites_only=favorites_only
        )
        
        # Update the table
        self.update_history_table()
    
    def update_history_table(self):
        """Update the history table with loaded items"""
        # Clear table
        self.history_table.setRowCount(0)
        
        # Add items to table
        for row, item in enumerate(self.clipboard_items):
            self.history_table.insertRow(row)
            
            # Content preview cell
            content_preview = ""
            if item['type'] == 'text':
                content_preview = item['content']
                if len(content_preview) > 50:
                    content_preview = content_preview[:47] + "..."
            else:
                content_preview = "[Image]"
            
            content_item = QTableWidgetItem(content_preview)
            self.history_table.setItem(row, 0, content_item)
            
            # Type cell
            type_item = QTableWidgetItem(item['type'].capitalize())
            self.history_table.setItem(row, 1, type_item)
            
            # Timestamp cell
            timestamp_str = item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            timestamp_item = QTableWidgetItem(timestamp_str)
            self.history_table.setItem(row, 2, timestamp_item)
            
            # Actions cell - using cell widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(2)
            
            # Copy button
            copy_button = QPushButton("Copy")
            copy_button.setToolTip("Copy to clipboard")
            copy_button.clicked.connect(lambda _, idx=row: self.on_copy_item(idx))
            
            # Favorite checkbox
            favorite_checkbox = QCheckBox()
            favorite_checkbox.setToolTip("Mark as favorite")
            favorite_checkbox.setChecked(item['favorite'])
            favorite_checkbox.stateChanged.connect(
                lambda state, idx=row: self.on_toggle_favorite(idx, state)
            )
            
            # Delete button
            delete_button = QPushButton("Delete")
            delete_button.setToolTip("Delete item")
            delete_button.clicked.connect(lambda _, idx=row: self.on_delete_item(idx))
            
            # Add buttons to layout
            actions_layout.addWidget(copy_button)
            actions_layout.addWidget(favorite_checkbox)
            actions_layout.addWidget(delete_button)
            
            # Set the actions widget in the cell
            self.history_table.setCellWidget(row, 3, actions_widget)
        
        # Clear preview if no rows
        if self.history_table.rowCount() == 0:
            self.clear_preview()
    
    def on_search_text_changed(self, text):
        """Handle search text changes"""
        self.refresh_history()
    
    def on_filter_changed(self, index):
        """Handle filter changes"""
        self.refresh_history()
    
    def on_selection_changed(self):
        """Handle selection changes in the table"""
        selected_rows = self.history_table.selectedIndexes()
        if not selected_rows:
            self.clear_preview()
            return
        
        # Get the selected row
        row = selected_rows[0].row()
        if row >= len(self.clipboard_items):
            self.clear_preview()
            return
        
        # Get the selected item
        item = self.clipboard_items[row]
        
        # Update preview
        self.update_preview(item)
    
    def update_preview(self, item):
        """Update the preview panel with selected item"""
        # Hide all preview widgets
        self.preview_label.setVisible(False)
        self.preview_text.setVisible(False)
        self.preview_image.setVisible(False)
        
        if item['type'] == 'text':
            # Show text preview
            self.preview_text.setPlainText(item['content'])
            self.preview_text.setVisible(True)
        else:
            # Show image preview
            image = QImage()
            image.loadFromData(item['content'])
            pixmap = QPixmap.fromImage(image)
            
            # Scale image if needed
            preview_width = self.preview_panel.width() - 20
            preview_height = self.preview_panel.height() - 20
            if pixmap.width() > preview_width or pixmap.height() > preview_height:
                pixmap = pixmap.scaled(
                    preview_width, preview_height, 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            
            self.preview_image.setPixmap(pixmap)
            self.preview_image.setVisible(True)
    
    def clear_preview(self):
        """Clear the preview panel"""
        self.preview_label.setVisible(True)
        self.preview_text.setVisible(False)
        self.preview_text.clear()
        self.preview_image.setVisible(False)
        self.preview_image.clear()
    
    def on_copy_item(self, row):
        """Copy the selected item to clipboard"""
        if row < 0 or row >= len(self.clipboard_items):
            return
        
        item = self.clipboard_items[row]
        self.clipboard_manager.set_clipboard_content(item)
        
        # Show a brief status message
        self.statusBar().showMessage("Copied to clipboard", 2000)
    
    def on_delete_item(self, row):
        """Delete the selected item"""
        if row < 0 or row >= len(self.clipboard_items):
            return
        
        item = self.clipboard_items[row]
        if self.db_manager.delete_item(item['id']):
            # Remove from the model
            self.clipboard_items.pop(row)
            # Remove from the table
            self.history_table.removeRow(row)
            # Show a brief status message
            self.statusBar().showMessage("Item deleted", 2000)
    
    def on_toggle_favorite(self, row, state):
        """Toggle favorite status for an item"""
        if row < 0 or row >= len(self.clipboard_items):
            return
        
        item = self.clipboard_items[row]
        new_state = self.db_manager.toggle_favorite(item['id'])
        
        if new_state is not None:
            # Update the model
            item['favorite'] = new_state
            # Show a brief status message
            status = "added to" if new_state else "removed from"
            self.statusBar().showMessage(f"Item {status} favorites", 2000)
    
    def on_item_double_clicked(self, row, column):
        """Handle double-click on an item"""
        if row < 0 or row >= len(self.clipboard_items):
            return
        
        # Copy to clipboard on double-click
        self.on_copy_item(row)
    
    def show_context_menu(self, position):
        """Show context menu for history table"""
        selected_rows = self.history_table.selectedIndexes()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if row < 0 or row >= len(self.clipboard_items):
            return
        
        item = self.clipboard_items[row]
        
        # Create context menu
        context_menu = QMenu(self)
        
        # Add actions
        copy_action = QAction("Copy to Clipboard", self)
        copy_action.triggered.connect(lambda: self.on_copy_item(row))
        
        favorite_action = QAction(
            "Remove from Favorites" if item['favorite'] else "Add to Favorites", 
            self
        )
        favorite_action.triggered.connect(
            lambda: self.on_toggle_favorite(row, not item['favorite'])
        )
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.on_delete_item(row))
        
        # Image-specific actions
        if item['type'] == 'image':
            save_action = QAction("Save Image As...", self)
            save_action.triggered.connect(lambda: self.save_image(item))
            context_menu.addAction(save_action)
        
        # Add actions to menu
        context_menu.addAction(copy_action)
        context_menu.addAction(favorite_action)
        context_menu.addSeparator()
        context_menu.addAction(delete_action)
        
        # Show context menu
        context_menu.exec_(self.history_table.mapToGlobal(position))
    
    def save_image(self, item):
        """Save image to file"""
        if item['type'] != 'image':
            return
        
        # Ask for save location
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Save the image
        try:
            image = QImage()
            image.loadFromData(item['content'])
            image.save(file_path)
            self.statusBar().showMessage(f"Image saved to {file_path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save image: {str(e)}")
            logger.error(f"Failed to save image: {e}")
    
    def on_clear_history(self):
        """Clear clipboard history"""
        # Confirm before clearing
        reply = QMessageBox.question(
            self, "Clear History",
            "Do you want to clear clipboard history?\nFavorite items can be preserved.",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        keep_favorites = (reply == QMessageBox.Yes)
        
        # Clear history
        count = self.db_manager.clear_history(keep_favorites=keep_favorites)
        
        # Refresh display
        self.refresh_history()
        
        # Show confirmation
        self.statusBar().showMessage(f"Cleared {count} items from history", 3000)
