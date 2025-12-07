import cv2
import numpy as np
import random

class AttackSimulator:
    @staticmethod
    def apply_noise(image_path, intensity=0.02):
        """Adds Salt & Pepper noise to simulate signal corruption."""
        img = cv2.imread(image_path)
        row, col, ch = img.shape
        
        # Salt (White dots)
        num_salt = np.ceil(intensity * img.size * 0.5)
        coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img.shape]
        img[tuple(coords)] = 255

        # Pepper (Black dots)
        num_pepper = np.ceil(intensity * img.size * 0.5)
        coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img.shape]
        img[tuple(coords)] = 0
        
        output_path = "assets/attacked_noise.png"
        cv2.imwrite(output_path, img)
        return output_path

    @staticmethod
    def apply_jpeg_compression(image_path, quality=50):
        """Compresses image to simulate transmission loss."""
        img = cv2.imread(image_path)
        output_path = "assets/attacked_compressed.jpg"
        # 0 = Worst Quality, 100 = Best. 50 is a strong attack.
        cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return output_path

    @staticmethod
    def apply_crop(image_path, crop_percent=10):
        """Crops the image edges to simulate geometric attacks."""
        img = cv2.imread(image_path)
        h, w, _ = img.shape
        
        # Calculate crop size
        y_crop = int(h * (crop_percent / 100))
        x_crop = int(w * (crop_percent / 100))
        
        # Black out the borders (Simulating data loss)
        img[:y_crop, :] = 0  # Top
        img[-y_crop:, :] = 0 # Bottom
        img[:, :x_crop] = 0  # Left
        img[:, -x_crop:] = 0 # Right
        
        output_path = "assets/attacked_cropped.png"
        cv2.imwrite(output_path, img)
        return output_path