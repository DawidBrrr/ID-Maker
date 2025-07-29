import os
import shutil


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
                    print(f'Failed to delete {file_path}. Reason: {e}')
            # Usuń pusty folder po wszystkim
            try:
                os.rmdir(folder)
            except Exception:
                pass