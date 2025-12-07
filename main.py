from core.steganography_dct import DCTSteganography
from core.crypto import CryptoHandler
from core.watermark import WatermarkHandler
from core.metrics import StegoMetrics
from core.analyzer import TextureAnalyzer  # <--- NEW IMPORT
import os
import cv2

def main():
    print("--- Hybrid Cybersecurity Project: RESEARCH ARCHITECTURE ---")
    
    # --- SETUP ---
    password = "MySuperSecretPassword123!" 
    crypto = CryptoHandler(key=password)
    stego = DCTSteganography()
    watermarker = WatermarkHandler("assets/watermark.png")
    analyzer = TextureAnalyzer()  # <--- Initialize Analyzer
    
    original_image = "assets/cover_image.png"
    watermarked_image = "assets/temp_watermarked.png"
    final_output = "assets/final_hybrid_secure.png"
    extracted_wm_path = "assets/extracted_watermark.png"
    
    secret_message = "TOP SECRET: The hybrid system is operational."

    # --- STEP 0: AI TEXTURE ANALYSIS (The "Brains") ---
    print("\n[STEP 0] Analyzing Image Texture (AI Module)...")
    try:
        # This mimics the "AI Texture Analyzer" box in your diagram.
        # It calculates where it is safe to hide data (edges/textures).
        texture_map, safe_pixels = analyzer.analyze_texture(original_image)
        
        print(f"    > Analysis Complete.")
        print(f"    > Safe Embedding Area (High Entropy): {safe_pixels} pixels found.")
        print(f"    > Visualizing the complexity map...")
        
        # Show the map to the user (Close window to proceed)
        analyzer.visualize_map(original_image)
        
    except Exception as e:
        print(f"    [!] Analysis Error: {e}")
        return

    # --- STEP 1: DUAL WATERMARKING (Robust Layer) ---
    # According to the diagram, we apply Robust Watermark first.
    print("\n[STEP 1] Applying Robust Watermark (Ownership Layer)...")
    try:
        watermarker.embed_watermark(original_image, watermarked_image)
    except Exception as e:
        print(f"Watermark Error: {e}")
        return

    # --- STEP 2: ENCRYPTION & EMBEDDING ---
    print("\n[STEP 2] Encrypting & Hiding Message (Privacy Layer)...")
    try:
        # A. Adaptive Steganography
        encrypted_msg = crypto.encrypt(secret_message)
        stego.dct_embed(watermarked_image, encrypted_msg, final_output)
        
        # B. Apply Fragile Seal (NEW)
        # We overwrite final_output with the "Sealed" version
        watermarker.embed_fragile_seal(final_output, final_output)
        print(f"[+] Fragile Tamper-Seal Applied.")
        
    except Exception as e:
        print(f"Steganography Error: {e}")
        return

    # --- STEP 3: RECEIVER VALIDATION ---
    print("\n[STEP 3] Receiver: Verifying Data...")
    
    # 3A. Check Integrity FIRST (NEW)
    print("   > Checking Tamper Seal...")
    is_valid, status_msg = watermarker.verify_fragile_seal(final_output)
    print(f"     {status_msg}")
    
    if not is_valid:
        print("     [WARN] Proceeding with caution (Image may be corrupted)...")

    # 3B. Extract Message
    print("   > Extracting Secret Message...")
    try:
        watermarker.extract_watermark(final_output, original_image, extracted_wm_path)
        print(f"     [SUCCESS] Check {extracted_wm_path} to see the recovered logo.")
    except Exception as e:
        print(f"     [FAIL] Watermark error: {e}")

    # --- STEP 4: SCIENTIFIC VALIDATION ---
    print("\n[STEP 4] Scientific Validation (Steganalysis)...")
    try:
        psnr_val = StegoMetrics.calculate_psnr(original_image, final_output)
        print(f"    > PSNR Value: {psnr_val:.2f} dB")
        
        if psnr_val > 40:
            print("    > [PASS] Imperceptibility Standard Met.")
        elif psnr_val > 35:
            print("    > [PASS] Acceptable Quality.")
        else:
            print("    > [WARN] Low Quality - Detectable!")
            
    except Exception as e:
        print(f"    > Metric Error: {e}")

if __name__ == "__main__":
    main()