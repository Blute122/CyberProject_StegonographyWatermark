import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import os
import secrets

# --- CORE MODULES ---
from core.steganography_dct import DCTSteganography
from core.crypto import CryptoHandler
from core.watermark import WatermarkHandler
from core.metrics import StegoMetrics
from core.attacks import AttackSimulator
from core.steganalysis import SteganalysisScanner
from core.rsa_manager import RSAManager
from core.video_stego import VideoStego
from core.audio_stego import AudioStego  # <--- NEW IMPORT

class CyberProjectApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hybrid Cybersecurity System (Research Edition)")
        self.root.geometry("900x950")
        
        # Initialize Core Modules
        self.stego = DCTSteganography()
        self.watermarker = WatermarkHandler("assets/watermark.png")
        self.video_stego = VideoStego()
        self.audio_stego = AudioStego()
        
        # UI Styling
        style = ttk.Style()
        style.configure("TButton", padding=6, relief="flat", background="#ccc")
        style.configure("Header.TLabel", font=("Helvetica", 12, "bold"))
        
        # --- TABS ---
        tab_control = ttk.Notebook(root)
        self.tab_keys = ttk.Frame(tab_control)
        self.tab_encrypt = ttk.Frame(tab_control)
        self.tab_decrypt = ttk.Frame(tab_control)
        self.tab_video = ttk.Frame(tab_control)
        self.tab_audio = ttk.Frame(tab_control)   # <--- NEW AUDIO TAB
        self.tab_attack = ttk.Frame(tab_control)
        self.tab_analysis = ttk.Frame(tab_control)
        
        tab_control.add(self.tab_keys, text='🔑 Keys')
        tab_control.add(self.tab_encrypt, text='🛡️ Image Protect')
        tab_control.add(self.tab_decrypt, text='🔍 Image Verify')
        tab_control.add(self.tab_video, text='🎥 Video')
        tab_control.add(self.tab_audio, text='🎵 Audio')  # <--- NEW
        tab_control.add(self.tab_attack, text='⚔️ Attack')
        tab_control.add(self.tab_analysis, text='🕵️ Analysis')
        tab_control.pack(expand=1, fill="both")
        
        self.setup_keys_tab()
        self.setup_encrypt_tab()
        self.setup_decrypt_tab()
        self.setup_video_tab()
        self.setup_audio_tab()
        self.setup_attack_tab()
        self.setup_analysis_tab()

    def log(self, msg, tab="enc"):
        if tab == "enc": target = self.console
        elif tab == "dec": target = self.console_dec
        elif tab == "key": target = self.console_key
        elif tab == "vid": target = self.console_vid
        elif tab == "aud": target = self.console_aud
        elif tab == "atk": target = self.console_atk
        elif tab == "ana": target = self.console_ana
        else: return
        
        target.config(state='normal')
        target.insert(tk.END, msg + "\n")
        target.see(tk.END)
        target.config(state='disabled')

    # --- TAB 1: KEYS ---
    def setup_keys_tab(self):
        frame = self.tab_keys
        ttk.Label(frame, text="Identity Management (RSA-2048)", style="Header.TLabel").pack(pady=15)
        ttk.Button(frame, text="🆕 GENERATE NEW KEY PAIR", command=self.generate_keys).pack(pady=10)
        ttk.Label(frame, text="Keys saved in 'assets/'. Share PUBLIC key only.").pack()
        self.console_key = tk.Text(frame, height=10, width=80, state='disabled', bg="#fdfdfd")
        self.console_key.pack(pady=20)

    def generate_keys(self):
        try:
            pub, priv = RSAManager.generate_keys()
            self.log(f"Success! Public Key: {pub}", "key")
        except Exception as e: self.log(f"Error: {e}", "key")

    # --- TAB 2: IMAGE PROTECT ---
    def setup_encrypt_tab(self):
        frame = self.tab_encrypt
        ttk.Label(frame, text="1. Cover Image", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Browse Image", command=self.load_image).pack()
        self.lbl_file = ttk.Label(frame, text="None", foreground="blue"); self.lbl_file.pack()

        ttk.Label(frame, text="2. Secret Message", style="Header.TLabel").pack(pady=5)
        self.txt_msg = tk.Text(frame, height=3, width=60); self.txt_msg.pack()

        ttk.Label(frame, text="3. Recipient Public Key", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Load Key (.pem)", command=self.load_pub_key).pack()
        self.lbl_pub_key = ttk.Label(frame, text="None", foreground="green"); self.lbl_pub_key.pack()

        ttk.Button(frame, text="🔒 ENCRYPT & EMBED", command=self.run_pipeline).pack(pady=20)
        self.console = tk.Text(frame, height=10, width=80, state='disabled', bg="#f4f4f4"); self.console.pack()

    def run_pipeline(self):
        if not hasattr(self, 'filepath') or not hasattr(self, 'pub_key_path'): return
        msg = self.txt_msg.get("1.0", tk.END).strip()
        
        try:
            session_key = secrets.token_hex(16) 
            crypto = CryptoHandler(session_key)
            enc_msg = crypto.encrypt(msg)
            enc_session_key = RSAManager.encrypt_session_key(session_key, self.pub_key_path)
            full_payload = enc_session_key + "###KEY_END###" + enc_msg
            
            wm_path = "assets/temp_gui_watermarked.png"
            self.watermarker.embed_watermark(self.filepath, wm_path)
            
            save_path = filedialog.asksaveasfilename(defaultextension=".png")
            if save_path:
                self.stego.dct_embed(wm_path, full_payload, save_path)
                self.watermarker.embed_fragile_seal(save_path, save_path)
                psnr = StegoMetrics.calculate_psnr(self.filepath, save_path)
                self.log(f"Success! PSNR: {psnr:.2f} dB")
                messagebox.showinfo("Success", f"Saved!\nPSNR: {psnr:.2f} dB")
        except Exception as e: self.log(f"Error: {e}")

    # --- TAB 3: IMAGE VERIFY ---
    def setup_decrypt_tab(self):
        frame = self.tab_decrypt
        ttk.Label(frame, text="1. Stego Image", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Browse Image", command=self.load_image_dec).pack()
        self.lbl_file_dec = ttk.Label(frame, text="None", foreground="blue"); self.lbl_file_dec.pack()

        ttk.Label(frame, text="2. Original (Optional)", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Browse Original", command=self.load_original_dec).pack()
        self.lbl_file_orig = ttk.Label(frame, text="None", foreground="red"); self.lbl_file_orig.pack()

        ttk.Label(frame, text="3. Private Key", style="Header.TLabel").pack(pady=5)
        ttk.Button(frame, text="Load Key (.pem)", command=self.load_priv_key).pack()
        self.lbl_priv_key = ttk.Label(frame, text="None", foreground="purple"); self.lbl_priv_key.pack()

        ttk.Button(frame, text="🔓 DECRYPT & VERIFY", command=self.run_verification).pack(pady=20)
        self.console_dec = tk.Text(frame, height=12, width=80, state='disabled', bg="#f4f4f4"); self.console_dec.pack()

    def run_verification(self):
        if not hasattr(self, 'filepath_dec') or not hasattr(self, 'priv_key_path'): return
        try:
            valid, status = self.watermarker.verify_fragile_seal(self.filepath_dec)
            self.log(f"Integrity: {status}", "dec")
            
            full_payload = self.stego.dct_extract(self.filepath_dec)
            if "###KEY_END###" in full_payload:
                enc_key, enc_msg = full_payload.split("###KEY_END###")
                session_key = RSAManager.decrypt_session_key(enc_key, self.priv_key_path)
                crypto = CryptoHandler(session_key)
                dec_msg = crypto.decrypt(enc_msg)
                self.log(f"Secret: {dec_msg}", "dec")
                messagebox.showinfo("Found", dec_msg)
                
            if hasattr(self, 'filepath_orig'):
                out = "assets/extracted_gui_watermark.png"
                self.watermarker.extract_watermark(self.filepath_dec, self.filepath_orig, out)
                cv2.imshow("Watermark", cv2.imread(out)); cv2.waitKey(0); cv2.destroyAllWindows()
        except Exception as e: self.log(f"Error: {e}", "dec")

    # --- TAB 4: VIDEO ---
    def setup_video_tab(self):
        frame = self.tab_video
        ttk.Label(frame, text="Video Steganography", style="Header.TLabel").pack(pady=10)
        ttk.Button(frame, text="Browse Video", command=self.load_video).pack()
        self.lbl_vid = ttk.Label(frame, text="None", foreground="blue"); self.lbl_vid.pack()
        
        self.entry_vid_msg = ttk.Entry(frame, width=60); self.entry_vid_msg.pack(pady=5)
        
        ttk.Button(frame, text="💾 EMBED (Save AVI)", command=self.run_vid_embed).pack(pady=5)
        ttk.Button(frame, text="🔍 EXTRACT", command=self.run_vid_extract).pack(pady=5)
        self.console_vid = tk.Text(frame, height=12, width=80, state='disabled', bg="#f0f8ff"); self.console_vid.pack()

    def run_vid_embed(self):
        if not hasattr(self, 'filepath_vid'): return
        save_path = filedialog.asksaveasfilename(defaultextension=".avi")
        if save_path:
            try:
                count = self.video_stego.embed_in_video(self.filepath_vid, self.entry_vid_msg.get(), save_path)
                self.log(f"Embedded in {count} frames.", "vid")
                messagebox.showinfo("Success", "Video Saved!")
            except Exception as e: self.log(f"Error: {e}", "vid")

    def run_vid_extract(self):
        if not hasattr(self, 'filepath_vid'): return
        try:
            res = self.video_stego.extract_from_video(self.filepath_vid)
            for r in res: self.log(f"Frame {r['frame']}: {r['message']}", "vid")
        except Exception as e: self.log(f"Error: {e}", "vid")

    # --- TAB 5: AUDIO (NEW) ---
    def setup_audio_tab(self):
        frame = self.tab_audio
        ttk.Label(frame, text="Audio Steganography (WAV)", style="Header.TLabel").pack(pady=10)
        
        ttk.Button(frame, text="Browse Audio (.wav)", command=self.load_audio).pack()
        self.lbl_aud = ttk.Label(frame, text="None", foreground="blue"); self.lbl_aud.pack()
        
        self.entry_aud_msg = ttk.Entry(frame, width=60); self.entry_aud_msg.pack(pady=5)
        
        ttk.Button(frame, text="💾 EMBED", command=self.run_aud_embed).pack(pady=5)
        ttk.Button(frame, text="🔊 EXTRACT", command=self.run_aud_extract).pack(pady=5)
        self.console_aud = tk.Text(frame, height=12, width=80, state='disabled', bg="#fff0f5"); self.console_aud.pack()

    def run_aud_embed(self):
        if not hasattr(self, 'filepath_aud'): return
        save_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV", "*.wav")])
        if save_path:
            try:
                bits = self.audio_stego.embed_audio(self.filepath_aud, self.entry_aud_msg.get(), save_path)
                self.log(f"Hidden {bits} bits.", "aud")
                messagebox.showinfo("Success", "Audio Saved!")
            except Exception as e: self.log(f"Error: {e}", "aud")

    def run_aud_extract(self):
        if not hasattr(self, 'filepath_aud'): return
        try:
            msg = self.audio_stego.extract_audio(self.filepath_aud)
            self.log(f"Message: {msg}", "aud")
        except Exception as e: self.log(f"Error: {e}", "aud")

    # --- TAB 6 & 7: ATTACK & ANALYSIS ---
    def setup_attack_tab(self):
        frame = self.tab_attack
        ttk.Button(frame, text="Browse Stego", command=self.load_image_attack).pack()
        self.lbl_atk = ttk.Label(frame, text="None"); self.lbl_atk.pack()
        ttk.Button(frame, text="Browse Original", command=self.load_original_atk).pack()
        self.lbl_atk_orig = ttk.Label(frame, text="None"); self.lbl_atk_orig.pack()
        
        ttk.Button(frame, text="JPEG", command=lambda: self.run_attack("jpeg")).pack()
        ttk.Button(frame, text="Noise", command=lambda: self.run_attack("noise")).pack()
        ttk.Button(frame, text="Crop", command=lambda: self.run_attack("crop")).pack()
        self.console_atk = tk.Text(frame, height=10, width=80, state='disabled'); self.console_atk.pack()

    def run_attack(self, t):
        if not hasattr(self, 'filepath_atk'): return
        try:
            if t=="jpeg": o=AttackSimulator.apply_jpeg_compression(self.filepath_atk)
            elif t=="noise": o=AttackSimulator.apply_noise(self.filepath_atk)
            else: o=AttackSimulator.apply_crop(self.filepath_atk)
            self.log(f"Attack: {o}", "atk")
            self.watermarker.extract_watermark(o, self.filepath_atk_orig, "assets/rec.png")
            cv2.imshow("Rec", cv2.imread("assets/rec.png")); cv2.waitKey(0); cv2.destroyAllWindows()
        except Exception as e: self.log(f"Error: {e}", "atk")

    def setup_analysis_tab(self):
        frame = self.tab_analysis
        ttk.Button(frame, text="Browse Image", command=self.load_image_ana).pack()
        self.lbl_ana = ttk.Label(frame, text="None"); self.lbl_ana.pack()
        ttk.Button(frame, text="SCAN", command=self.run_analysis).pack()
        self.lbl_threat = ttk.Label(frame, text="WAITING"); self.lbl_threat.pack()
        self.console_ana = tk.Text(frame, height=10, width=80, state='disabled'); self.console_ana.pack()

    def run_analysis(self):
        if not hasattr(self, 'filepath_ana'): return
        p = SteganalysisScanner.perform_chi_square_test(self.filepath_ana) * 100
        self.log(f"LSB Prob: {p:.2f}%", "ana")
        self.lbl_threat.config(text=f"Threat: {p:.1f}%")

    # --- LOADERS ---
    def load_image(self): f=filedialog.askopenfilename(); self.filepath=f; self.lbl_file.config(text=os.path.basename(f))
    def load_pub_key(self): f=filedialog.askopenfilename(); self.pub_key_path=f; self.lbl_pub_key.config(text=os.path.basename(f))
    def load_image_dec(self): f=filedialog.askopenfilename(); self.filepath_dec=f; self.lbl_file_dec.config(text=os.path.basename(f))
    def load_original_dec(self): f=filedialog.askopenfilename(); self.filepath_orig=f; self.lbl_file_orig.config(text=os.path.basename(f))
    def load_priv_key(self): f=filedialog.askopenfilename(); self.priv_key_path=f; self.lbl_priv_key.config(text=os.path.basename(f))
    def load_video(self): f=filedialog.askopenfilename(); self.filepath_vid=f; self.lbl_vid.config(text=os.path.basename(f))
    def load_audio(self): f=filedialog.askopenfilename(filetypes=[("WAV","*.wav")]); self.filepath_aud=f; self.lbl_aud.config(text=os.path.basename(f))
    def load_image_attack(self): f=filedialog.askopenfilename(); self.filepath_atk=f; self.lbl_atk.config(text=os.path.basename(f))
    def load_original_atk(self): f=filedialog.askopenfilename(); self.filepath_atk_orig=f; self.lbl_atk_orig.config(text=os.path.basename(f))
    def load_image_ana(self): f=filedialog.askopenfilename(); self.filepath_ana=f; self.lbl_ana.config(text=os.path.basename(f))

if __name__ == "__main__":
    root = tk.Tk()
    app = CyberProjectApp(root)
    root.mainloop()