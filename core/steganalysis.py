import cv2
import numpy as np
from scipy.stats import chi2

class SteganalysisScanner:
    @staticmethod
    def perform_chi_square_test(image_path):
        """
        Analyzes pixel histograms to detect LSB Steganography.
        Returns: Probability (0.0 - 1.0) that the image has hidden data.
        """
        img = cv2.imread(image_path)
        if img is None: raise ValueError("Image not found")
        
        # We analyze the Blue channel (most common for hiding)
        # Flatten to 1D array
        pixels = img[:, :, 0].flatten()
        
        # Count frequencies of each pixel value (0-255)
        counts = np.bincount(pixels, minlength=256)
        
        chi_sq_sum = 0
        k = 0 # degrees of freedom
        
        # Analyze pairs (0,1), (2,3), ... (254,255)
        for i in range(0, 256, 2):
            count_even = counts[i]
            count_odd = counts[i+1]
            
            # Expected count if random (average of the pair)
            expected = (count_even + count_odd) / 2.0
            
            if expected > 0:
                # Chi-Square Formula: sum( (observed - expected)^2 / expected )
                chi_sq_sum += ((count_even - expected) ** 2) / expected
                k += 1
        
        # Calculate p-value (Probability)
        # Low p-value (< 0.05) usually means "Natural Image"
        # High p-value (> 0.95) usually means "Hidden Data Detected"
        # We invert this for easier understanding:
        # "Probability of Steganography"
        
        p_value = chi2.cdf(chi_sq_sum, k - 1)
        prob_stego = 1.0 - p_value
        
        # Note: This specific statistical test targets LSB embedding.
        # Since we use DCT, we EXPECT this to be low (proving our robustness).
        
        return prob_stego