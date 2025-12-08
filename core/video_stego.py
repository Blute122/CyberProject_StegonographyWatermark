import cv2
import os
import numpy as np
from core.steganography_dct import DCTSteganography
from core.watermark import WatermarkHandler

class VideoStego:
    def __init__(self):
        self.stego = DCTSteganography()
        self.watermarker = WatermarkHandler("assets/watermark.png")
        
    def embed_in_video(self, video_path, message, output_path, frame_interval=100):
        if not os.path.exists(video_path): raise ValueError(f"Input video not found.")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): raise ValueError("Could not open input video.")
        
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps    = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # --- FIX 1: Use HuffYUV (HFYU) Codec ---
        # Best balance of compatibility and lossless storage on Windows.
        fourcc = cv2.VideoWriter_fourcc(*'HFYU') 
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # --- FIX 2: Signal Boost ---
        original_Q = self.stego.Q
        self.stego.Q = 60
        
        frame_idx = 0
        embedded_count = 0
        
        print(f"[*] Starting Video Embedding (HFYU/Q=60) - {total_frames} frames...")
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if frame_idx % frame_interval == 0:
                print(f"    > Embedding data in Frame {frame_idx}...")
                temp_out = f"assets/temp_frame_{frame_idx}_stego.png"
                
                try:
                    self.watermarker.embed_watermark_to_frame(frame, temp_out)
                    
                    # --- FIX 3: Disable Adaptive Mode (use_adaptive=False) ---
                    # We force sequential embedding to avoid sync errors.
                    self.stego.dct_embed(temp_out, message, temp_out, use_adaptive=False)
                    
                    self.watermarker.embed_fragile_seal(temp_out, temp_out)
                    frame = cv2.imread(temp_out)
                    embedded_count += 1
                    
                    if os.path.exists(temp_out): os.remove(temp_out)
                except Exception as e:
                    print(f"    [!] Error processing frame {frame_idx}: {e}")

            out.write(frame)
            frame_idx += 1
            
        self.stego.Q = original_Q
        cap.release()
        out.release()
        print(f"[*] Video saved to {output_path}")
        return embedded_count

    def extract_from_video(self, video_path, frame_interval=100):
        if not os.path.exists(video_path): raise ValueError(f"File not found.")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened(): raise ValueError("Could not open video file.")
        
        frame_idx = 0
        results = []
        
        original_Q = self.stego.Q
        self.stego.Q = 60
        
        print(f"[*] Scanning Video for Secrets...")
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            if frame_idx % frame_interval == 0:
                print(f"    > Scanning Frame {frame_idx}...")
                temp_frame = f"assets/temp_extract_{frame_idx}.png"
                cv2.imwrite(temp_frame, frame)
                
                try:
                    valid, status = self.watermarker.verify_fragile_seal(temp_frame)
                    seal_status = "✅ Valid" if valid else "❌ Broken"
                    
                    # --- FIX 3: Disable Adaptive Mode here too ---
                    msg = self.stego.dct_extract(temp_frame, use_adaptive=False)
                    
                    if "No hidden message" not in msg:
                        results.append({"frame": frame_idx, "seal": seal_status, "message": msg})
                        print(f"      [FOUND] Frame {frame_idx}: {msg} ({seal_status})")
                    else:
                        print(f"      [MISS] Frame {frame_idx} empty.")
                        
                except Exception as e:
                    print(f"Error: {e}")
                    
                if os.path.exists(temp_frame): os.remove(temp_frame)
                
            frame_idx += 1
            
        self.stego.Q = original_Q
        cap.release()
        return results