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
        self.cropping_successful = False

    def process_image(self):
        """
        Main method to process the image through all steps: cropping, checking, background change, and DPI adjustment.
        """
        self.crop_image()
        
        # Only proceed with further processing if cropping was successful
        if self.cropping_successful:
            self.check_image()
            self.change_background()
            self.change_dpi()
        else:
            # Still run check_image to get biometric info even if cropping failed
            self.check_image()


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
            self.cropping_successful = True
            logger.info(f"Image successfully cropped and saved to {self.processed_image_path}")
        except Exception as e:
            self.cropping_successful = False
            logger.error(f"Error processing image: {e}")
            # Don't re-raise the exception, just log it and set the flag

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
            self.biometric_info = "Zdjęcie przeszło wszystkie kontrole biometryczne"
        except NoFaceDetectedException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Nie wykryto twarzy na zdjęciu"
            logger.warning(msg)
            self.biometric_info = msg
        except MultipleFacesDetectedException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Wykryto wiele twarzy na zdjęciu"
            logger.warning(msg)
            self.biometric_info = msg
        except MissingFaceFeaturesException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Brakujące cechy twarzy"
            logger.warning(msg)
            self.biometric_info = msg
        except ObliqueFacePoseException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Twarz nie jest skierowana prosto/ukośna poza wykryta"
            logger.warning(msg)
            self.biometric_info = msg
        except OpenedMouthOrSmileException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Usta są otwarte lub wykryto uśmiech"
            logger.warning(msg)
            self.biometric_info = msg
        except AbnormalEyelidOpeningStateException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Nienormalny stan otwarcia powiek"
            logger.warning(msg)
            self.biometric_info = msg
        except UnevenlyOpenEyelidException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Oczy są nierówno otwarte"
            logger.warning(msg)
            self.biometric_info = msg
        except BiometricPassportPhotoException as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Ogólny problem z walidacją biometryczną"
            logger.warning(msg)
            self.biometric_info = msg
        except Exception as e:
            msg = f"Ostrzeżenie kontroli biometrycznej: Nieoczekiwany błąd podczas walidacji"
            logger.warning(msg)
            self.biometric_info = msg
    def get_biometric_info(self):
        """Return the biometric validation info string for frontend display."""
        return self.biometric_info

    def change_background(self):
        """Change background to white using rembg"""
        if not os.path.exists(self.processed_image_path):
            logger.warning(f"Cannot change background: file {self.processed_image_path} does not exist")
            return
            
        try:
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
        except Exception as e:
            logger.error(f"Error changing background: {e}")

    def change_dpi(self):
        """Change the DPI of the processed image"""
        if not os.path.exists(self.processed_image_path):
            logger.warning(f"Cannot change DPI: file {self.processed_image_path} does not exist")
            return
            
        try:
            with Image.open(self.processed_image_path) as img:
                img.save(self.processed_image_path, dpi=self.params['dpi'])
            logger.info(f"DPI changed to {self.params['dpi']} and saved to {self.processed_image_path}")
        except Exception as e:
            logger.error(f"Error changing DPI: {e}")