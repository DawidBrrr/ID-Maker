import os
import shutil
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

def clear_client_data(upload_folder, output_folder, error_folder):
    """
    Clear all client data by removing files from user's upload, output, and error folders.
    """
    for folder in [upload_folder, output_folder, error_folder]:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}. Reason: {e}")
            # Usuń pusty folder po wszystkim
            try:
                os.rmdir(folder)
            except Exception:
                logger.warning(f"Failed to remove empty folder: {folder}")


def cleanup_filesystem(folder: str, max_age_hours: int):
    """Removes old files and empty folders"""
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    

    for root, dirs, files in os.walk(folder):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                # Check age of the file
                file_age = now - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    os.remove(file_path)
                    logger.info(f"Removed old file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing file {file_path}: {e}")

        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Remove empty directories
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    logger.info(f"Removed empty directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error removing directory {dir_path}: {e}")


def get_filename_from_path(path: str) -> str:
    """Return the filename from a given file path."""
    return Path(path).name