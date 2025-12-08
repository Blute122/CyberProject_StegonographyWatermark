import sys
import os
import cv2
import secrets
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QPushButton, QLabel, 
                               QLineEdit, QTextEdit, QFileDialog, QMessageBox, 
                               QProgressBar, QGroupBox, QStatusBar)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont, QPalette, QColor

# --- CORE MODULES ---
from core.steganography_dct import DCTSteganography
from core.crypto import CryptoHandler
from core.watermark import WatermarkHandler
from core.metrics import StegoMetrics
from core.attacks import AttackSimulator
from core.steganalysis import SteganalysisScanner
from core.rsa_manager import RSAManager
from core.video_stego import VideoStego
from core.audio_stego import AudioStego # <--- NEW IMPORT

class ModernCyberApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Hybrid Cybersecurity Suite (Research Edition)")
        self.setGeometry(100, 100, 1100, 850)
        self.apply_dark_theme()
        
        # Modules
        self.stego = DCTSteganography()
        self.watermarker = WatermarkHandler("assets/watermark.png")
        self.video_stego = VideoStego()
        self.audio_stego = AudioStego()
        
        # State
        self.filepath = ""; self.pub_key_path = ""
        self.filepath_dec = ""; self.priv_key_path = ""; self.filepath_orig = ""
        self.filepath_vid = ""; self.filepath_aud = ""
        self.filepath_atk = ""; self.filepath_atk_orig = ""
        self.filepath_ana = ""

        # Layout
        main_widget = QWidget(); self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        header = QLabel("🛡️ Hybrid Steganography & Watermarking System")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("color: #4CAF50; margin-bottom: 10px;")
        layout.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { height: 40px; width: 130px; }")
        layout.addWidget(self.tabs)
        
        self.create_keys_tab()
        self.create_protect_tab()
        self.create_verify_tab()
        self.create_video_tab()
        self.create_audio_tab() # <--- NEW
        self.create_attack_tab()
        self.create_analysis_tab()
        
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.status.showMessage("System Ready.")

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.setPalette(palette)

    # --- TAB 1: KEYS ---
    def create_keys_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        layout.addWidget(QLabel("RSA-2048 Identity Management"))
        btn = QPushButton("🆕 Generate New Key Pair")
        btn.clicked.connect(self.generate_keys)
        layout.addWidget(btn)
        self.log_keys = QTextEdit(); layout.addWidget(self.log_keys)
        tab.setLayout(layout); self.tabs.addTab(tab, "🔑 Keys")

    def generate_keys(self):
        try:
            pub, priv = RSAManager.generate_keys()
            self.log_keys.append(f"Saved: {pub}")
        except Exception as e: self.log_keys.append(str(e))

    # --- TAB 2: PROTECT ---
    def create_protect_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        
        h1 = QHBoxLayout()
        self.lbl_prot_img = QLabel("No Image")
        btn1 = QPushButton("Browse Image"); btn1.clicked.connect(lambda: self.load_file(self.lbl_prot_img, "img", "prot_img"))
        h1.addWidget(btn1); h1.addWidget(self.lbl_prot_img)
        layout.addLayout(h1)
        
        h2 = QHBoxLayout()
        self.lbl_prot_key = QLabel("No Public Key")
        btn2 = QPushButton("Browse Public Key"); btn2.clicked.connect(lambda: self.load_file(self.lbl_prot_key, "pem", "prot_key"))
        h2.addWidget(btn2); h2.addWidget(self.lbl_prot_key)
        layout.addLayout(h2)
        
        self.txt_prot_msg = QTextEdit(); self.txt_prot_msg.setMaximumHeight(80); layout.addWidget(self.txt_prot_msg)
        
        btn_run = QPushButton("🔒 Encrypt & Embed"); btn_run.setStyleSheet("background-color: #4CAF50;")
        btn_run.clicked.connect(self.run_protect); layout.addWidget(btn_run)
        
        self.log_prot = QTextEdit(); layout.addWidget(self.log_prot)
        tab.setLayout(layout); self.tabs.addTab(tab, "🛡️ Protect")

    def run_protect(self):
        if not self.filepath or not self.pub_key_path: return
        msg = self.txt_prot_msg.toPlainText()
        try:
            session_key = secrets.token_hex(16)
            crypto = CryptoHandler(session_key)
            enc_msg = crypto.encrypt(msg)
            enc_key = RSAManager.encrypt_session_key(session_key, self.pub_key_path)
            full_payload = enc_key + "###KEY_END###" + enc_msg
            
            wm_path = "assets/temp_qt_wm.png"
            self.watermarker.embed_watermark(self.filepath, wm_path)
            
            save_path, _ = QFileDialog.getSaveFileName(self, "Save", "", "PNG (*.png)")
            if save_path:
                self.stego.dct_embed(wm_path, full_payload, save_path)
                self.watermarker.embed_fragile_seal(save_path, save_path)
                psnr = StegoMetrics.calculate_psnr(self.filepath, save_path)
                self.log_prot.append(f"Success! PSNR: {psnr:.2f} dB")
                QMessageBox.information(self, "Done", "File Saved!")
        except Exception as e: self.log_prot.append(str(e))

    # --- TAB 3: VERIFY ---
    def create_verify_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        
        h1 = QHBoxLayout()
        self.lbl_ver_img = QLabel("No Stego Image")
        btn1 = QPushButton("Browse Stego"); btn1.clicked.connect(lambda: self.load_file(self.lbl_ver_img, "img", "ver_img"))
        h1.addWidget(btn1); h1.addWidget(self.lbl_ver_img)
        layout.addLayout(h1)
        
        h2 = QHBoxLayout()
        self.lbl_ver_key = QLabel("No Private Key")
        btn2 = QPushButton("Browse Priv Key"); btn2.clicked.connect(lambda: self.load_file(self.lbl_ver_key, "pem", "ver_key"))
        h2.addWidget(btn2); h2.addWidget(self.lbl_ver_key)
        layout.addLayout(h2)

        h3 = QHBoxLayout()
        self.lbl_ver_orig = QLabel("No Original")
        btn3 = QPushButton("Browse Original"); btn3.clicked.connect(lambda: self.load_file(self.lbl_ver_orig, "img", "ver_orig"))
        h3.addWidget(btn3); h3.addWidget(self.lbl_ver_orig)
        layout.addLayout(h3)
        
        btn_ver = QPushButton("🔓 Decrypt & Verify"); btn_ver.setStyleSheet("background-color: #9C27B0;")
        btn_ver.clicked.connect(self.run_verify); layout.addWidget(btn_ver)
        
        self.log_ver = QTextEdit(); layout.addWidget(self.log_ver)
        tab.setLayout(layout); self.tabs.addTab(tab, "🔍 Verify")

    def run_verify(self):
        if not self.filepath_dec or not self.priv_key_path: return
        try:
            valid, status = self.watermarker.verify_fragile_seal(self.filepath_dec)
            self.log_ver.append(status)
            
            payload = self.stego.dct_extract(self.filepath_dec)
            if "###KEY_END###" in payload:
                ek, em = payload.split("###KEY_END###")
                sk = RSAManager.decrypt_session_key(ek, self.priv_key_path)
                dm = CryptoHandler(sk).decrypt(em)
                self.log_ver.append(f"Secret: {dm}")
                
            if self.filepath_orig:
                self.watermarker.extract_watermark(self.filepath_dec, self.filepath_orig, "assets/qt_wm_ext.png")
                cv2.imshow("WM", cv2.imread("assets/qt_wm_ext.png"))
        except Exception as e: self.log_ver.append(str(e))

    # --- TAB 4: VIDEO ---
    def create_video_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        
        h1 = QHBoxLayout()
        self.lbl_vid = QLabel("No Video")
        btn = QPushButton("Browse Video"); btn.clicked.connect(lambda: self.load_file(self.lbl_vid, "vid", "vid_file"))
        h1.addWidget(btn); h1.addWidget(self.lbl_vid)
        layout.addLayout(h1)
        
        self.txt_vid_msg = QLineEdit(); layout.addWidget(self.txt_vid_msg)
        
        h2 = QHBoxLayout()
        b1 = QPushButton("Embed"); b1.clicked.connect(self.run_vid_embed)
        b2 = QPushButton("Extract"); b2.clicked.connect(self.run_vid_extract)
        h2.addWidget(b1); h2.addWidget(b2); layout.addLayout(h2)
        
        self.log_vid = QTextEdit(); layout.addWidget(self.log_vid)
        tab.setLayout(layout); self.tabs.addTab(tab, "🎥 Video")

    def run_vid_embed(self):
        if not self.filepath_vid: return
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "AVI (*.avi)")
        if path:
            self.log_vid.append("Processing...")
            c = self.video_stego.embed_in_video(self.filepath_vid, self.txt_vid_msg.text(), path)
            self.log_vid.append(f"Embedded in {c} frames.")

    def run_vid_extract(self):
        if not self.filepath_vid: return
        self.log_vid.append("Scanning...")
        res = self.video_stego.extract_from_video(self.filepath_vid)
        for r in res: self.log_vid.append(f"Frame {r['frame']}: {r['message']}")

    # --- TAB 5: AUDIO (NEW) ---
    def create_audio_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        
        h1 = QHBoxLayout()
        self.lbl_aud = QLabel("No Audio (.wav)")
        btn = QPushButton("Browse Audio"); btn.clicked.connect(lambda: self.load_file(self.lbl_aud, "aud", "aud_file"))
        h1.addWidget(btn); h1.addWidget(self.lbl_aud)
        layout.addLayout(h1)
        
        self.txt_aud_msg = QLineEdit(); self.txt_aud_msg.setPlaceholderText("Message..."); layout.addWidget(self.txt_aud_msg)
        
        h2 = QHBoxLayout()
        b1 = QPushButton("Embed"); b1.clicked.connect(self.run_aud_embed)
        b2 = QPushButton("Extract"); b2.clicked.connect(self.run_aud_extract)
        h2.addWidget(b1); h2.addWidget(b2); layout.addLayout(h2)
        
        self.log_aud = QTextEdit(); layout.addWidget(self.log_aud)
        tab.setLayout(layout); self.tabs.addTab(tab, "🎵 Audio")

    def run_aud_embed(self):
        if not self.filepath_aud: return
        path, _ = QFileDialog.getSaveFileName(self, "Save", "", "WAV (*.wav)")
        if path:
            try:
                bits = self.audio_stego.embed_audio(self.filepath_aud, self.txt_aud_msg.text(), path)
                self.log_aud.append(f"Success! Hidden {bits} bits.")
            except Exception as e: self.log_aud.append(str(e))

    def run_aud_extract(self):
        if not self.filepath_aud: return
        try:
            msg = self.audio_stego.extract_audio(self.filepath_aud)
            self.log_aud.append(f"Found: {msg}")
        except Exception as e: self.log_aud.append(str(e))

    # --- TABS 6 & 7: ATTACK & ANALYSIS ---
    def create_attack_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        h1 = QHBoxLayout()
        self.lbl_atk = QLabel("No Image"); b1 = QPushButton("Stego"); b1.clicked.connect(lambda: self.load_file(self.lbl_atk, "img", "atk_img"))
        h1.addWidget(b1); h1.addWidget(self.lbl_atk); layout.addLayout(h1)
        h2 = QHBoxLayout()
        self.lbl_atk_orig = QLabel("No Original"); b2 = QPushButton("Original"); b2.clicked.connect(lambda: self.load_file(self.lbl_atk_orig, "img", "atk_orig"))
        h2.addWidget(b2); h2.addWidget(self.lbl_atk_orig); layout.addLayout(h2)
        
        h3 = QHBoxLayout()
        b_jpg = QPushButton("JPEG"); b_jpg.clicked.connect(lambda: self.run_attack("jpeg"))
        b_nse = QPushButton("Noise"); b_nse.clicked.connect(lambda: self.run_attack("noise"))
        h3.addWidget(b_jpg); h3.addWidget(b_nse); layout.addLayout(h3)
        self.log_atk = QTextEdit(); layout.addWidget(self.log_atk)
        tab.setLayout(layout); self.tabs.addTab(tab, "⚔️ Attack")

    def run_attack(self, t):
        if not self.filepath_atk: return
        if t=="jpeg": o=AttackSimulator.apply_jpeg_compression(self.filepath_atk)
        else: o=AttackSimulator.apply_noise(self.filepath_atk)
        self.log_atk.append(f"Attacked: {o}")
        self.watermarker.extract_watermark(o, self.filepath_atk_orig, "assets/qt_rec.png")
        cv2.imshow("Rec", cv2.imread("assets/qt_rec.png"))

    def create_analysis_tab(self):
        tab = QWidget(); layout = QVBoxLayout()
        h1 = QHBoxLayout()
        self.lbl_ana = QLabel("No Image"); b = QPushButton("Browse"); b.clicked.connect(lambda: self.load_file(self.lbl_ana, "img", "ana_img"))
        h1.addWidget(b); h1.addWidget(self.lbl_ana); layout.addLayout(h1)
        
        b_scan = QPushButton("Run Scan"); b_scan.clicked.connect(self.run_analysis); layout.addWidget(b_scan)
        self.lbl_threat = QLabel("Waiting..."); layout.addWidget(self.lbl_threat)
        tab.setLayout(layout); self.tabs.addTab(tab, "🕵️ Analysis")

    def run_analysis(self):
        if not self.filepath_ana: return
        p = SteganalysisScanner.perform_chi_square_test(self.filepath_ana) * 100
        self.lbl_threat.setText(f"Threat: {p:.1f}%")

    def load_file(self, lbl, t, v):
        f = "Images (*.png *.jpg)"
        if t=="pem": f="Keys (*.pem)"
        elif t=="vid": f="Video (*.mp4 *.avi)"
        elif t=="aud": f="Audio (*.wav)"
        
        fn, _ = QFileDialog.getOpenFileName(self, "Select", "", f)
        if fn:
            lbl.setText(os.path.basename(fn))
            if v=="prot_img": self.filepath=fn
            elif v=="prot_key": self.pub_key_path=fn
            elif v=="ver_img": self.filepath_dec=fn
            elif v=="ver_key": self.priv_key_path=fn
            elif v=="ver_orig": self.filepath_orig=fn
            elif v=="vid_file": self.filepath_vid=fn
            elif v=="aud_file": self.filepath_aud=fn
            elif v=="atk_img": self.filepath_atk=fn
            elif v=="atk_orig": self.filepath_atk_orig=fn
            elif v=="ana_img": self.filepath_ana=fn

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ModernCyberApp()
    w.show()
    sys.exit(app.exec())