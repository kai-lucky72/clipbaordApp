"""
Settings Dialog Module

This module implements the settings dialog for the clipboard manager.
"""
import sys
import os
import logging
import platform
import subprocess
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QSpinBox, QComboBox, QTabWidget,
    QWidget, QFormLayout, QMessageBox, QLineEdit
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QSettings, QSize

from clipboard_manager import ClipboardManager

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """
    Settings dialog for the clipboard manager application
    """
    def __init__(self, clipboard_manager):
        super().__init__()
        self.clipboard_manager = clipboard_manager
        self.setWindowTitle("Settings")
        self.setFixedSize(450, 400)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create tabs
        tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Startup options
        startup_group = QGroupBox("Startup Options")
        startup_layout = QVBoxLayout()
        
        self.autostart_checkbox = QCheckBox("Start with operating system")
        self.start_minimized_checkbox = QCheckBox("Start minimized to system tray")
        
        startup_layout.addWidget(self.autostart_checkbox)
        startup_layout.addWidget(self.start_minimized_checkbox)
        startup_group.setLayout(startup_layout)
        
        # Clipboard monitoring options
        monitoring_group = QGroupBox("Clipboard Monitoring")
        monitoring_layout = QVBoxLayout()
        
        self.track_images_checkbox = QCheckBox("Track images in clipboard")
        
        # Max history items
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Maximum history items:"))
        self.max_history_spinbox = QSpinBox()
        self.max_history_spinbox.setRange(10, 10000)
        self.max_history_spinbox.setSingleStep(10)
        history_layout.addWidget(self.max_history_spinbox)
        
        monitoring_layout.addWidget(self.track_images_checkbox)
        monitoring_layout.addLayout(history_layout)
        monitoring_group.setLayout(monitoring_layout)
        
        # Appearance options
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light")
        self.theme_combo.addItem("Dark")
        theme_layout.addWidget(self.theme_combo)
        
        appearance_layout.addLayout(theme_layout)
        appearance_group.setLayout(appearance_layout)
        
        # Add groups to general tab
        general_layout.addWidget(startup_group)
        general_layout.addWidget(monitoring_group)
        general_layout.addWidget(appearance_group)
        general_layout.addStretch()
        
        # Add tabs to widget
        tabs.addTab(general_tab, "General")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_settings)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        # Add widgets to main layout
        main_layout.addWidget(tabs)
        main_layout.addLayout(button_layout)
        
        # Set dialog layout
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load settings from QSettings"""
        settings = QSettings("ClipboardManager", "ClipboardManager")
        
        # Startup options
        self.autostart_checkbox.setChecked(settings.value("startup/autostart", False, type=bool))
        self.start_minimized_checkbox.setChecked(settings.value("startup/start_minimized", True, type=bool))
        
        # Monitoring options
        self.track_images_checkbox.setChecked(settings.value("monitoring/track_images", True, type=bool))
        self.max_history_spinbox.setValue(settings.value("monitoring/max_history_items", 1000, type=int))
        
        # Appearance options
        theme_index = self.theme_combo.findText(settings.value("appearance/theme", "Light"))
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
    
    def save_settings(self):
        """Save settings to QSettings"""
        settings = QSettings("ClipboardManager", "ClipboardManager")
        
        # Startup options
        settings.setValue("startup/autostart", self.autostart_checkbox.isChecked())
        settings.setValue("startup/start_minimized", self.start_minimized_checkbox.isChecked())
        
        # Monitoring options
        settings.setValue("monitoring/track_images", self.track_images_checkbox.isChecked())
        settings.setValue("monitoring/max_history_items", self.max_history_spinbox.value())
        
        # Appearance options
        settings.setValue("appearance/theme", self.theme_combo.currentText())
        
        # Apply settings
        self.clipboard_manager.set_track_images(self.track_images_checkbox.isChecked())
        
        # Configure autostart
        self.configure_autostart(self.autostart_checkbox.isChecked())
        
        # Accept dialog
        self.accept()
    
    def reset_settings(self):
        """Reset settings to defaults"""
        # Startup options
        self.autostart_checkbox.setChecked(False)
        self.start_minimized_checkbox.setChecked(True)
        
        # Monitoring options
        self.track_images_checkbox.setChecked(True)
        self.max_history_spinbox.setValue(1000)
        
        # Appearance options
        self.theme_combo.setCurrentIndex(0)  # Light theme
        
        # Show confirmation
        QMessageBox.information(self, "Settings Reset", "Settings have been reset to defaults.")
    
    def configure_autostart(self, enable):
        """Configure application to start with OS based on platform"""
        system = platform.system()
        
        try:
            if system == 'Windows':
                self._configure_autostart_windows(enable)
            elif system == 'Darwin':  # macOS
                self._configure_autostart_mac(enable)
            elif system == 'Linux':
                self._configure_autostart_linux(enable)
            else:
                logger.warning(f"Autostart configuration not supported on {system}")
        except Exception as e:
            logger.error(f"Failed to configure autostart: {e}")
            QMessageBox.warning(
                self, "Autostart Configuration",
                f"Failed to configure autostart: {str(e)}"
            )
    
    def _configure_autostart_windows(self, enable):
        """Configure autostart on Windows"""
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "ClipboardManager"
        
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                if enable:
                    # Get executable path
                    exe_path = sys.executable
                    if not exe_path.endswith('pythonw.exe'):
                        # Use pythonw.exe to run without console window
                        exe_path = exe_path.replace('python.exe', 'pythonw.exe')
                    
                    script_path = os.path.abspath(sys.argv[0])
                    command = f'"{exe_path}" "{script_path}"'
                    
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
                else:
                    try:
                        winreg.DeleteValue(key, app_name)
                    except FileNotFoundError:
                        pass  # Value doesn't exist, which is fine
        except Exception as e:
            logger.error(f"Windows autostart configuration error: {e}")
            raise
    
    def _configure_autostart_mac(self, enable):
        """Configure autostart on macOS"""
        # On macOS, we use a launch agent plist file
        launch_agent_dir = os.path.expanduser("~/Library/LaunchAgents")
        plist_path = os.path.join(launch_agent_dir, "com.clipboardmanager.app.plist")
        
        if enable:
            # Create LaunchAgents directory if it doesn't exist
            os.makedirs(launch_agent_dir, exist_ok=True)
            
            # Get executable path
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            
            # Create plist file content
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clipboardmanager.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
            # Write plist file
            with open(plist_path, 'w') as f:
                f.write(plist_content)
            
            # Load the launch agent
            subprocess.run(["launchctl", "load", plist_path], check=True)
            
        else:
            # Unload and remove the launch agent if it exists
            if os.path.exists(plist_path):
                try:
                    subprocess.run(["launchctl", "unload", plist_path], check=True)
                except subprocess.CalledProcessError:
                    pass  # Might not be loaded
                
                os.remove(plist_path)
    
    def _configure_autostart_linux(self, enable):
        """Configure autostart on Linux"""
        # On Linux, we use a .desktop file in the autostart directory
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_path = os.path.join(autostart_dir, "clipboardmanager.desktop")
        
        if enable:
            # Create autostart directory if it doesn't exist
            os.makedirs(autostart_dir, exist_ok=True)
            
            # Get executable path
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            
            # Create desktop file content
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=Clipboard Manager
Exec={exe_path} {script_path}
Terminal=false
X-GNOME-Autostart-enabled=true
"""
            
            # Write desktop file
            with open(desktop_path, 'w') as f:
                f.write(desktop_content)
            
            # Make it executable
            os.chmod(desktop_path, 0o755)
            
        else:
            # Remove the desktop file if it exists
            if os.path.exists(desktop_path):
                os.remove(desktop_path)
