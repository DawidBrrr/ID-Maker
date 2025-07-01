import os
import cv2
import numpy as np
import json

#TODO becouse of this two functions antivirus can block the program
def cv2_imwrite_unicode(filepath, image):
    """
    Workaround for cv2.imwrite not supporting Unicode filenames on Windows.
    Encode the image into a memory buffer and write it using Python's open().
    
    Args:
        filepath (str): Full path to the image file, can contain Unicode characters
        image (numpy.ndarray): Image array to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Normalize the path to handle any path separators
        normalized_path = os.path.normpath(filepath)
        
        # Get file extension (e.g., '.png', '.jpg')
        ext = os.path.splitext(normalized_path)[1]
        
        # cv2.imencode expects the extension with a dot
        success, encoded_img = cv2.imencode(ext, image)
        
        if success:
            with open(normalized_path, "wb") as f:
                f.write(encoded_img)
            return True
        else:
            print(f"Failed to encode image for path: {normalized_path}")
            return False
            
    except PermissionError:
        print(f"Permission denied accessing file at: {normalized_path}")
        return False
    except Exception as e:
        print(f"Error saving image at {normalized_path}: {str(e)}")
        return False
    
def cv2_imread_unicode(filepath):
    """
    Workaround for cv2.imread not supporting Unicode filenames on Windows.
    Read image using Python's open() and decode with cv2.imdecode.
    
    Args:
        filepath (str): Full path to the image file, can contain Unicode characters
        
    Returns:
        numpy.ndarray: Image array if successful, None if failed
    """
    try:
        # Normalize the path to handle any path separators
        normalized_path = os.path.normpath(filepath)
        
        # Read the file into a byte array using regular Python I/O
        with open(normalized_path, 'rb') as f:
            byte_array = bytearray(f.read())
        
        # Convert to numpy array
        img_array = np.asarray(byte_array, dtype=np.uint8)
        
        # Decode the image using OpenCV
        image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        
        if image is None:
            print(f"Failed to decode image at path: {normalized_path}")
            return None
            
        return image
    except FileNotFoundError:
        print(f"Image file not found at path: {normalized_path}")
        return None
    except PermissionError:
        print(f"Permission denied accessing file at: {normalized_path}")
        return None
    except Exception as e:
        print(f"Error reading image at {normalized_path}: {str(e)}")
        return None
    