import cv2
import numpy as np
import random

class AttackSimulator:
    @staticmethod
    def apply_noise_salt_pepper(image_path, intensity=0.02):
        """Original Salt & Pepper Attack"""
        img = cv2.imread(image_path)
        if img is None: return image_path
        
        # Salt
        num_salt = np.ceil(intensity * img.size * 0.5)
        coords = [np.random.randint(0, i - 1, int(num_salt)) for i in img.shape]
        img[tuple(coords)] = 255

        # Pepper
        num_pepper = np.ceil(intensity * img.size * 0.5)
        coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in img.shape]
        img[tuple(coords)] = 0
        
        output_path = "assets/attacked_noise_sp.png"
        cv2.imwrite(output_path, img)
        return output_path

    @staticmethod
    def apply_noise_gaussian(image_path, var=50):
        """Adds Gaussian Noise (simulating electronic/sensor noise)."""
        img = cv2.imread(image_path)
        if img is None: return image_path

        mean = 0
        sigma = var ** 0.5
        gaussian = np.random.normal(mean, sigma, img.shape)
        
        noisy_image = np.zeros(img.shape, np.float32)
        noisy_image = img + gaussian
        noisy_image = np.clip(noisy_image, 0, 255).astype(np.uint8)
        
        output_path = "assets/attacked_noise_gaussian.png"
        cv2.imwrite(output_path, noisy_image)
        return output_path

    @staticmethod
    def apply_rotation(image_path, angle=10):
        """Rotates image by 'angle' degrees (Simulating geometric attacks)."""
        img = cv2.imread(image_path)
        if img is None: return image_path
        
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h))
        
        output_path = f"assets/attacked_rot{angle}.png"
        cv2.imwrite(output_path, rotated)
        return output_path

    @staticmethod
    def apply_filter_blur(image_path, kernel_size=5):
        """Applies Gaussian Blur (Simulating filtering/smoothing)."""
        img = cv2.imread(image_path)
        if img is None: return image_path
        
        blurred = cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)
        
        output_path = "assets/attacked_blur.png"
        cv2.imwrite(output_path, blurred)
        return output_path

    @staticmethod
    def apply_jpeg_compression(image_path, quality=50):
        """Compresses image (Quality: 1-100). Lower is stronger attack."""
        img = cv2.imread(image_path)
        output_path = f"assets/attacked_jpeg_{quality}.jpg"
        cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return output_path

    @staticmethod
    def apply_crop(image_path, crop_percent=10):
        """Crops borders."""
        img = cv2.imread(image_path)
        h, w, _ = img.shape
        
        y_crop = int(h * (crop_percent / 100))
        x_crop = int(w * (crop_percent / 100))
        
        img[:y_crop, :] = 0
        img[-y_crop:, :] = 0
        img[:, :x_crop] = 0
        img[:, -x_crop:] = 0
        
        output_path = "assets/attacked_cropped.png"
        cv2.imwrite(output_path, img)
        return output_path