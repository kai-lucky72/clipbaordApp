#!/usr/bin/env python3
"""
Clipboard Adapter Module

This module provides a simplified wrapper around clipboard operations,
avoiding PyQt5 dependencies which can cause issues in headless environments.
"""
import os
import sys
import logging
import subprocess
import tempfile
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

class ClipboardAdapter:
    """
    Platform-independent clipboard adapter that avoids PyQt5 dependencies.
    """
    
    @staticmethod
    def get_text():
        """
        Get text from clipboard using platform-specific methods.
        
        Returns:
            str or None: Clipboard text content or None if not available
        """
        try:
            # We're not using pyperclip anymore to avoid PyQt5 dependency issues
            
            # Fall back to platform-specific methods
            platform = sys.platform
            
            if platform == 'win32':
                # Windows fallback using powershell
                try:
                    result = subprocess.run(
                        ['powershell', '-command', 'Get-Clipboard'],
                        capture_output=True, text=True, check=True
                    )
                    return result.stdout.strip()
                except Exception as e:
                    logger.error(f"Windows clipboard access failed: {e}")
                    
            elif platform == 'darwin':
                # macOS fallback using pbpaste
                try:
                    result = subprocess.run(
                        ['pbpaste'],
                        capture_output=True, text=True, check=True
                    )
                    return result.stdout
                except Exception as e:
                    logger.error(f"macOS clipboard access failed: {e}")
                    
            elif platform.startswith('linux'):
                # Linux fallback using xclip or xsel if available
                for cmd in [
                    ['xclip', '-selection', 'clipboard', '-o'],
                    ['xsel', '-b', '-o']
                ]:
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True, text=True, check=False
                        )
                        if result.returncode == 0:
                            return result.stdout
                    except FileNotFoundError:
                        continue
                
                logger.error("Linux clipboard access failed: xclip/xsel not available")
                
        except Exception as e:
            logger.error(f"Error getting clipboard text: {e}")
            
        return None
    
    @staticmethod
    def set_text(text):
        """
        Set text to clipboard using platform-specific methods.
        
        Args:
            text (str): Text to copy to clipboard
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # We're not using pyperclip anymore to avoid PyQt5 dependency issues
            
            # Fall back to platform-specific methods
            platform = sys.platform
            
            if platform == 'win32':
                # Windows fallback using powershell
                try:
                    # Escape quotes in PowerShell commands
                    escaped_text = text.replace('"', '`"')
                    command = f'Set-Clipboard -Value "{escaped_text}"'
                    subprocess.run(
                        ['powershell', '-command', command],
                        check=True
                    )
                    return True
                except Exception as e:
                    logger.error(f"Windows clipboard copy failed: {e}")
                    
            elif platform == 'darwin':
                # macOS fallback using pbcopy
                try:
                    proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
                    proc.communicate(text.encode('utf-8'))
                    return proc.returncode == 0
                except Exception as e:
                    logger.error(f"macOS clipboard copy failed: {e}")
                    
            elif platform.startswith('linux'):
                # Linux fallback using xclip or xsel if available
                for cmd_base in [
                    ['xclip', '-selection', 'clipboard'],
                    ['xsel', '-b', '-i']
                ]:
                    try:
                        proc = subprocess.Popen(cmd_base, stdin=subprocess.PIPE)
                        proc.communicate(text.encode('utf-8'))
                        if proc.returncode == 0:
                            return True
                    except FileNotFoundError:
                        continue
                
                logger.error("Linux clipboard copy failed: xclip/xsel not available")
                
        except Exception as e:
            logger.error(f"Error setting clipboard text: {e}")
            
        return False
    
    @staticmethod
    def get_image():
        """
        Get image from clipboard using platform-specific methods.
        
        Returns:
            bytes or None: Image data as bytes or None if not available
        """
        try:
            platform = sys.platform
            
            if platform == 'win32':
                # Windows - attempt to use PowerShell and temp files
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.close()
                    
                    # PowerShell script to save clipboard image
                    ps_script = f'''
                    Add-Type -Assembly System.Windows.Forms;
                    $img = [Windows.Forms.Clipboard]::GetImage();
                    if ($img) {{
                        $img.Save("{temp_file.name}");
                        exit 0;
                    }} else {{
                        exit 1;
                    }}
                    '''
                    
                    result = subprocess.run(
                        ['powershell', '-command', ps_script],
                        capture_output=True, check=False
                    )
                    
                    if result.returncode == 0 and os.path.exists(temp_file.name):
                        with open(temp_file.name, 'rb') as f:
                            image_data = f.read()
                        os.unlink(temp_file.name)
                        return image_data
                    
                    # Clean up temp file
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                        
                except Exception as e:
                    logger.error(f"Windows clipboard image access failed: {e}")
                    
            elif platform == 'darwin':
                # macOS - using pngpaste if available
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.close()
                    
                    result = subprocess.run(
                        ['pngpaste', temp_file.name],
                        capture_output=True, check=False
                    )
                    
                    if result.returncode == 0 and os.path.exists(temp_file.name):
                        with open(temp_file.name, 'rb') as f:
                            image_data = f.read()
                        os.unlink(temp_file.name)
                        return image_data
                    
                    # Clean up temp file
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                        
                except Exception as e:
                    logger.error(f"macOS clipboard image access failed: {e}")
                    
            elif platform.startswith('linux'):
                # Linux - trying xclip with image formats
                try:
                    for fmt in ['image/png', 'image/jpeg', 'image/bmp']:
                        try:
                            result = subprocess.run(
                                ['xclip', '-selection', 'clipboard', '-t', fmt, '-o'],
                                capture_output=True, check=False
                            )
                            if result.returncode == 0 and result.stdout:
                                return result.stdout
                        except:
                            pass
                except Exception as e:
                    logger.error(f"Linux clipboard image access failed: {e}")
                
        except Exception as e:
            logger.error(f"Error getting clipboard image: {e}")
            
        return None
    
    @staticmethod
    def set_image(image_data):
        """
        Set image to clipboard using platform-specific methods.
        
        Args:
            image_data (bytes): Image data as bytes
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Verify image data is valid
            try:
                img = Image.open(BytesIO(image_data))
                img.verify()  # Verify it's a valid image
            except Exception as e:
                logger.error(f"Invalid image data: {e}")
                return False
            
            platform = sys.platform
            
            if platform == 'win32':
                # Windows - using temp file and PowerShell
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    temp_file.close()
                    
                    # Save image to temp file
                    with open(temp_file.name, 'wb') as f:
                        f.write(image_data)
                    
                    # PowerShell script to load image into clipboard
                    ps_script = f'''
                    Add-Type -Assembly System.Windows.Forms;
                    Add-Type -Assembly System.Drawing;
                    $img = [System.Drawing.Image]::FromFile("{temp_file.name}");
                    [Windows.Forms.Clipboard]::SetImage($img);
                    '''
                    
                    subprocess.run(
                        ['powershell', '-command', ps_script],
                        check=True
                    )
                    
                    # Clean up
                    if os.path.exists(temp_file.name):
                        os.unlink(temp_file.name)
                    
                    return True
                        
                except Exception as e:
                    logger.error(f"Windows clipboard image copy failed: {e}")
                    
            elif platform == 'darwin':
                # macOS - using impbcopy if available, otherwise temp file
                try:
                    proc = subprocess.Popen(
                        ['impbcopy'],
                        stdin=subprocess.PIPE
                    )
                    proc.communicate(image_data)
                    return proc.returncode == 0
                except FileNotFoundError:
                    # Try alternate method with temp file and osascript
                    try:
                        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                        temp_file.close()
                        
                        # Save image to temp file
                        with open(temp_file.name, 'wb') as f:
                            f.write(image_data)
                        
                        # Use AppleScript to set clipboard
                        script = f'''
                        set theFile to POSIX file "{temp_file.name}"
                        set theImage to read theFile as TIFF picture
                        set the clipboard to theImage
                        '''
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.applescript') as script_file:
                            script_file.write(script.encode('utf-8'))
                            script_path = script_file.name
                        
                        subprocess.run(
                            ['osascript', script_path],
                            check=True
                        )
                        
                        # Clean up
                        if os.path.exists(temp_file.name):
                            os.unlink(temp_file.name)
                        if os.path.exists(script_path):
                            os.unlink(script_path)
                        
                        return True
                        
                    except Exception as e:
                        logger.error(f"macOS clipboard image copy alternate method failed: {e}")
                    
            elif platform.startswith('linux'):
                # Linux - using xclip if available
                try:
                    # Determine image MIME type
                    mime_type = 'image/png'  # Default
                    img = Image.open(BytesIO(image_data))
                    if img.format:
                        mime_type = f'image/{img.format.lower()}'
                    
                    proc = subprocess.Popen(
                        ['xclip', '-selection', 'clipboard', '-t', mime_type],
                        stdin=subprocess.PIPE
                    )
                    proc.communicate(image_data)
                    return proc.returncode == 0
                    
                except Exception as e:
                    logger.error(f"Linux clipboard image copy failed: {e}")
                
        except Exception as e:
            logger.error(f"Error setting clipboard image: {e}")
            
        return False