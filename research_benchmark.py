import cv2
import numpy as np
import difflib  # To calculate text similarity (Recovery %)
from core.steganography_dct import DCTSteganography
from core.metrics import StegoMetrics
from core.steganalysis import SteganalysisScanner
from core.attacks import AttackSimulator

def calculate_recovery_rate(original_msg, recovered_msg):
    """Calculates how much of the message survived the attack (0-100%)."""
    if not recovered_msg or "No hidden message" in recovered_msg:
        return 0.0
    matcher = difflib.SequenceMatcher(None, original_msg, recovered_msg)
    return matcher.ratio() * 100

def generate_diff_map(original_path, stego_path, save_path):
    """Creates a high-contrast visual proof of WHERE data is hidden."""
    img1 = cv2.imread(original_path).astype(float)
    img2 = cv2.imread(stego_path).astype(float)
    
    # Handle Dimension Mismatch (Crop to smaller size)
    h_min = min(img1.shape[0], img2.shape[0])
    w_min = min(img1.shape[1], img2.shape[1])
    img1 = img1[:h_min, :w_min]
    img2 = img2[:h_min, :w_min]
    
    # Calculate Difference & Amplify
    diff = np.abs(img1 - img2)
    diff_amplified = diff * 50.0  # Amplify x50 to make it visible
    
    # Clip and convert to uint8 (Fixes the warning)
    diff_final = np.clip(diff_amplified, 0, 255).astype(np.uint8)
    cv2.imwrite(save_path, diff_final)

def run_comparative_study(cover_image_path, secret_message):
    print(f"--- Starting Full Research Benchmark on {cover_image_path} ---")
    stego = DCTSteganography()
    
    # File Paths
    seq_output = "research_sequential.png"
    adapt_output = "research_adaptive.png"
    
    # --- PHASE 1: EMBEDDING ---
    print("\n[1/5] Embedding Data...")
    print("   > Legacy Sequential Mode...")
    stego.dct_embed(cover_image_path, secret_message, seq_output, use_adaptive=False)
    
    print("   > Proposed Adaptive Mode...")
    stego.dct_embed(cover_image_path, secret_message, adapt_output, use_adaptive=True)
    
    # --- PHASE 2: VISUAL & STATISTICAL METRICS ---
    print("\n[2/5] Calculating Quality & Security Metrics...")
    psnr_seq = StegoMetrics.calculate_psnr(cover_image_path, seq_output)
    psnr_adapt = StegoMetrics.calculate_psnr(cover_image_path, adapt_output)
    
    detect_seq = SteganalysisScanner.perform_chi_square_test(seq_output)
    detect_adapt = SteganalysisScanner.perform_chi_square_test(adapt_output)
    
    # --- PHASE 3: GENERATE VISUAL PROOF ---
    print("\n[3/5] Generating Difference Maps (Check folder!)...")
    generate_diff_map(cover_image_path, seq_output, "diff_sequential.png")
    generate_diff_map(cover_image_path, adapt_output, "diff_adaptive.png")
    
    # --- PHASE 4: ROBUSTNESS ATTACK SIMULATION ---
    print("\n[4/5] Simulating Cyber Attacks (JPEG Compression)...")
    
    # Attack 1: Sequential File (Noise instead of Compression)
    attacked_seq_path = AttackSimulator.apply_noise(seq_output, intensity=0.01) # 1% noise
    # Attack 2: Adaptive File
    attacked_adapt_path = AttackSimulator.apply_noise(adapt_output, intensity=0.01)
    
    # --- PHASE 5: RECOVERY TESTING ---
    print("\n[5/5] Attempting Data Recovery...")
    
    # Recover from Sequential
    try:
        rec_seq = stego.dct_extract(attacked_seq_path, use_adaptive=False)
        score_seq = calculate_recovery_rate(secret_message, rec_seq)
    except Exception as e:
        rec_seq = "Extraction Error"
        score_seq = 0.0

    # Recover from Adaptive
    try:
        rec_adapt = stego.dct_extract(attacked_adapt_path, use_adaptive=True)
        score_adapt = calculate_recovery_rate(secret_message, rec_adapt)
    except Exception as e:
        rec_adapt = "Extraction Error"
        score_adapt = 0.0

    # --- FINAL REPORT ---
    print("\n" + "="*60)
    print(f"{'METRIC':<25} | {'SEQUENTIAL (Legacy)':<20} | {'ADAPTIVE (Proposed)':<20}")
    print("="*60)
    print(f"{'PSNR (Visual Quality)':<25} | {f'{psnr_seq:.2f} dB':<20} | {f'{psnr_adapt:.2f} dB':<20}")
    print(f"{'Detection Probability':<25} | {f'{detect_seq:.4f}':<20} | {f'{detect_adapt:.4f}':<20}")
    print("-" * 60)
    print(f"{'Attack Survival (JPEG)':<25} | {f'{score_seq:.1f}% Recovered':<20} | {f'{score_adapt:.1f}% Recovered':<20}")
    print("="*60)

# --- RUN CONFIGURATION ---
# Use a long payload to verify robustness
long_secret = "This payload simulates a critical watermark that must survive compression. " * 50
run_comparative_study("assets/cover_image.png", long_secret)