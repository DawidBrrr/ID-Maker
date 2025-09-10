import logging
import os
from majormode.photoidmagick import (
    BiometricPassportPhoto, 
    BiometricPassportPhotoException,
    NoFaceDetectedException,
    MultipleFacesDetectedException,
    MissingFaceFeaturesException,
    ObliqueFacePoseException,
    OpenedMouthOrSmileException,
    AbnormalEyelidOpeningStateException,
    UnevenlyOpenEyelidException
)
from typing import Dict, Any
from PIL import Image
from rembg import remove
from ..utils.helpers import get_filename_from_path


logger = logging.getLogger(__name__)

class id_maker:
    def __init__(self,upload_path : str,error_folder : str,output_folder : str,params: Dict[str, Any]):
        self.upload_path = upload_path
        self.error_folder = error_folder
        self.output_folder = output_folder
        self.image_name = get_filename_from_path(upload_path)
        self.processed_image_path = os.path.join(self.output_folder,self.image_name)
        self.params = params
        self.biometric_info = ""

    def process_image(self):
        """
        Main method to process the image through all steps: cropping, checking, background change, and DPI adjustment.
        """
        self.crop_image()
        self.check_image()
        self.change_background()
        self.change_dpi()


    def crop_image(self):
        """
        Crops the image to the specified dimensions and saves it to the processed_image_path
        Biometric validations are disabled to allow processing even with minor quality issues.
        """
        try:
            biometric_photo = BiometricPassportPhoto.from_file(
                self.upload_path,
                forbid_abnormally_open_eyelid=False,
                forbid_closed_eye=False,
                forbid_oblique_face=False,
                forbid_open_mouth=False,
                forbid_unevenly_open_eye=False
            )
            cropped_photo = biometric_photo.build_image(
                size=(self.params['res_x'], self.params['res_y']),
                horizontal_padding=self.params['horizontal_padding'],
                vertical_padding=self.params['vertical_padding']
            )
            cropped_photo.save(self.processed_image_path)
            logger.info(f"Image successfully cropped and saved to {self.processed_image_path}")
        except Exception as e:
            logger.error(f"Error processing image: {e}")

    def check_image(self):
        """
        Check image for biometric compliance and log warnings for any issues.
        This function performs validation but doesn't stop processing.
        Sets self.biometric_info for frontend display.
        """
        try:
            biometric_photo = BiometricPassportPhoto.from_file(
                self.upload_path,
                forbid_abnormally_open_eyelid=True,
                forbid_closed_eye=True,
                forbid_oblique_face=True,
                forbid_open_mouth=True,
                forbid_unevenly_open_eye=True
            )
            logger.info("Image passed all biometric validation checks")
            self.biometric_info = "Image passed all biometric validation checks"
        except NoFaceDetectedException as e:
            msg = f"Biometric check warning: No face detected in the image - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except MultipleFacesDetectedException as e:
            msg = f"Biometric check warning: Multiple faces detected in the image - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except MissingFaceFeaturesException as e:
            msg = f"Biometric check warning: Missing facial features detected - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except ObliqueFacePoseException as e:
            msg = f"Biometric check warning: Face is not straight/oblique pose detected - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except OpenedMouthOrSmileException as e:
            msg = f"Biometric check warning: Mouth is open or smiling - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except AbnormalEyelidOpeningStateException as e:
            msg = f"Biometric check warning: Abnormal eyelid opening state - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except UnevenlyOpenEyelidException as e:
            msg = f"Biometric check warning: Eyes are unevenly open - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except BiometricPassportPhotoException as e:
            msg = f"Biometric check warning: General biometric validation issue - {e}"
            logger.warning(msg)
            self.biometric_info = msg
        except Exception as e:
            msg = f"Biometric check warning: Unexpected error during validation - {e}"
            logger.warning(msg)
            self.biometric_info = msg
    def get_biometric_info(self):
        """Return the biometric validation info string for frontend display."""
        return self.biometric_info

    def change_background(self):
        processed_image = Image.open(self.processed_image_path)

        # Change background to white with rembg force CPU
        no_bg_image = remove(
            processed_image,
            providers=['CPUExecutionProvider'],
            alpha_matting=True,
            alpha_matting_foreground_threshold=250,
            alpha_matting_background_threshold=5,
            alpha_matting_erode_size=5
        )
        # Change transparent background to white
        white_bg = Image.new("RGB", no_bg_image.size, (255, 255, 255))
        white_bg.paste(no_bg_image, mask=no_bg_image.split()[3] if len(no_bg_image.split()) > 3 else None)

        # Save final image
        white_bg.save(self.processed_image_path)
        logger.info(f"Background changed to white and saved to {self.processed_image_path}")

    def change_dpi(self):
        try:
            with Image.open(self.processed_image_path) as img:
                img.save(self.processed_image_path, dpi=self.params['dpi'])
            logger.info(f"DPI changed to {self.params['dpi']} and saved to {self.processed_image_path}")
        except Exception as e:
            logger.error(f"Error changing DPI: {e}")