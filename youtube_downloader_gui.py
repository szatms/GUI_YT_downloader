import sys
import os
import subprocess
import re
import logging
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QComboBox, 
                             QMessageBox, QProgressBar, QFileDialog, QCheckBox, 
                             QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCharFormat
import threading

# Setup logging
logging.basicConfig(
    filename='logs.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class DownloadThread(QThread):
    download_progress = pyqtSignal(int)
    download_finished = pyqtSignal(str)
    download_error = pyqtSignal(str)

    def __init__(self, url, format_type, output_dir, is_playlist=False):
        super().__init__()
        # Only sanitize URL if not in playlist mode to preserve playlist parameters
        if is_playlist:
            self.url = url  # Don't sanitize when playlist mode is enabled
        else:
            self.url = self.sanitize_url(url)
        self.format_type = format_type
        self.output_dir = output_dir
        self.is_playlist = is_playlist

    def sanitize_url(self, url):
        """Remove playlist and radio parameters from URL to avoid downloading entire playlists"""
        import re
        # Remove common YouTube playlist and radio parameters
        url = re.sub(r'&list=[^&]*', '', url)
        url = re.sub(r'&start_radio=1', '', url)
        url = re.sub(r'&radio=1', '', url)
        return url

    def run(self):
        try:
            logging.info(f"Starting download for URL: {self.url}, format: {self.format_type}, playlist: {self.is_playlist}")
            # Build yt-dlp command with forced MP3 format
            if self.format_type == "mp3":
                cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", f"{self.output_dir}/%(title)s.%(ext)s", self.url]
            else:
                cmd = ["yt-dlp", "-f", "best", "-o", f"{self.output_dir}/%(title)s.%(ext)s", self.url]
            
            # Add playlist flag if needed
            if self.is_playlist:
                cmd.insert(1, "--yes-playlist")
            
            # Add no-playlist flag if we're not in playlist mode to prevent accidental playlist downloads
            if not self.is_playlist:
                cmd.insert(1, "--no-playlist")
            
            logging.debug(f"Executing command: {' '.join(cmd)}")
            # Run the command and capture output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Just pass through the output to show basic status
            for line in process.stdout:
                logging.debug(f"Process output: {line.strip()}")
                # We'll just show a simple status line for download activity
                if "[download]" in line and ("ETA" in line or "100%" in line):
                    # Show when download starts and completes
                    self.download_progress.emit(0)  # Emit dummy signal to trigger update
                    
            process.wait()
            logging.info(f"Process finished with return code: {process.returncode}")
            if process.returncode != 0:
                logging.error(f"Command failed with return code: {process.returncode}")
                # Get the actual command that was run and the output
                logging.error(f"Command executed: {' '.join(cmd)}")
                if process.stdout:
                    logging.error(f"Last few lines of output: {process.stdout[-10:] if hasattr(process.stdout, '__len__') else 'Could not get output'}")
            
            if process.returncode == 0:
                self.download_finished.emit("Download completed successfully!")
            else:
                error_msg = f"Download failed with return code: {process.returncode}"
                logging.error(error_msg)
                self.download_error.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Exception in download thread: {str(e)}"
            logging.error(error_msg)
            self.download_error.emit(error_msg)

class YouTubeDownloader(QWidget):
    def __init__(self):
        super().__init__()
        # Set default download directory to system downloads folder
        self.output_dir = os.path.expanduser("~/Downloads")
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('YouTube Downloader')
        self.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        # URL input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("YouTube URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=... or playlist URL")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)
        
        # Playlist checkbox
        self.playlist_checkbox = QCheckBox("Download as Playlist")
        self.playlist_checkbox.stateChanged.connect(self.toggle_playlist_mode)
        layout.addWidget(self.playlist_checkbox)
        
        # Output directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Download Location:"))
        self.dir_label = QLabel(self.output_dir)
        self.dir_button = QPushButton("Browse...")
        self.dir_button.clicked.connect(self.select_directory)
        dir_layout.addWidget(self.dir_label)
        dir_layout.addWidget(self.dir_button)
        layout.addLayout(dir_layout)
        
        # Visual feedback area
        self.feedback_label = QLabel("")
        self.feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback_label.setStyleSheet("QLabel { font-size: 48px; }")
        self.feedback_label.setVisible(False)  # Hidden by default
        # Add stretch to push feedback to bottom
        layout.addStretch()
        layout.addWidget(self.feedback_label)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3 (Audio)", "MP4 (Video)"])
        self.format_combo.setCurrentIndex(0)  # Default to MP3
        format_layout.addWidget(self.format_combo)
        layout.addLayout(format_layout)
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)
        
        # Status label
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        # Terminal-style status box
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.status_box.setMaximumHeight(150)
        self.status_box.setStyleSheet("QTextEdit { background-color: #303030; color: white; font-family: monospace; }")
        layout.addWidget(self.status_box)
        
        # Add stretch to push status box to bottom
        layout.addStretch()
        
        self.setLayout(layout)
        
    def toggle_playlist_mode(self, state):
        """Enable/disable playlist mode"""
        if state == Qt.CheckState.Checked:
            self.format_combo.setCurrentIndex(0)  # Force MP3 for playlists
            self.format_combo.setEnabled(False)
        else:
            self.format_combo.setEnabled(True)
        
    def select_directory(self):
        """Allow user to select download directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Download Directory")
        if directory:
            self.output_dir = directory
            self.dir_label.setText(directory)
        
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
            
        format_type = "mp3" if self.format_combo.currentIndex() == 0 else "mp4"
        is_playlist = self.playlist_checkbox.isChecked()
        
        self.download_btn.setEnabled(False)
        self.status_box.clear()
        self.status_box.append("Starting download...")
        self.status_box.append(f"URL: {url}")
        self.status_box.append("Status: Started")
        
        # Create and start download thread
        self.download_thread = DownloadThread(url, format_type, self.output_dir, is_playlist)
        self.download_thread.download_progress.connect(self.update_progress)
        self.download_thread.download_finished.connect(self.download_completed)
        self.download_thread.download_error.connect(self.download_error)
        self.download_thread.start()
        
    def update_progress(self, percentage):
        # Show download status messages
        self.status_box.append("Status: Downloading...")
        
    def download_completed(self, message):
        self.status_box.append("Status: Done")
        self.status_box.append(message)
        self.download_btn.setEnabled(True)
        
    def hide_feedback(self):
        pass
        
    def download_error(self, error_message):
        self.status_box.append("Status: Error")
        self.status_box.append(f"Error: {error_message}")
        self.download_btn.setEnabled(True)
        logging.error(f"Download error: {error_message}")
        QMessageBox.critical(self, "Error", error_message)

def main():
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()