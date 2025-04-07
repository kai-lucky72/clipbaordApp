"""
System Tray Module

This module implements the system tray icon and its menu.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QDialog,
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QWidget,
    QMessageBox
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QSize, Qt, pyqtSignal

from ui.settings_dialog import SettingsDialog
from utils import resource_path

logger = logging.getLogger(__name__)

class SystemTrayIcon(QSystemTrayIcon):
    """
    System tray icon for clipboard manager application
    """
    def __init__(self, clipboard_manager, history_viewer):
        super().__init__()
        self.clipboard_manager = clipboard_manager
        self.history_viewer = history_viewer
        self.is_paused = False
        
        # Set icon
        self.setIcon(QIcon(resource_path("assets/clipboard_icon.png")))
        self.setToolTip("Clipboard Manager")
        
        # Create menu
        self.create_menu()
        
        # Connect signals
        self.activated.connect(self.on_tray_activated)
    
    def create_menu(self):
        """Create system tray icon menu"""
        menu = QMenu()
        
        # Show history action
        show_history_action = QAction("Show History", menu)
        show_history_action.triggered.connect(self.show_history_viewer)
        menu.addAction(show_history_action)
        
        # Pause/resume monitoring
        self.pause_action = QAction("Pause Monitoring", menu)
        self.pause_action.setCheckable(True)
        self.pause_action.toggled.connect(self.toggle_monitoring)
        menu.addAction(self.pause_action)
        
        menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        # About action
        about_action = QAction("About", menu)
        about_action.triggered.connect(self.show_about)
        menu.addAction(about_action)
        
        menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_application)
        menu.addAction(exit_action)
        
        # Set the menu
        self.setContextMenu(menu)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_history_viewer()
    
    def show_history_viewer(self):
        """Show clipboard history viewer"""
        self.history_viewer.show()
        self.history_viewer.activateWindow()
        self.history_viewer.raise_()
    
    def toggle_monitoring(self, paused):
        """Toggle clipboard monitoring"""
        self.is_paused = paused
        
        if paused:
            self.clipboard_manager.stop_monitoring()
            self.pause_action.setText("Resume Monitoring")
            self.showMessage(
                "Clipboard Manager", 
                "Clipboard monitoring paused",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.clipboard_manager.start_monitoring()
            self.pause_action.setText("Pause Monitoring")
            self.showMessage(
                "Clipboard Manager", 
                "Clipboard monitoring resumed",
                QSystemTrayIcon.Information,
                2000
            )
    
    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = SettingsDialog(self.clipboard_manager)
        settings_dialog.exec_()
    
    def show_about(self):
        """Show about dialog"""
        about_dialog = QDialog()
        about_dialog.setWindowTitle("About Clipboard Manager")
        about_dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # Application title and version
        title_label = QLabel("Clipboard Manager")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        version_label = QLabel("Version 1.0")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Description
        description_label = QLabel(
            "A cross-platform Python clipboard manager designed to enhance user "
            "productivity with advanced clipboard handling and intuitive interface."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        
        # OK button
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(about_dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        
        # Add widgets to layout
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addSpacing(10)
        layout.addWidget(description_label)
        layout.addStretch()
        layout.addLayout(button_layout)
        
        about_dialog.setLayout(layout)
        about_dialog.exec_()
    
    def exit_application(self):
        """Exit the application"""
        # Confirm exit
        reply = QMessageBox.question(
            None, "Exit Confirmation",
            "Are you sure you want to exit Clipboard Manager?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop monitoring
            self.clipboard_manager.stop_monitoring()
            # Quit application
            QApplication.quit()
