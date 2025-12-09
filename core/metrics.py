import cv2
import numpy as np
import math

class StegoMetrics:
    @staticmethod
    def calculate_psnr(original_path, stego_path):
        """Calculates Peak Signal-to-Noise Ratio (PSNR). Higher is better."""
        img1 = cv2.imread(original_path)
        img2 = cv2.imread(stego_path)
        
        if img1 is None or img2 is None:
            return 0

        # Align dimensions if needed (DWT/DCT sometimes crops)
        h_min = min(img1.shape[0], img2.shape[0])
        w_min = min(img1.shape[1], img2.shape[1])
        img1 = img1[:h_min, :w_min]
        img2 = img2[:h_min, :w_min]
        
        mse = np.mean((img1 - img2) ** 2)
        if mse == 0:
            return 100  # Identical
            
        max_pixel = 255.0
        psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
        return psnr

    @staticmethod
    def calculate_ssim(original_path, stego_path):
        """
        Calculates Structural Similarity Index (SSIM).
        Range: -1 to 1. Closer to 1 is better.
        Implemented using OpenCV/Numpy to avoid 'scikit-image' dependency.
        """
        img1 = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(stego_path, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return 0

        # Align dimensions
        h_min = min(img1.shape[0], img2.shape[0])
        w_min = min(img1.shape[1], img2.shape[1])
        img1 = img1[:h_min, :w_min]
        img2 = img2[:h_min, :w_min]

        # Constants for SSIM
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2

        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)

        kernel = cv2.getGaussianKernel(11, 1.5)
        window = np.outer(kernel, kernel.transpose())

        mu1 = cv2.filter2D(img1, -1, window)[5:-5, 5:-5]  # valid mode
        mu2 = cv2.filter2D(img2, -1, window)[5:-5, 5:-5]
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.filter2D(img1**2, -1, window)[5:-5, 5:-5] - mu1_sq
        sigma2_sq = cv2.filter2D(img2**2, -1, window)[5:-5, 5:-5] - mu2_sq
        sigma12 = cv2.filter2D(img1 * img2, -1, window)[5:-5, 5:-5] - mu1_mu2

        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
                   ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        
        return ssim_map.mean()

    @staticmethod
    def calculate_ber(original_msg, extracted_msg):
        """
        Calculates Bit Error Rate (BER).
        Range: 0.0 to 1.0. Lower is better (0.0 = perfect recovery).
        """
        if not extracted_msg:
            return 1.0  # 100% Error if nothing extracted

        def to_bin(data):
            return ''.join([format(ord(i), "08b") for i in data])

        bin_orig = to_bin(original_msg)
        bin_ext = to_bin(extracted_msg)

        # Pad with zeros if lengths differ (simple approach)
        max_len = max(len(bin_orig), len(bin_ext))
        bin_orig = bin_orig.ljust(max_len, '0')
        bin_ext = bin_ext.ljust(max_len, '0')

        errors = sum(c1 != c2 for c1, c2 in zip(bin_orig, bin_ext))
        return errors / max_len

    @staticmethod
    def calculate_payload(image_path, message):
        """
        Calculates Payload in Bits Per Pixel (bpp).
        """
        img = cv2.imread(image_path)
        if img is None: return 0
        
        h, w, _ = img.shape
        total_pixels = h * w
        
        # Message bits (8 bits per char)
        msg_bits = len(message) * 8
        
        bpp = msg_bits / total_pixels
        return bpp