import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import secrets  # For generating random AES keys

# --- CORE MODULES ---
# Ensure all these files exist in your 'core/' folder
from core.steganography_dct import DCTSteganography
from core.crypto import CryptoHandler
from core.watermark import WatermarkHandler
from core.metrics import StegoMetrics
from core.attacks import AttackSimulator
from core.steganalysis import SteganalysisScanner
from core.rsa_manager import RSAManager
from core.video_stego import VideoStego  # <--- NEW IMPORT

class CyberProjectApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hybrid Cybersecurity System (Research Edition)")
        self.root.geometry("900x950")  # Increased size for video tab
        
        # Initialize Core Modules
        self.stego = DCTSteganography()
        self.watermarker = WatermarkHandler("assets/watermark.png")
        self.video_stego = VideoStego()
        
        # UI Styling
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        
        # --- TABS ---
        tab_control = ttk.Notebook(root)
        self.tab_keys = ttk.Frame(tab_control)
        self.tab_encrypt = ttk.Frame(tab_control)
        self.tab_decrypt = ttk.Frame(tab_control)
        self.tab_video = ttk.Frame(tab_control)   # <--- NEW VIDEO TAB
        self.tab_attack = ttk.Frame(tab_control)
        self.tab_analysis = ttk.Frame(tab_control)
        
        tab_control.add(self.tab_keys, text='🔑 Keys')
        tab_control.add(self.tab_encrypt, text='🛡️ Image Protect')
        tab_control.add(self.tab_decrypt, text='🔍 Image Verify')
        tab_control.add(self.tab_video, text='🎥 Video Stego')  # <--- NEW
        tab_control.add(self.tab_attack, text='⚔️ Attack Sim')
        tab_control.add(self.tab_analysis, text='🕵️ Steganalysis')
        tab_control.pack(expand=1, fill="both")
        
        # Setup Layouts
        self.setup_keys_tab()
        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_video_tab()
        self.setup_attack_tab()
        self.setup_analysis_tab()

    def log(self, msg, tab="enc"):
        if tab == "enc": target = self.console
        elif tab == "dec": target = self.console_dec
        elif tab == "key": target = self.console_key
        elif tab == "vid": target = self.console_vid
        elif tab == "atk": target = self.console_atk
        elif tab == "ana": target = self.console_ana
        else: return
        
        target.config(state='normal')
        target.insert(tk.END, msg + "\n")
        target.see(tk.END)
        target.config(state='disabled')

    # ==========================================
    # TAB 1: KEY MANAGEMENT (RSA)
    # ==========================================
    def setup_keys_tab(self):
        frame = self.tab_keys
        ttk.Label(frame, text="Identity Management (RSA-2048)", style="Header.TLabel").pack(pady=15)
        
        ttk.Button(frame, text="🆕 GENERATE NEW KEY PAIR", command=self.generate_keys).pack(pady=10)
        
        ttk.Label(frame, text="Keys will be saved in 'assets/' folder.").pack()
        ttk.Label(frame, text="Share Public Key (.pem) with senders. Keep Private Key SAFE.", foreground="red").pack()
        
        self.console_key = tk.Text(frame, height=10, width=80, state='disabled', bg="#fdfdfd")
        self.console_key.pack(pady=20)

    def generate_keys(self):
        try:
            pub, priv = RSAManager.generate_keys()
            self.log(f"Keys Generated Successfully!", "key")
            self.log(f"Public Key: {pub}", "key")
            self.log(f"Private Key: {priv}", "key")
            messagebox.showinfo("Success", "Keys generated in 'assets/' folder.")
        except Exception as e:
            self.log(f"Error: {e}", "key")

    # ==========================================
    # TAB 2: IMAGE PROTECTION (Hybrid)
    # ==========================================
    def setup_encrypt_tab(self):
        frame = self.tab_encrypt
        # Image
        ttk.Label(frame, text="1. Cover Image", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Browse Image", command=self.load_image).pack()
        self.lbl_file = ttk.Label(frame, text="None", foreground="blue")
        self.lbl_file.pack()

        # Message
        ttk.Label(frame, text="2. Secret Message", style="Header.TLabel").pack(pady=5)
        self.txt_msg = tk.Text(frame, height=3, width=60)
        self.txt_msg.pack()

        # Recipient Key
        ttk.Label(frame, text="3. Recipient's Public Key", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Load Public Key (.pem)", command=self.load_pub_key).pack()
        self.lbl_pub_key = ttk.Label(frame, text="None", foreground="green")
        self.lbl_pub_key.pack()

        ttk.Button(frame, text="🔒 ENCRYPT & EMBED", command=self.run_pipeline).pack(pady=20)
        self.console = tk.Text(frame, height=10, width=80, state='disabled', bg="#f4f4f4")
        self.console.pack()

    def run_pipeline(self):
        if not hasattr(self, 'filepath') or not hasattr(self, 'pub_key_path'): 
            return messagebox.showerror("Error", "Missing Image or Public Key.")
        msg = self.txt_msg.get("1.0", tk.END).strip()
        if not msg: return messagebox.showerror("Error", "No message.")

        self.log("--- STARTING HYBRID RSA PIPELINE ---")
        
        try:
            # 1. Generate Random AES Session Key
            session_key = secrets.token_hex(16) 
            self.log(f"[1] Generated Session Key: {session_key[:6]}...")
            
            # 2. Encrypt Message with AES
            crypto = CryptoHandler(session_key)
            enc_msg = crypto.encrypt(msg)
            
            # 3. Encrypt Session Key with RSA
            self.log("[2] Encrypting Session Key (RSA)...")
            enc_session_key = RSAManager.encrypt_session_key(session_key, self.pub_key_path)
            
            # 4. Combine Payload
            full_payload = enc_session_key + "###KEY_END###" + enc_msg
            
            # 5. Pipeline Execution
            wm_path = "assets/temp_gui_watermarked.png"
            self.watermarker.embed_watermark(self.filepath, wm_path)
            
            save_path = filedialog.asksaveasfilename(defaultextension=".png")
            if not save_path: return
            
            self.log(f"[3] Embedding Hybrid Payload ({len(full_payload)} chars)...")
            self.stego.dct_embed(wm_path, full_payload, save_path)
            
            self.watermarker.embed_fragile_seal(save_path, save_path)
            
            psnr = StegoMetrics.calculate_psnr(self.filepath, save_path)
            self.log(f"[RESULT] PSNR: {psnr:.2f} dB. Secure File Created.")
            messagebox.showinfo("Success", f"File Saved!\nPSNR: {psnr:.2f} dB")
            
        except Exception as e: self.log(f"ERROR: {e}")

    # ==========================================
    # TAB 3: IMAGE VERIFICATION
    # ==========================================
    def setup_decrypt_tab(self):
        frame = self.tab_decrypt
        # Stego File
        ttk.Label(frame, text="1. Stego Image", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Browse Stego File", command=self.load_image_dec).pack()
        self.lbl_file_dec = ttk.Label(frame, text="None", foreground="blue")
        self.lbl_file_dec.pack()

        # Original (Watermark)
        ttk.Label(frame, text="2. Original Image (For Watermark)", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Browse Original", command=self.load_original_dec).pack()
        self.lbl_file_orig = ttk.Label(frame, text="None", foreground="red")
        self.lbl_file_orig.pack()
        
        # My Private Key
        ttk.Label(frame, text="3. My Private Key", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Load Private Key (.pem)", command=self.load_priv_key).pack()
        self.lbl_priv_key = ttk.Label(frame, text="None", foreground="purple")
        self.lbl_priv_key.pack()
        
        ttk.Button(frame, text="🔓 DECRYPT & VERIFY", command=self.run_verification).pack(pady=20)
        self.console_dec = tk.Text(frame, height=12, width=80, state='disabled', bg="#f4f4f4")
        self.console_dec.pack()

    def run_verification(self):
        if not hasattr(self, 'filepath_dec') or not hasattr(self, 'priv_key_path'): 
            return messagebox.showerror("Error", "Missing Image or Private Key.")
        
        self.log("--- STARTING RSA DECRYPTION ---", "dec")
        
        try:
            # 1. Integrity
            is_valid, status = self.watermarker.verify_fragile_seal(self.filepath_dec)
            if not is_valid: self.log("    [WARN] Integrity Seal Broken!", "dec")
            else: self.log("    [PASS] Integrity Verified.", "dec")

            # 2. Extract Full Payload
            self.log("[1] Extracting Payload...", "dec")
            full_payload = self.stego.dct_extract(self.filepath_dec)
            
            if "###KEY_END###" not in full_payload:
                self.log("    FAILED: RSA header missing.", "dec")
                return
                
            # 3. Split Payload
            enc_session_key, enc_msg = full_payload.split("###KEY_END###")
            
            # 4. Decrypt RSA Key
            self.log("[2] Decrypting AES Session Key (RSA)...", "dec")
            session_key = RSAManager.decrypt_session_key(enc_session_key, self.priv_key_path)
            self.log(f"    Key Recovered: {session_key[:6]}...", "dec")
            
            # 5. Decrypt Message
            crypto = CryptoHandler(session_key)
            dec_msg = crypto.decrypt(enc_msg)
            
            self.log(f"\n[SECRET]: {dec_msg}\n", "dec")
            messagebox.showinfo("Secret Found", dec_msg)
            
            # 6. Watermark Check
            if hasattr(self, 'filepath_orig'):
                self.log("[3] Extracting Watermark...", "dec")
                out_wm = "assets/extracted_gui_watermark.png"
                self.watermarker.extract_watermark(self.filepath_dec, self.filepath_orig, out_wm)
                cv2.imshow("Watermark", cv2.imread(out_wm))
                cv2.waitKey(0); cv2.destroyAllWindows()
                
        except Exception as e: self.log(f"ERROR: {e}", "dec")

    # ==========================================
    # TAB 4: VIDEO STEGANOGRAPHY (NEW)
    # ==========================================
    def setup_video_tab(self):
        frame = self.tab_video
        ttk.Label(frame, text="Multi-Modal Video Steganography", style="Header.TLabel").pack(pady=10)
        
        # Input 1: Video File
        ttk.Button(frame, text="Browse Video File (.mp4, .avi)", command=self.load_video).pack()
        self.lbl_vid = ttk.Label(frame, text="No video selected", foreground="blue")
        self.lbl_vid.pack()
        
        # Input 2: Message
        ttk.Label(frame, text="Secret Message (Embedded every 100 frames)", style="Header.TLabel").pack(pady=5)
        self.entry_vid_msg = ttk.Entry(frame, width=60)
        self.entry_vid_msg.pack()
        
        # Actions
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="💾 EMBED INTO VIDEO", command=self.run_video_embed).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="🔍 EXTRACT FROM VIDEO", command=self.run_video_extract).grid(row=0, column=1, padx=10)
        
        self.console_vid = tk.Text(frame, height=15, width=80, state='disabled', bg="#f0f8ff")
        self.console_vid.pack(pady=10)

    def run_video_embed(self):
        if not hasattr(self, 'filepath_vid'): return messagebox.showerror("Error", "Select Video.")
        msg = self.entry_vid_msg.get()
        if not msg: return messagebox.showerror("Error", "Enter message.")
        
        self.log("--- STARTING VIDEO EMBEDDING ---", "vid")
        self.log(f"Target: {os.path.basename(self.filepath_vid)}", "vid")
        self.log("Output: Lossless .avi (FFV1 codec)", "vid")
        
        save_path = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI Video", "*.avi")])
        if not save_path: return
        
        try:
            count = self.video_stego.embed_in_video(self.filepath_vid, msg, save_path)
            self.log(f"[SUCCESS] Embedded in {count} frames.", "vid")
            self.log(f"Saved to: {save_path}", "vid")
            messagebox.showinfo("Success", f"Video Saved!\nEmbedded in {count} frames.")
        except Exception as e:
            self.log(f"ERROR: {e}", "vid")

    def run_video_extract(self):
        if not hasattr(self, 'filepath_vid'): return messagebox.showerror("Error", "Select Video.")
        
        self.log("--- STARTING VIDEO EXTRACTION ---", "vid")
        try:
            results = self.video_stego.extract_from_video(self.filepath_vid)
            if not results:
                self.log("No data found.", "vid")
            else:
                self.log(f"[FOUND] {len(results)} Hidden Messages:", "vid")
                for res in results:
                    self.log(f"  Frame {res['frame']}: {res['message']} ({res['seal']})", "vid")
                messagebox.showinfo("Success", f"Found {len(results)} messages!")
        except Exception as e:
            self.log(f"ERROR: {e}", "vid")

    # ==========================================
    # TAB 5: ATTACK SIMULATION
    # ==========================================
    def setup_attack_tab(self):
        frame = self.tab_attack
        ttk.Label(frame, text="Attack Simulation", style="Header.TLabel").pack(pady=10)
        
        ttk.Button(frame, text="Browse Stego Image", command=self.load_image_attack).pack()
        self.lbl_file_atk = ttk.Label(frame, text="None", foreground="blue")
        self.lbl_file_atk.pack()

        ttk.Button(frame, text="Browse Original (Proof)", command=self.load_original_atk).pack()
        self.lbl_file_atk_orig = ttk.Label(frame, text="None", foreground="red")
        self.lbl_file_atk_orig.pack()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="📉 JPEG Compression", command=lambda: self.run_attack("jpeg")).grid(row=0,column=0, padx=5)
        ttk.Button(btn_frame, text="🌫️ Noise Injection", command=lambda: self.run_attack("noise")).grid(row=0,column=1, padx=5)
        ttk.Button(btn_frame, text="✂️ Crop Attack", command=lambda: self.run_attack("crop")).grid(row=0,column=2, padx=5)
        
        self.console_atk = tk.Text(frame, height=10, width=80, state='disabled', bg="#ffecec")
        self.console_atk.pack(pady=10)

    def run_attack(self, attack_type):
        if not hasattr(self, 'filepath_atk') or not hasattr(self, 'filepath_atk_orig'): 
            return messagebox.showerror("Error", "Select both images.")
        
        self.log(f"--- SIMULATING {attack_type.upper()} ---", "atk")
        try:
            if attack_type == "jpeg": out_path = AttackSimulator.apply_jpeg_compression(self.filepath_atk)
            elif attack_type == "noise": out_path = AttackSimulator.apply_noise(self.filepath_atk)
            elif attack_type == "crop": out_path = AttackSimulator.apply_crop(self.filepath_atk)
            self.log(f"[1] Applied -> {out_path}", "atk")
            
            self.log("[2] Checking Watermark Survival...", "atk")
            rec_wm = "assets/recovered_from_attack.png"
            self.watermarker.extract_watermark(out_path, self.filepath_atk_orig, rec_wm)
            self.log(f"    Extracted to {rec_wm}", "atk")
            
            img = cv2.imread(rec_wm)
            cv2.imshow(f"Survived {attack_type}?", img)
            cv2.waitKey(0); cv2.destroyAllWindows()
        except Exception as e: self.log(f"ERROR: {e}", "atk")

    # ==========================================
    # TAB 6: STEGANALYSIS
    # ==========================================
    def setup_analysis_tab(self):
        frame = self.tab_analysis
        ttk.Label(frame, text="Steganalysis Tool (Chi-Square)", style="Header.TLabel").pack(pady=15)
        
        ttk.Button(frame, text="Browse Suspicious Image", command=self.load_image_ana).pack()
        self.lbl_file_ana = ttk.Label(frame, text="None", foreground="blue")
        self.lbl_file_ana.pack()
        
        ttk.Button(frame, text="🔍 SCAN FOR HIDDEN DATA", command=self.run_analysis).pack(pady=20)
        
        self.lbl_threat = ttk.Label(frame, text="Threat Level: WAITING", font=("Helvetica", 14, "bold"))
        self.lbl_threat.pack(pady=10)
        
        self.console_ana = tk.Text(frame, height=12, width=80, state='disabled', bg="#e6f3ff")
        self.console_ana.pack(pady=10)

    def run_analysis(self):
        if not hasattr(self, 'filepath_ana'): return messagebox.showerror("Error", "Select Image.")
        self.log("--- STARTING FORENSIC SCAN ---", "ana")
        try:
            self.log("[1] Calculating Chi-Square Statistic...", "ana")
            prob = SteganalysisScanner.perform_chi_square_test(self.filepath_ana)
            percent = prob * 100
            self.log(f"    Probability of LSB Steganography: {percent:.2f}%", "ana")
            
            if percent > 90: self.lbl_threat.config(text="Threat Level: CRITICAL 🔴", foreground="red")
            elif percent > 50: self.lbl_threat.config(text="Threat Level: SUSPICIOUS 🟠", foreground="orange")
            else:
                self.lbl_threat.config(text="Threat Level: LOW 🟢", foreground="green")
                self.log("    [PASS] No LSB patterns detected.", "ana")
        except Exception as e: self.log(f"ERROR: {e}", "ana")

    # ==========================================
    # FILE LOADERS
    # ==========================================
    def load_image(self): f=filedialog.askopenfilename(); self.filepath=f; self.lbl_file.config(text=os.path.basename(f))
    def load_pub_key(self): f=filedialog.askopenfilename(filetypes=[("PEM","*.pem")]); self.pub_key_path=f; self.lbl_pub_key.config(text=os.path.basename(f))
    def load_image_dec(self): f=filedialog.askopenfilename(); self.filepath_dec=f; self.lbl_file_dec.config(text=os.path.basename(f))
    def load_original_dec(self): f=filedialog.askopenfilename(); self.filepath_orig=f; self.lbl_file_orig.config(text=os.path.basename(f))
    def load_priv_key(self): f=filedialog.askopenfilename(filetypes=[("PEM","*.pem")]); self.priv_key_path=f; self.lbl_priv_key.config(text=os.path.basename(f))
    def load_image_attack(self): f=filedialog.askopenfilename(); self.filepath_atk=f; self.lbl_file_atk.config(text=os.path.basename(f))
    def load_original_atk(self): f=filedialog.askopenfilename(); self.filepath_atk_orig=f; self.lbl_file_atk_orig.config(text=os.path.basename(f))
    def load_image_ana(self): f=filedialog.askopenfilename(); self.filepath_ana=f; self.lbl_file_ana.config(text=os.path.basename(f))
    def load_video(self): f=filedialog.askopenfilename(filetypes=[("Video","*.mp4;*.avi")]); self.filepath_vid=f; self.lbl_vid.config(text=os.path.basename(f))

if __name__ == "__main__":
    root = tk.Tk()
    app = CyberProjectApp(root)
    root.mainloop()