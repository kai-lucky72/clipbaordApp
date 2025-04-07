"""
Settings Dialog Module

This module implements the settings dialog for the clipboard manager.
"""
import logging
import os
import sys
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QLabel, 
    QSpinBox, QComboBox, QPushButton, QGroupBox, QFormLayout,
    QLineEdit, QTabWidget, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QSettings

logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """
    Settings dialog for the clipboard manager application
    """
    def __init__(self, clipboard_manager):
        super().__init__()
        self.clipboard_manager = clipboard_manager
        self.settings = QSettings()
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Initialize the UI components"""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Tabs
        tabs = QTabWidget()
        
        # General tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Clipboard group
        clipboard_group = QGroupBox("Clipboard Settings")
        clipboard_layout = QVBoxLayout(clipboard_group)
        
        # Track images checkbox
        self.track_images_cb = QCheckBox("Track images in clipboard")
        self.track_images_cb.setChecked(True)
        
        # Maximum history size
        history_layout = QHBoxLayout()
        history_layout.addWidget(QLabel("Maximum history items:"))
        
        self.max_history_spin = QSpinBox()
        self.max_history_spin.setMinimum(10)
        self.max_history_spin.setMaximum(10000)
        self.max_history_spin.setValue(1000)
        history_layout.addWidget(self.max_history_spin)
        history_layout.addStretch()
        
        # Add to clipboard group
        clipboard_layout.addWidget(self.track_images_cb)
        clipboard_layout.addLayout(history_layout)
        
        # Startup group
        startup_group = QGroupBox("Startup Settings")
        startup_layout = QVBoxLayout(startup_group)
        
        # Start with OS checkbox
        self.start_with_os_cb = QCheckBox("Start with operating system")
        
        # Start minimized checkbox
        self.start_minimized_cb = QCheckBox("Start minimized to tray")
        self.start_minimized_cb.setChecked(True)
        
        # Add to startup group
        startup_layout.addWidget(self.start_with_os_cb)
        startup_layout.addWidget(self.start_minimized_cb)
        
        # Appearance group
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        
        # Theme selector
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Light")
        self.theme_combo.addItem("Dark")
        appearance_layout.addRow("Theme:", self.theme_combo)
        
        # Add groups to general tab
        general_layout.addWidget(clipboard_group)
        general_layout.addWidget(startup_group)
        general_layout.addWidget(appearance_group)
        general_layout.addStretch()
        
        # Advanced tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)
        
        # Privacy group
        privacy_group = QGroupBox("Privacy")
        privacy_layout = QVBoxLayout(privacy_group)
        
        # Encryption checkbox
        self.encryption_cb = QCheckBox("Enable encryption for stored clipboard data")
        privacy_layout.addWidget(self.encryption_cb)
        
        # Add privacy group to advanced tab
        advanced_layout.addWidget(privacy_group)
        advanced_layout.addStretch()
        
        # Add tabs
        tabs.addTab(general_tab, "General")
        tabs.addTab(advanced_tab, "Advanced")
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Reset to defaults button
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_settings)
        
        # OK and Cancel buttons
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(reset_button)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        # Add widgets to main layout
        main_layout.addWidget(tabs)
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def load_settings(self):
        """Load settings from QSettings"""
        # Clipboard settings
        self.track_images_cb.setChecked(
            self.settings.value("clipboard/track_images", True, type=bool)
        )
        self.max_history_spin.setValue(
            self.settings.value("clipboard/max_history", 1000, type=int)
        )
        
        # Startup settings
        self.start_with_os_cb.setChecked(
            self.settings.value("startup/start_with_os", False, type=bool)
        )
        self.start_minimized_cb.setChecked(
            self.settings.value("startup/start_minimized", True, type=bool)
        )
        
        # Appearance settings
        theme = self.settings.value("appearance/theme", "Light")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        # Advanced settings
        self.encryption_cb.setChecked(
            self.settings.value("privacy/enable_encryption", False, type=bool)
        )
    
    def save_settings(self):
        """Save settings to QSettings"""
        # Clipboard settings
        self.settings.setValue("clipboard/track_images", self.track_images_cb.isChecked())
        self.settings.setValue("clipboard/max_history", self.max_history_spin.value())
        
        # Set track_images in the clipboard manager
        self.clipboard_manager.set_track_images(self.track_images_cb.isChecked())
        
        # Startup settings
        self.settings.setValue("startup/start_with_os", self.start_with_os_cb.isChecked())
        self.settings.setValue("startup/start_minimized", self.start_minimized_cb.isChecked())
        
        # Configure autostart based on OS
        self.configure_autostart(self.start_with_os_cb.isChecked())
        
        # Appearance settings
        self.settings.setValue("appearance/theme", self.theme_combo.currentText())
        
        # Advanced settings
        self.settings.setValue("privacy/enable_encryption", self.encryption_cb.isChecked())
        
        # Sync settings
        self.settings.sync()
        
        # Close dialog
        self.accept()
    
    def reset_settings(self):
        """Reset settings to defaults"""
        # Reset clipboard settings
        self.track_images_cb.setChecked(True)
        self.max_history_spin.setValue(1000)
        
        # Reset startup settings
        self.start_with_os_cb.setChecked(False)
        self.start_minimized_cb.setChecked(True)
        
        # Reset appearance settings
        self.theme_combo.setCurrentIndex(0)  # Light theme
        
        # Reset advanced settings
        self.encryption_cb.setChecked(False)
        
        # Show confirmation message
        QMessageBox.information(self, "Reset Settings", "Settings have been reset to defaults.")
    
    def configure_autostart(self, enable):
        """Configure application to start with OS based on platform"""
        if sys.platform == 'win32':
            self._configure_autostart_windows(enable)
        elif sys.platform == 'darwin':
            self._configure_autostart_mac(enable)
        elif sys.platform.startswith('linux'):
            self._configure_autostart_linux(enable)
        else:
            logger.warning(f"Autostart not supported on platform: {sys.platform}")
    
    def _configure_autostart_windows(self, enable):
        """Configure autostart on Windows"""
        try:
            import winreg
            
            # Get executable path
            exe_path = sys.executable
            if os.path.basename(exe_path).lower() == 'python.exe':
                # Running from source, use script path
                exe_path = f'"{exe_path}" "{os.path.abspath(sys.argv[0])}"'
            
            # Registry key
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "AdvancedClipboardManager"
            
            # Open registry key
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, 
                winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
            ) as key:
                if enable:
                    # Add to startup
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
                    logger.info(f"Added to Windows startup: {exe_path}")
                else:
                    # Remove from startup
                    try:
                        winreg.DeleteValue(key, app_name)
                        logger.info("Removed from Windows startup")
                    except FileNotFoundError:
                        # Key didn't exist, which is fine
                        pass
        except Exception as e:
            logger.error(f"Failed to configure Windows autostart: {e}")
    
    def _configure_autostart_mac(self, enable):
        """Configure autostart on macOS"""
        try:
            # Path to user's LaunchAgents directory
            launch_agents_dir = os.path.expanduser("~/Library/LaunchAgents")
            os.makedirs(launch_agents_dir, exist_ok=True)
            
            # Plist file path
            plist_path = os.path.join(launch_agents_dir, "com.clipboardtools.clipboardmanager.plist")
            
            if enable:
                # Get executable path
                exe_path = sys.executable
                if os.path.basename(exe_path) == 'python':
                    # Running from source, use script path
                    exe_path = f'{exe_path} {os.path.abspath(sys.argv[0])}'
                
                # Create plist content
                plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.clipboardtools.clipboardmanager</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
                
                # Write plist file
                with open(plist_path, 'w') as f:
                    f.write(plist_content)
                
                logger.info(f"Added to macOS startup: {plist_path}")
            else:
                # Remove plist file if it exists
                if os.path.exists(plist_path):
                    os.remove(plist_path)
                    logger.info(f"Removed from macOS startup: {plist_path}")
        except Exception as e:
            logger.error(f"Failed to configure macOS autostart: {e}")
    
    def _configure_autostart_linux(self, enable):
        """Configure autostart on Linux"""
        try:
            # Path to user's autostart directory
            autostart_dir = os.path.expanduser("~/.config/autostart")
            os.makedirs(autostart_dir, exist_ok=True)
            
            # Desktop file path
            desktop_path = os.path.join(autostart_dir, "clipboardmanager.desktop")
            
            if enable:
                # Get executable path
                exe_path = sys.executable
                if os.path.basename(exe_path) == 'python':
                    # Running from source, use script path
                    exe_path = f'{exe_path} {os.path.abspath(sys.argv[0])}'
                
                # Create desktop file content
                desktop_content = f'''[Desktop Entry]
Type=Application
Name=Advanced Clipboard Manager
Comment=Clipboard history manager
Exec={exe_path}
Terminal=false
Categories=Utility;
'''
                
                # Write desktop file
                with open(desktop_path, 'w') as f:
                    f.write(desktop_content)
                
                # Make it executable
                os.chmod(desktop_path, 0o755)
                
                logger.info(f"Added to Linux startup: {desktop_path}")
            else:
                # Remove desktop file if it exists
                if os.path.exists(desktop_path):
                    os.remove(desktop_path)
                    logger.info(f"Removed from Linux startup: {desktop_path}")
        except Exception as e:
            logger.error(f"Failed to configure Linux autostart: {e}")
