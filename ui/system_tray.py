"""
System Tray Module

This module implements the system tray icon and its menu.
"""
import logging
import sys
from PyQt5.QtWidgets import (
    QSystemTrayIcon, QMenu, QAction, QMessageBox, QApplication
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

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
        
        # Set icon
        self.setIcon(QIcon(resource_path("assets/app_icon.svg")))
        self.setToolTip("Advanced Clipboard Manager")
        
        # Create menu
        self.create_menu()
        
        # Connect signals
        self.activated.connect(self.on_tray_activated)
    
    def create_menu(self):
        """Create system tray icon menu"""
        # Create menu
        menu = QMenu()
        
        # Add actions
        show_history_action = QAction("Show Clipboard History", self)
        show_history_action.triggered.connect(self.show_history_viewer)
        
        toggle_monitor_action = QAction("Pause Clipboard Monitoring", self)
        toggle_monitor_action.setCheckable(True)
        toggle_monitor_action.toggled.connect(self.toggle_monitoring)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_application)
        
        # Add actions to menu
        menu.addAction(show_history_action)
        menu.addSeparator()
        menu.addAction(toggle_monitor_action)
        menu.addSeparator()
        menu.addAction(settings_action)
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        
        # Set as tray icon menu
        self.setContextMenu(menu)
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_history_viewer()
    
    def show_history_viewer(self):
        """Show clipboard history viewer"""
        self.history_viewer.show()
        self.history_viewer.activateWindow()
    
    def toggle_monitoring(self, paused):
        """Toggle clipboard monitoring"""
        if paused:
            self.clipboard_manager.stop_monitoring()
            self.showMessage(
                "Clipboard Manager", 
                "Clipboard monitoring paused",
                QSystemTrayIcon.Information, 2000
            )
            # Update menu item
            self.contextMenu().actions()[2].setText("Resume Clipboard Monitoring")
        else:
            self.clipboard_manager.start_monitoring()
            self.showMessage(
                "Clipboard Manager", 
                "Clipboard monitoring resumed",
                QSystemTrayIcon.Information, 2000
            )
            # Update menu item
            self.contextMenu().actions()[2].setText("Pause Clipboard Monitoring")
    
    def show_settings(self):
        """Show settings dialog"""
        settings_dialog = SettingsDialog(self.clipboard_manager)
        settings_dialog.exec_()
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            None, 
            "About Advanced Clipboard Manager",
            "<h2>Advanced Clipboard Manager</h2>"
            "<p>A cross-platform clipboard history manager</p>"
            "<p>Version 1.0.0</p>"
            "<p>&copy; 2023 ClipboardTools</p>"
        )
    
    def exit_application(self):
        """Exit the application"""
        # Ask for confirmation
        reply = QMessageBox.question(
            None, "Exit Confirmation",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Stop clipboard monitoring before exit
            self.clipboard_manager.stop_monitoring()
            # Exit application
            QApplication.instance().quit()
