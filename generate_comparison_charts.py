import matplotlib.pyplot as plt
import numpy as np
import os

# --- 1. ENTER YOUR DATA HERE ---
# Replace these values with your actual benchmark findings
# (These are sample values based on typical Steganography results)
results = {
    "images": ["Lena", "Baboon", "Peppers", "Airplane"],
    
    # METRIC 1: PSNR (Higher is Better)
    # Visual Quality: Adaptive usually has slightly lower or similar PSNR because it targets edges
    "psnr_seq":   [52.4, 48.1, 51.2, 53.0], 
    "psnr_adapt": [51.8, 47.9, 50.5, 52.1],

    # METRIC 2: SSIM (Higher is Better, Max 1.0)
    # Structural Similarity: Adaptive should be very high, preserving structure
    "ssim_seq":   [0.985, 0.920, 0.975, 0.990],
    "ssim_adapt": [0.992, 0.945, 0.988, 0.995],

    # METRIC 3: BER (Lower is Better)
    # Robustness against Attack (e.g., JPEG compression)
    # Adaptive should be significantly lower (better) than Sequential
    "ber_seq":    [0.15, 0.22, 0.18, 0.12],  # 15% error, 22% error...
    "ber_adapt":  [0.02, 0.05, 0.03, 0.01]   # 2% error, 5% error...
}

OUTPUT_DIR = "benchmark_charts"

# --- 2. PLOTTING FUNCTION ---
def generate_charts():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    labels = results["images"]
    x = np.arange(len(labels))  # Label locations
    width = 0.35  # Width of the bars

    # --- CHART 1: PSNR ---
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, results["psnr_seq"], width, label='Sequential (Standard)', color='#95a5a6')
    plt.bar(x + width/2, results["psnr_adapt"], width, label='Adaptive (Proposed)', color='#2ecc71')
    
    plt.ylabel('PSNR (dB) - Higher is Better')
    plt.title('Visual Quality Comparison (PSNR)')
    plt.xticks(x, labels)
    plt.legend()
    plt.ylim(40, 60) # Set reasonable range for visibility
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    save_path = os.path.join(OUTPUT_DIR, "chart_psnr.png")
    plt.savefig(save_path)
    print(f"[+] Saved {save_path}")
    plt.close()

    # --- CHART 2: SSIM ---
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, results["ssim_seq"], width, label='Sequential (Standard)', color='#95a5a6')
    plt.bar(x + width/2, results["ssim_adapt"], width, label='Adaptive (Proposed)', color='#3498db')
    
    plt.ylabel('SSIM Index (0-1) - Higher is Better')
    plt.title('Structural Similarity Comparison (SSIM)')
    plt.xticks(x, labels)
    plt.legend()
    plt.ylim(0.9, 1.0) # Zoom in to show fine differences
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    save_path = os.path.join(OUTPUT_DIR, "chart_ssim.png")
    plt.savefig(save_path)
    print(f"[+] Saved {save_path}")
    plt.close()

    # --- CHART 3: BER ---
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, results["ber_seq"], width, label='Sequential (Standard)', color='#95a5a6')
    plt.bar(x + width/2, results["ber_adapt"], width, label='Adaptive (Proposed)', color='#e74c3c')
    
    plt.ylabel('Bit Error Rate (BER) - Lower is Better')
    plt.title('Robustness Against JPEG Attack (BER)')
    plt.xticks(x, labels)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    save_path = os.path.join(OUTPUT_DIR, "chart_ber.png")
    plt.savefig(save_path)
    print(f"[+] Saved {save_path}")
    plt.close()

if __name__ == "__main__":
    generate_charts()
    print("\nDone! Check the 'benchmark_charts' folder.")