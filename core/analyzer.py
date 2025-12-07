import cv2
import numpy as np
import matplotlib.pyplot as plt

class TextureAnalyzer:
    def __init__(self):
        pass

    def analyze_texture(self, image_path):
        """
        Analyzes image complexity to find optimal embedding regions.
        mimics the 'AI Texture Analyzer' by finding high-entropy (busy) areas.
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        # 1. Use Canny Edge Detection to find 'busy' textures
        edges = cv2.Canny(img, 100, 200)
        
        # 2. Dilate edges to create 'safe zones' around textures
        kernel = np.ones((5,5), np.uint8)
        texture_map = cv2.dilate(edges, kernel, iterations=1)
        
        # Calculate 'Capacity' (how many bits we can hide safely)
        # We assume we can hide data wherever the texture map is white (255)
        safe_pixels = np.count_nonzero(texture_map)
        
        return texture_map, safe_pixels

    def visualize_map(self, image_path):
        """Debug function to show the user the analysis map"""
        texture_map, _ = self.analyze_texture(image_path)
        
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        plt.imshow(cv2.imread(image_path)[:,:,::-1])
        plt.title("Original Image")
        
        plt.subplot(1, 2, 2)
        plt.imshow(texture_map, cmap='hot')
        plt.title("AI/Texture Analysis Map\n(White areas = Safe for Hiding)")
        plt.show()