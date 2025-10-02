
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import hashlib
import threading
import time
import mimetypes
import subprocess
import psutil
import json
import math
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import shutil
import zipfile
import queue
from typing import Optional, List, Tuple, Dict, Any
from collections import Counter, defaultdict
import struct
import pickle
from dataclasses import dataclass, field

print("Verificando dependências...")

try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    QT_VERSION = 5
    print("PyQt5 carregado com sucesso")
except ImportError:
    try:
        from PyQt6.QtWidgets import *
        from PyQt6.QtGui import *
        from PyQt6.QtCore import *
        QT_VERSION = 6
        print("PyQt6 carregado com sucesso")
    except ImportError:
        print("ERRO: PyQt5/6 não encontrado!")
        print("Execute: pip install PyQt5 pyqt5-tools psutil")
        input("\nPressione Enter para sair...")
        sys.exit(1)

try:
    import winreg
    WINDOWS_AVAILABLE = True
    print("Controles Windows disponíveis")
except ImportError:
    WINDOWS_AVAILABLE = False
    print("Controles Windows não disponíveis (sistema não-Windows)")

try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
    print("tkinter disponível para pop-ups")
except ImportError:
    TKINTER_AVAILABLE = False
    print("tkinter não disponível")

ML_AVAILABLE = False
try:
    import numpy as np
    ML_AVAILABLE = True
    print("NumPy disponível para ML")
except ImportError:
    print("NumPy não disponível - ML desabilitado")

LIGHTGBM_AVAILABLE = False
if ML_AVAILABLE:
    try:
        import lightgbm as lgb
        LIGHTGBM_AVAILABLE = True
        print("LightGBM disponível - ML completo ativo")
    except ImportError:
        print("LightGBM não disponível - usando fallback heurístico")

ULTRA_ENTROPY_THRESHOLD = 6.8
FALLEN_ANGEL_ENTROPY_THRESHOLD = 6.5
MAX_SUSPICIOUS_SCORE = 20
FALLEN_ANGEL_KILL_THRESHOLD = 6

ML_CONFIDENCE_THRESHOLD = 0.7
ML_FEATURE_TIMEOUT_MS = 100
ML_CACHE_SIZE = 10000
PROCESS_CONFIRMATION_COUNT = 1
KILL_RETRY_ATTEMPTS = 3
KILL_RETRY_DELAY = 0.1

MALWARE_SIGNATURES = {
    "44d88612fea8a8f36de82e1278abb02f": "EICAR-Test-Signature",
    "5d41402abc4b2a76b9719d911017c592": "Trojan.Generic",
    "1ec1fed91f694e0d229928963b30f6b0d7d3a745": "NotPetya",
    "7a828afd2abf153d840938090d498072b7e507c7021e4cdd8c6baf727cadf3e3": "Ryuk",
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "WannaCry",
    "4a468603fdcb7a2eb5770705898cf9ef37aade532a7964642ecd705a74794b79": "Maze",
    "9c11c5fdc39e2e3b5c8c4b2e4b4e4b4e4b4e4b4e4b4e4b4e4b4e4b4e4b4e4b4e": "Conti",
    "b12c5fdc39e2e3b5c8c4b2e4b4e4b4e4b4e4b4e4b4e4b4e4b4e4b4e4b4e4b4e": "REvil"
}

SUSPICIOUS_EXTENSIONS = [
    '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.reg', '.vbs',
    '.js', '.jar', '.ps1', '.msi', '.app', '.deb', '.rpm',
    '.crypted', '.encrypted', '.locked', '.crypto', '.crypt', '.enc', '.locky',
    '.cerber', '.zepto', '.thor', '.aesir', '.odin', '.sage', '.spora',
    '.wannacry', '.wcry', '.wncry', '.onion', '.dharma', '.wallet'
]

ULTRA_SUSPICIOUS_PROCESSES = [
    "powershell.exe", "cmd.exe", "certutil.exe", "bitsadmin.exe",
    "regsvr32.exe", "rundll32.exe", "mshta.exe", "wmic.exe",
    "taskkill.exe", "net.exe", "netsh.exe", "schtasks.exe",
    "reg.exe", "regedit.exe", "bcdedit.exe", "vssadmin.exe",
    "wbadmin.exe", "wevtutil.exe", "fsutil.exe", "cipher.exe"
]

SUSPICIOUS_PATTERNS = [
    'crack', 'keygen', 'patch', 'activator', 'loader', 'hack',
    'trojan', 'virus', 'malware', 'bitcoin', 'crypto', 'miner',
    'ransomware', 'encrypt', 'decrypt', 'wannacry', 'locky'
]

RANSOMWARE_PATTERNS = [
    'readme_for_decrypt', 'how_to_decrypt', 'recovery_key',
    'files_encrypted', 'your_files', 'restore_files',
    'bitcoin', 'cryptocurrency', 'payment', 'recovery'
]

@dataclass
class ProcessThreat:
    pid: int
    name: str
    path: str
    detections: List[Dict[str, Any]] = field(default_factory=list)
    first_detected: datetime = field(default_factory=datetime.now)
    last_detection: datetime = field(default_factory=datetime.now)
    kill_attempts: int = 0
    is_persistent: bool = False
    ml_scores: List[float] = field(default_factory=list)

    @property
    def avg_ml_score(self) -> float:
        return sum(self.ml_scores) / len(self.ml_scores) if self.ml_scores else 0.0

    @property
    def should_kill(self) -> bool:
        if len(self.detections) < PROCESS_CONFIRMATION_COUNT:
            return False
        
        recent_detections = [d for d in self.detections if (datetime.now() - d['timestamp']).seconds < 30]
        
        if len(recent_detections) >= PROCESS_CONFIRMATION_COUNT:
            avg_score = sum(d.get('score', 0) for d in recent_detections) / len(recent_detections)
            return avg_score >= FALLEN_ANGEL_KILL_THRESHOLD
        
        return False

@dataclass
class MLPrediction:
    malware_probability: float
    confidence: float
    features_extracted: bool
    processing_time_ms: float
    model_used: str

class ProcessTracker:
    def __init__(self):
        self.tracked_processes: Dict[int, ProcessThreat] = {}
        self.process_hashes: Dict[str, List[int]] = defaultdict(list)
        self.lock = threading.RLock()

    def get_process_hash(self, proc_info: Dict) -> str:
        try:
            name = proc_info.get('name', '')
            path = proc_info.get('path', '')
            unique_str = f"{name}|{path}|{proc_info.get('pid', 0)}"
            return hashlib.md5(unique_str.encode()).hexdigest()
        except Exception:
            return f"unknown_{proc_info.get('pid', 0)}"

    def add_detection(self, proc_info: Dict, detection_info: Dict):
        with self.lock:
            pid = proc_info.get('pid')
            if not pid:
                return
            
            if pid not in self.tracked_processes:
                self.tracked_processes[pid] = ProcessThreat(
                    pid=pid,
                    name=proc_info.get('name', ''),
                    path=proc_info.get('path', '')
                )
            
            threat = self.tracked_processes[pid]
            detection_info['timestamp'] = datetime.now()
            threat.detections.append(detection_info)
            threat.last_detection = datetime.now()
            
            if 'ml_score' in detection_info:
                threat.ml_scores.append(detection_info['ml_score'])
            
            cutoff = datetime.now() - timedelta(minutes=5)
            threat.detections = [d for d in threat.detections if d['timestamp'] > cutoff]
            
            if len(threat.detections) > 3:
                threat.is_persistent = True

    def get_threat(self, pid: int) -> Optional[ProcessThreat]:
        with self.lock:
            return self.tracked_processes.get(pid)

    def cleanup_old_processes(self):
        with self.lock:
            cutoff = datetime.now() - timedelta(minutes=10)
            old_pids = [pid for pid, threat in self.tracked_processes.items() if threat.last_detection < cutoff]
            for pid in old_pids:
                del self.tracked_processes[pid]

class ConsistentDetectionSystem:
    def __init__(self):
        self.process_tracker = ProcessTracker()
        self.prediction_cache = {}
        self.hash_cache = {}
        self.features_cache = {}
        self.cleanup_timer = None
        self._start_cleanup_timer()

    def _start_cleanup_timer(self):
        def cleanup():
            self.process_tracker.cleanup_old_processes()
            self._clear_old_caches()
            self.cleanup_timer = threading.Timer(300, cleanup)
            self.cleanup_timer.start()
        
        self.cleanup_timer = threading.Timer(300, cleanup)
        self.cleanup_timer.start()

    def _clear_old_caches(self):
        if len(self.prediction_cache) > ML_CACHE_SIZE:
            sorted_items = sorted(self.prediction_cache.items(), key=lambda x: x[1].get('timestamp', 0))
            self.prediction_cache = dict(sorted_items[-ML_CACHE_SIZE//2:])
        
        if len(self.hash_cache) > ML_CACHE_SIZE:
            sorted_items = sorted(self.hash_cache.items(), key=lambda x: x[1].get('timestamp', 0))
            self.hash_cache = dict(sorted_items[-ML_CACHE_SIZE//2:])

    def analyze_process(self, proc_info: Dict, ml_score: float = None) -> ProcessThreat:
        detection_info = {'score': proc_info.get('suspicious_score', 0), 'ml_score': ml_score or 0.0, 'source': 'ml' if ml_score else 'heuristic'}
        self.process_tracker.add_detection(proc_info, detection_info)
        threat = self.process_tracker.get_threat(proc_info.get('pid'))
        return threat or ProcessThreat(pid=proc_info.get('pid', 0), name=proc_info.get('name', ''), path=proc_info.get('path', ''))

class LightweightMLEngine:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.fallback_mode = True
        if LIGHTGBM_AVAILABLE:
            self._try_load_model()

    def _try_load_model(self):
        try:
            model_path = Path(__file__).parent / "ember_model.pkl"
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.model_loaded = True
                self.fallback_mode = False
                print("Modelo EMBER carregado com sucesso")
            else:
                print("Modelo EMBER não encontrado - usando fallback heurístico")
        except Exception as e:
            print(f"Erro ao carregar modelo ML: {e}")
            self.fallback_mode = True

    def extract_pe_features(self, file_path: str) -> Optional[np.ndarray]:
        if not ML_AVAILABLE:
            return None
        try:
            start_time = time.time()
            with open(file_path, 'rb') as f:
                data = f.read(1024)
                if len(data) < 64 or data[:2] != b'MZ':
                    return None
                features = []
                features.append(self._calculate_entropy(data))
                file_size = os.path.getsize(file_path)
                features.append(min(file_size / 1024 / 1024, 100))
                features.append(len([b for b in data if b == 0x2E]))
                byte_counts = Counter(data)
                for i in range(7):
                    features.append(byte_counts.get(i, 0) / len(data))
                if (time.time() - start_time) * 1000 > ML_FEATURE_TIMEOUT_MS:
                    return None
                return np.array(features)
        except Exception:
            return None

    def _calculate_entropy(self, data: bytes) -> float:
        if not data:
            return 0.0
        byte_counts = Counter(data)
        data_len = len(data)
        entropy = -sum((count / data_len) * math.log2(count / data_len) for count in byte_counts.values() if count > 0)
        return entropy

    def predict_safe(self, file_path: str) -> MLPrediction:
        start_time = time.time()
        try:
            if not self.model_loaded or self.fallback_mode:
                return self._heuristic_fallback(file_path, start_time)
            features = self.extract_pe_features(file_path)
            if features is None:
                return self._heuristic_fallback(file_path, start_time)
            try:
                probability = self.model.predict_proba([features])[0][1]
                confidence = abs(probability - 0.5) * 2
                return MLPrediction(malware_probability=probability, confidence=confidence, features_extracted=True, processing_time_ms=(time.time() - start_time) * 1000, model_used="EMBER")
            except Exception:
                return self._heuristic_fallback(file_path, start_time)
        except Exception:
            return self._heuristic_fallback(file_path, start_time)

    def _heuristic_fallback(self, file_path: str, start_time: float) -> MLPrediction:
        try:
            suspicious_score = 0.0
            ext = os.path.splitext(file_path)[1].lower()
            if ext in SUSPICIOUS_EXTENSIONS:
                suspicious_score += 0.3
            filename = os.path.basename(file_path).lower()
            for pattern in SUSPICIOUS_PATTERNS + RANSOMWARE_PATTERNS:
                if pattern in filename:
                    suspicious_score += 0.4
                    break
            try:
                with open(file_path, 'rb') as f:
                    data = f.read(8192)
                entropy = self._calculate_entropy(data)
                if entropy > FALLEN_ANGEL_ENTROPY_THRESHOLD:
                    suspicious_score += 0.5
            except Exception:
                pass
            return MLPrediction(malware_probability=min(suspicious_score, 1.0), confidence=0.6, features_extracted=False, processing_time_ms=(time.time() - start_time) * 1000, model_used="Heuristic")
        except Exception:
            return MLPrediction(malware_probability=0.0, confidence=0.0, features_extracted=False, processing_time_ms=(time.time() - start_time) * 1000, model_used="Error")

def calculate_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    try:
        byte_counts = Counter(data)
        data_len = len(data)
        entropy = -sum((count / data_len) * math.log2(count / data_len) for count in byte_counts.values() if count > 0)
        return entropy
    except Exception:
        return 0.0

class AlertSystem(QObject):
    threat_detected_signal = pyqtSignal(dict)
    process_killed_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.popup_enabled = True
    
    def show_threat_alert(self, threat_info):
        if not self.popup_enabled:
            return
        self.threat_detected_signal.emit(threat_info)
        try:
            if TKINTER_AVAILABLE:
                self._show_tkinter_popup("AMEAÇA DETECTADA - ANGLE GUARD", f"AMEAÇA DETECTADA!\n\nArquivo: {threat_info.get('file_path', 'Desconhecido')}\nTipo: {threat_info.get('threat_type', 'Desconhecido')}\nConfiança: {threat_info.get('confidence', 0):.1%}\nModelo: {threat_info.get('model_used', 'Heurístico')}\n\nAÇÃO AUTOMÁTICA EXECUTADA", "warning")
        except Exception as e:
            print(f"Erro ao mostrar pop-up de ameaça: {e}")
    
    def show_process_killed_alert(self, process_info):
        if not self.popup_enabled:
            return
        self.process_killed_signal.emit(process_info)
        try:
            if TKINTER_AVAILABLE:
                self._show_tkinter_popup("PROCESSO ELIMINADO - ANGLE GUARD", f"PROCESSO SUSPEITO ELIMINADO!\n\nNome: {process_info.get('name', 'Desconhecido')}\nPID: {process_info.get('pid', 'Desconhecido')}\nMotivo: {process_info.get('reason', 'Comportamento suspeito')}\nML Score: {process_info.get('ml_score', 0):.2f}\n\nPROTEÇÃO ATIVA", "error")
        except Exception as e:
            print(f"Erro ao mostrar pop-up de processo: {e}")
    
    def _show_tkinter_popup(self, title, message, level="info"):
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            if level == "error":
                messagebox.showerror(title, message)
            elif level == "warning":
                messagebox.showwarning(title, message)
            else:
                messagebox.showinfo(title, message)
            root.destroy()
        except Exception as e:
            print(f"Erro no pop-up tkinter: {e}")

class ProcessKiller:
    def __init__(self, alert_system):
        self.alert_system = alert_system
        self.fallen_angel_mode = False
        self.killed_processes = set()
        self.detection_system = ConsistentDetectionSystem()
        self.ml_engine = LightweightMLEngine() if ML_AVAILABLE else None

    def set_fallen_angel_mode(self, enabled):
        self.fallen_angel_mode = enabled
        print(f"Modo Anjo Caído {'ATIVADO' if enabled else 'desativado'}")
        if enabled and self.ml_engine:
            print("Sistema ML anti-oscilação ativado")
    
    def should_kill_process(self, process_info):
        if not self.fallen_angel_mode:
            return False
        try:
            name = process_info.get('name', '').lower()
            path = process_info.get('path', '')
            pid = process_info.get('pid')
            threat = self.detection_system.process_tracker.get_threat(pid)
            if threat and threat.kill_attempts >= KILL_RETRY_ATTEMPTS:
                return False
            ml_score = 0.0
            if self.ml_engine and path and os.path.exists(path):
                try:
                    prediction = self.ml_engine.predict_safe(path)
                    ml_score = prediction.malware_probability
                    process_info['ml_score'] = ml_score
                    process_info['ml_confidence'] = prediction.confidence
                    process_info['ml_model'] = prediction.model_used
                except Exception as e:
                    print(f"Erro na predição ML: {e}")
            threat = self.detection_system.analyze_process(process_info, ml_score)
            if threat.should_kill:
                return True
            if name in [p.lower() for p in ULTRA_SUSPICIOUS_PROCESSES]:
                if ml_score > 0.5 or process_info.get('suspicious_score', 0) > 15:
                    return True
            return False
        except Exception as e:
            print(f"Erro ao analisar processo: {e}")
            return False
    
    def kill_process_with_retry(self, process_info, reason="Comportamento suspeito"):
        pid = process_info.get('pid')
        name = process_info.get('name', 'Desconhecido')
        if not pid or pid in self.killed_processes:
            return False
        
        for attempt in range(KILL_RETRY_ATTEMPTS):
            try:
                if not psutil.pid_exists(pid):
                    return True
                
                process = psutil.Process(pid)
                print(f"ELIMINANDO PROCESSO (tentativa {attempt + 1}): {name} (PID: {pid}) via psutil")
                for child in process.children(recursive=True):
                    try: child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied): pass
                process.kill()

                if not psutil.pid_exists(pid):
                    self.killed_processes.add(pid)
                    threat = self.detection_system.process_tracker.get_threat(pid)
                    if threat: threat.kill_attempts += 1
                    process_info['reason'] = reason
                    self.alert_system.show_process_killed_alert(process_info)
                    print(f"Processo {name} (PID: {pid}) eliminado com sucesso.")
                    return True
            except psutil.NoSuchProcess:
                return True
            except (psutil.AccessDenied, Exception) as e:
                print(f"psutil kill falhou: {e}. Tentando fallback com taskkill...")
                if os.name == 'nt':
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        subprocess.run(['taskkill', '/F', '/PID', str(pid)], check=True, capture_output=True, startupinfo=startupinfo)
                        if not psutil.pid_exists(pid):
                            self.killed_processes.add(pid)
                            process_info['reason'] = reason
                            self.alert_system.show_process_killed_alert(process_info)
                            print(f"Processo {name} (PID: {pid}) eliminado com sucesso via taskkill.")
                            return True
                    except Exception as taskkill_e:
                        print(f"Falha ao executar taskkill: {taskkill_e}")
            
            if attempt < KILL_RETRY_ATTEMPTS - 1:
                time.sleep(KILL_RETRY_DELAY)

        print(f"Falhou ao eliminar processo {pid} após {KILL_RETRY_ATTEMPTS} tentativas")
        return False

class NetworkManager:
    def __init__(self):
        self.wifi_enabled = True
        self.usb_enabled = True
    
    def disable_wifi(self):
        try:
            if os.name == 'nt':
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disable"], check=True, capture_output=True)
            else:
                subprocess.run(["nmcli", "radio", "wifi", "off"], check=True, capture_output=True)
            self.wifi_enabled = False
            return True
        except Exception:
            return False
    
    def enable_wifi(self):
        try:
            if os.name == 'nt':
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enable"], check=True, capture_output=True)
            else:
                subprocess.run(["nmcli", "radio", "wifi", "on"], check=True, capture_output=True)
            self.wifi_enabled = True
            return True
        except Exception:
            return False
    
    def disable_usb(self):
        try:
            if os.name == 'nt' and WINDOWS_AVAILABLE:
                subprocess.run(["reg", "add", "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR", "/v", "Start", "/t", "REG_DWORD", "/d", "4", "/f"], check=True, capture_output=True)
            self.usb_enabled = False
            return True
        except Exception:
            return False
    
    def enable_usb(self):
        try:
            if os.name == 'nt' and WINDOWS_AVAILABLE:
                subprocess.run(["reg", "add", "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR", "/v", "Start", "/t", "REG_DWORD", "/d", "3", "/f"], check=True, capture_output=True)
            self.usb_enabled = True
            return True
        except Exception:
            return False
    
    def get_network_status(self):
        return {'wifi_enabled': self.wifi_enabled, 'usb_enabled': self.usb_enabled}

    def toggle_wifi(self):
        return self.disable_wifi() if self.wifi_enabled else self.enable_wifi()

    def toggle_usb(self):
        return self.disable_usb() if self.usb_enabled else self.enable_usb()

    def emergency_lockdown(self):
        return self.disable_wifi() and self.disable_usb()

class StartupControl:
    def __init__(self):
        self.app_name = "AngleGuard"
        
    def toggle(self):
        return self.disable() if self.is_enabled() else self.enable()
    
    def is_enabled(self):
        if not WINDOWS_AVAILABLE:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ) as key:
                winreg.QueryValueEx(key, self.app_name)
            return True
        except (FileNotFoundError, Exception):
            return False
    
    def enable(self):
        if not WINDOWS_AVAILABLE:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, sys.executable)
            return True
        except Exception:
            return False
    
    def disable(self):
        if not WINDOWS_AVAILABLE:
            return False
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.app_name)
            return True
        except Exception:
            return False

class EnhancedScanWorker(QThread):
    progress_updated = pyqtSignal(int)
    file_scanned = pyqtSignal(str)
    threat_found = pyqtSignal(str, str, str)
    scan_completed = pyqtSignal(int, int, list)
    scan_status = pyqtSignal(str)
    
    def __init__(self, directories: List[str], scan_type: str = "quick", fallen_angel_mode: bool = False):
        super().__init__()
        self.directories = directories
        self.scan_type = scan_type
        self.fallen_angel_mode = fallen_angel_mode
        self._stop_requested = False
        self._mutex = QMutex()
        self.ml_engine = LightweightMLEngine() if fallen_angel_mode and ML_AVAILABLE else None
        
    def request_stop(self):
        with QMutexLocker(self._mutex):
            self._stop_requested = True
    
    def is_stop_requested(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._stop_requested
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    if self.is_stop_requested():
                        return None
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None
    
    def is_executable(self, file_path: str) -> bool:
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.exe', '.scr', '.com', '.bat', '.cmd', '.pif']
    
    def check_file_suspicious_enhanced(self, file_path: str) -> Tuple[bool, Optional[str], float]:
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_path)[1].lower()
        confidence = 0.0
        threat_type = "Suspeito"
        
        if self.fallen_angel_mode and self.ml_engine and self.is_executable(file_path):
            try:
                ml_prediction = self.ml_engine.predict_safe(file_path)
                ml_score = ml_prediction.malware_probability
                if ml_score > ML_CONFIDENCE_THRESHOLD:
                    confidence = ml_score
                    threat_type = "Malware" if ml_score > 0.9 else "Suspeito"
                    reason = f"Detecção ML ({ml_prediction.model_used}): {ml_score:.2f}"
                    return True, reason, confidence
            except Exception as e:
                print(f"Erro na detecção ML: {e}")
        
        if file_ext in SUSPICIOUS_EXTENSIONS:
            confidence += 0.6
            for pattern in SUSPICIOUS_PATTERNS:
                if pattern in file_name:
                    confidence += 0.3
                    break
            for pattern in RANSOMWARE_PATTERNS:
                if pattern in file_name:
                    confidence += 0.4
                    threat_type = "Ransomware"
                    break
        try:
            file_size = os.path.getsize(file_path)
            if file_size < 10 * 1024 * 1024:
                with open(file_path, 'rb') as f:
                    data = f.read(min(65536, file_size))
                entropy = calculate_entropy(data)
                threshold = FALLEN_ANGEL_ENTROPY_THRESHOLD if self.fallen_angel_mode else ULTRA_ENTROPY_THRESHOLD
                if entropy > threshold:
                    confidence += 0.8 if self.fallen_angel_mode else 0.6
        except Exception:
            pass
        
        if confidence >= 0.5:
            reason = f"Arquivo {threat_type.lower()} - Confiança: {confidence:.1%}"
            return True, reason, confidence
        return False, None, confidence
    
    def scan_file_enhanced(self, file_path: str) -> Optional[Tuple[str, str, float]]:
        try:
            if not os.path.exists(file_path) or self.is_stop_requested():
                return None
            file_hash = self.calculate_file_hash(file_path)
            if file_hash and not self.is_stop_requested() and file_hash in MALWARE_SIGNATURES:
                threat_name = MALWARE_SIGNATURES[file_hash]
                self.threat_found.emit(file_path, "Malware", f"Detectado: {threat_name}")
                return "Malware", threat_name, 1.0
            if self.is_stop_requested():
                return None
            is_suspicious, reason, confidence = self.check_file_suspicious_enhanced(file_path)
            if is_suspicious:
                threat_type = "Suspeito" if confidence < 0.8 else "Malware"
                self.threat_found.emit(file_path, threat_type, reason)
                return threat_type, reason, confidence
            return None
        except Exception as e:
            print(f"Erro ao verificar arquivo {file_path}: {e}")
            return None
    
    def run(self):
        try:
            files_scanned = 0
            threats_found = []
            mode_text = "MODO ANJO CAÍDO" if self.fallen_angel_mode else "modo normal"
            self.scan_status.emit(f"Iniciando verificação aprimorada ({mode_text})...")
            
            patterns = ["*.exe", "*.scr", "*.bat", "*.cmd", "*.vbs", "*.js"] if self.scan_type == "quick" else ["*"]
            
            all_files = []
            self.scan_status.emit("Coletando arquivos...")
            for directory in self.directories:
                if self.is_stop_requested() or not os.path.exists(directory):
                    break
                try:
                    for pattern in patterns:
                        for file_path in Path(directory).rglob(pattern):
                            if self.is_stop_requested(): break
                            if file_path.is_file():
                                all_files.append(str(file_path))
                            if len(all_files) > 10000: break
                        if self.is_stop_requested() or len(all_files) > 10000: break
                except Exception as e:
                    print(f"Erro ao coletar arquivos de {directory}: {e}")
            
            total_files = len(all_files)
            self.scan_status.emit(f"Verificando {total_files} arquivos ({mode_text})...")
            
            for i, file_path in enumerate(all_files):
                if self.is_stop_requested():
                    break
                self.file_scanned.emit(os.path.basename(file_path))
                result = self.scan_file_enhanced(file_path)
                if result and not self.is_stop_requested():
                    threats_found.append({'file': file_path, 'type': result[0], 'description': result[1], 'confidence': result[2], 'detected_at': datetime.now().isoformat(), 'ml_enabled': self.fallen_angel_mode and self.ml_engine is not None})
                files_scanned += 1
                if total_files > 0:
                    self.progress_updated.emit(min(100, int((i + 1) * 100 / total_files)))
                if i % 10 == 0:
                    self.msleep(1)
            
            if not self.is_stop_requested():
                self.scan_completed.emit(files_scanned, len(threats_found), threats_found)
                self.scan_status.emit("Verificação concluída")
            else:
                self.scan_status.emit("Verificação cancelada")
        except Exception as e:
            print(f"Erro durante verificação: {e}")
            self.scan_status.emit(f"Erro na verificação: {str(e)}")
            self.scan_completed.emit(0, 0, [])

class ThreatScanner(QObject):
    def __init__(self):
        super().__init__()
        self.current_worker: Optional[EnhancedScanWorker] = None
        
    def start_scan(self, directories: List[str], scan_type: str = "quick", fallen_angel_mode: bool = False) -> EnhancedScanWorker:
        self.stop_scan()
        self.current_worker = EnhancedScanWorker(directories, scan_type, fallen_angel_mode)
        return self.current_worker
    
    def stop_scan(self):
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.request_stop()
            if not self.current_worker.wait(3000):
                self.current_worker.terminate()
                self.current_worker.wait(1000)
        self.current_worker = None

class QuarantineManager:
    def __init__(self, quarantine_dir):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.quarantine_dir / "quarantine.db"
        self.init_database()
    
    def init_database(self):
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS quarantine (id INTEGER PRIMARY KEY, original_path TEXT, quarantine_path TEXT, threat_type TEXT, description TEXT, quarantined_at TEXT, reason TEXT, confidence REAL, ml_enabled INTEGER DEFAULT 0, model_used TEXT)''')
        except Exception as e:
            print(f"Erro ao inicializar banco de quarentena: {e}")
    
    def quarantine_file(self, file_path, threat_type, description, reason=None, confidence=0.0, ml_enabled=False, model_used=None):
        try:
            original_path = Path(file_path)
            if not original_path.exists():
                return False
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_name = f"{timestamp}_{original_path.name}.quar"
            quarantine_path = self.quarantine_dir / quarantine_name
            shutil.move(str(original_path), str(quarantine_path))
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute('''INSERT INTO quarantine (original_path, quarantine_path, threat_type, description, quarantined_at, reason, confidence, ml_enabled, model_used) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (str(original_path), str(quarantine_path), threat_type, description, datetime.now().isoformat(), reason or description, confidence, 1 if ml_enabled else 0, model_used or 'Heuristic'))
            print(f"Arquivo em quarentena: {file_path}")
            return True
        except Exception as e:
            print(f"Erro ao quarentenar arquivo {file_path}: {e}")
            return False
    
    def get_quarantined_files(self):
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('''SELECT id, original_path, threat_type, description, quarantined_at, reason, confidence, ml_enabled, model_used FROM quarantine ORDER BY quarantined_at DESC''')
                return cursor.fetchall()
        except Exception as e:
            print(f"Erro ao obter arquivos em quarentena: {e}")
            return []
    
    def restore_file(self, quarantine_id):
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('''SELECT original_path, quarantine_path FROM quarantine WHERE id = ?''', (quarantine_id,))
                result = cursor.fetchone()
                if result:
                    original_path, quarantine_path = result
                    if os.path.exists(quarantine_path):
                        os.makedirs(os.path.dirname(original_path), exist_ok=True)
                        shutil.move(quarantine_path, original_path)
                        conn.execute('DELETE FROM quarantine WHERE id = ?', (quarantine_id,))
                        print(f"Arquivo restaurado: {original_path}")
                        return True
            return False
        except Exception as e:
            print(f"Erro ao restaurar arquivo: {e}")
            return False
    
    def delete_quarantine_file(self, quarantine_id):
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute('''SELECT quarantine_path FROM quarantine WHERE id = ?''', (quarantine_id,))
                result = cursor.fetchone()
                if result:
                    quarantine_path = result[0]
                    if os.path.exists(quarantine_path):
                        os.remove(quarantine_path)
                    conn.execute('DELETE FROM quarantine WHERE id = ?', (quarantine_id,))
                    return True
            return False
        except Exception as e:
            print(f"Erro ao deletar arquivo: {e}")
            return False

class RealTimeProtection(QObject):
    threat_detected = pyqtSignal(str, str, str)
    
    def __init__(self, scanner, quarantine_manager, process_killer):
        super().__init__()
        self.scanner = scanner
        self.quarantine_manager = quarantine_manager
        self.process_killer = process_killer
        self.monitoring = False
        self.monitoring_thread = None
    
    def start_monitoring(self):
        self.monitoring = True
        if psutil:
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
        print("Proteção em tempo real ativada")
    
    def stop_monitoring(self):
        self.monitoring = False
        print("Proteção em tempo real desativada")
    
    def _monitoring_loop(self):
        while self.monitoring:
            try:
                if not self.process_killer.fallen_angel_mode:
                    time.sleep(5)
                    continue
                
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        if not self.monitoring: break
                        process_info = {'pid': proc.info['pid'], 'name': proc.info['name'], 'path': proc.info.get('exe', ''), 'suspicious_score': 0}
                        self._calculate_process_suspicion(process_info)
                        if self.process_killer.should_kill_process(process_info):
                            reason = "Monitoramento automático - modo anjo caído"
                            if 'ml_score' in process_info:
                                reason += f" (ML: {process_info['ml_score']:.2f})"
                            
                            if self.process_killer.kill_process_with_retry(process_info, reason):
                                file_path = process_info.get('path')
                                if file_path and os.path.exists(file_path):
                                    print(f"Tentando colocar em quarentena o arquivo de origem: {file_path}")
                                    self.quarantine_manager.quarantine_file(
                                        file_path, 
                                        "Ameaça em Tempo Real", 
                                        f"Processo suspeito eliminado (PID: {process_info['pid']})"
                                    )
                                    self.process_killer.alert_system.show_threat_alert({
                                        'file_path': file_path, 
                                        'threat_type': 'Processo Malicioso',
                                        'confidence': 1.0,
                                        'model_used': 'Real-Time Kill'
                                    })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    except Exception as e:
                        print(f"Erro ao monitorar processo: {e}")
                time.sleep(0.2)
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                time.sleep(10)
    
    def _calculate_process_suspicion(self, process_info):
        try:
            name = process_info['name'].lower()
            path = process_info['path'].lower()
            score = 0
            if name in [p.lower() for p in ULTRA_SUSPICIOUS_PROCESSES]:
                score += 40
            if any(sp in path for sp in ['temp', 'tmp', 'appdata\\roaming', 'downloads']):
                score += 15
            for pattern in RANSOMWARE_PATTERNS:
                if pattern in name:
                    score += 25
                    break
            process_info['suspicious_score'] = score
        except Exception:
            process_info['suspicious_score'] = 0

class AngleGuard(QMainWindow):
    def __init__(self):
        super().__init__()
        print("Iniciando Angle Guard...")
        
        self.app_data_dir = Path.home() / ".angleGuard"
        self.app_data_dir.mkdir(exist_ok=True)
        
        self.alert_system = AlertSystem()
        
        self.scanner = ThreatScanner()
        self.quarantine_manager = QuarantineManager(self.app_data_dir / "quarantine")
        self.process_killer = ProcessKiller(self.alert_system)
        self.realtime_protection = RealTimeProtection(self.scanner, self.quarantine_manager, self.process_killer)
        
        self.network_manager = NetworkManager()
        self.startup_control = StartupControl() if WINDOWS_AVAILABLE else None
        
        self.dark_mode = True
        self.current_tab = 'home'
        self.is_scanning = False
        self.fallen_angel_active = False
        self.current_scan_worker: Optional[EnhancedScanWorker] = None
        
        self.system_data = {'files_scanned': 0, 'threats_blocked': 0, 'ml_detections': 0, 'protection_level': 'Celestial Enhanced', 'quarantine_items': 0, 'last_scan_time': 'Nunca', 'last_scan_duration': '0s', 'last_scan_files': 0, 'wifi_enabled': True, 'usb_enabled': True, 'startup_enabled': False, 'processes_killed': 0}
        
        self.icon_path = ""
        try:
            if getattr(sys, 'frozen', False):
                application_path = os.path.dirname(sys.executable)
            elif __file__:
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            self.icon_path = os.path.join(application_path, 'icon.png')

            if not os.path.exists(self.icon_path):
                print(f"AVISO: Arquivo de ícone 'icon.png' não encontrado na pasta do programa.")
                self.icon_path = ""
        except Exception as e:
            print(f"Erro ao determinar o caminho do ícone: {e}")
            self.icon_path = ""
        
        try:
            self.init_ui()
            self.apply_theme()
            self.load_system_data()
            self.alert_system.threat_detected_signal.connect(self.on_threat_alert)
            self.alert_system.process_killed_signal.connect(self.on_process_killed_alert)
            print("Interface V10 Enhanced criada com sucesso!")
        except Exception as e:
            print(f"Erro ao criar interface: {e}")
            raise
    
    def init_ui(self):
        self.setWindowTitle("Angle Guard - Proteção Celestial ")
        self.setGeometry(150, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        if self.icon_path:
            self.setWindowIcon(QIcon(self.icon_path))

        screen = QApplication.primaryScreen().geometry() if QT_VERSION == 6 else QApplication.desktop().screenGeometry()
        self.move((screen.width() - 1400) // 2, (screen.height() - 900) // 2)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.create_sidebar(main_layout)
        self.create_main_area(main_layout)
        self.create_tray_icon()
        
        self.realtime_protection.start_monitoring()
        self.show_home_page()
    
    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        if self.icon_path:
            self.tray_icon.setIcon(QIcon(self.icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.setToolTip("Angle Guard V10")

        tray_menu = QMenu()
        show_action = QAction("Mostrar Angle Guard", self)
        quit_action = QAction("Sair", self)

        show_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.quit_application)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isHidden() or self.isMinimized():
                self.showNormal()
                self.activateWindow()
            else:
                self.hide()

    def create_sidebar(self, main_layout):
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        self.create_sidebar_header(sidebar_layout)
        self.create_navigation_menu(sidebar_layout)
        main_layout.addWidget(self.sidebar)
    
    def create_sidebar_header(self, layout):
        header_frame = QFrame()
        header_frame.setObjectName("sidebar_header")
        header_frame.setFixedHeight(140)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 25, 20, 25)
        header_layout.setAlignment(Qt.AlignCenter)
        header_layout.setSpacing(10)
        
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        self.theme_btn = QPushButton("☀️" if self.dark_mode else "🌙")
        self.theme_btn.setObjectName("theme_toggle")
        self.theme_btn.setFixedSize(35, 35)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        theme_layout.addWidget(self.theme_btn)
        header_layout.addLayout(theme_layout)
        
        logo_label = QLabel()
        if self.icon_path:
            pixmap = QPixmap(self.icon_path)
            logo_label.setPixmap(pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo_label.setText("🛡️")
            logo_label.setStyleSheet("font-size: 32px;")
        logo_label.setObjectName("logo")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(60, 60)
        header_layout.addWidget(logo_label)
        
        title_label = QLabel("Angle Guard")
        title_label.setObjectName("app_title")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Proteção Enhanced v10.0")
        subtitle_label.setObjectName("app_subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_frame)
    
    def create_navigation_menu(self, layout):
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setObjectName("nav_scroll")
        
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)
        
        self.nav_buttons = {}
        
        self.add_nav_section("PROTEÇÃO", nav_layout)
        self.add_nav_item("home", "🏠", "Início", nav_layout, active=True)
        self.add_nav_item("scan", "🔍", "Verificação", nav_layout)
        self.add_nav_item("realtime", "🛡️", "Proteção em Tempo Real", nav_layout)
        self.add_nav_section("MODO ESPECIAL", nav_layout)
        self.add_nav_item("fallen-angel", "😈", "Anjo Caído", nav_layout, special=True)
        self.add_nav_section("FERRAMENTAS", nav_layout)
        self.add_nav_item("quarantine", "🔒", "Quarentena", nav_layout)
        self.add_nav_item("backup", "💾", "Backup", nav_layout)
        self.add_nav_item("firewall", "🔥", "Firewall", nav_layout)
        self.add_nav_section("SISTEMA", nav_layout)
        self.add_nav_item("performance", "⚡", "Performance", nav_layout)
        self.add_nav_item("settings", "⚙️", "Configurações", nav_layout)
        
        nav_layout.addStretch()
        nav_scroll.setWidget(nav_widget)
        layout.addWidget(nav_scroll)
    
    def add_nav_section(self, title, layout):
        section_label = QLabel(title)
        section_label.setObjectName("nav_section_title")
        section_label.setContentsMargins(20, 15, 20, 5)
        layout.addWidget(section_label)
    
    def add_nav_item(self, item_id, icon, text, layout, active=False, special=False):
        btn = QPushButton(f"  {icon}  {text}")
        btn.setObjectName("nav_item_special" if special else "nav_item")
        btn.setProperty("active", active)
        btn.setFixedHeight(45)
        btn.clicked.connect(lambda: self.switch_tab(item_id))
        btn.setCursor(Qt.PointingHandCursor)
        self.nav_buttons[item_id] = btn
        layout.addWidget(btn)
    
    def create_main_area(self, main_layout):
        main_frame = QFrame()
        main_frame.setObjectName("main_content")
        self.main_layout = QVBoxLayout(main_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.create_main_header()
        
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setObjectName("content_scroll")
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(25)
        
        self.content_scroll.setWidget(self.content_widget)
        self.main_layout.addWidget(self.content_scroll)
        main_layout.addWidget(main_frame, 1)
    
    def create_main_header(self):
        header_frame = QFrame()
        header_frame.setObjectName("main_header")
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        self.page_title = QLabel("Início")
        self.page_title.setObjectName("page_title")
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()
        
        quick_scan_btn = QPushButton("Verificação Rápida")
        quick_scan_btn.setObjectName("primary_button")
        quick_scan_btn.setFixedSize(180, 40)
        quick_scan_btn.clicked.connect(self.start_quick_scan)
        quick_scan_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(quick_scan_btn)
        self.main_layout.addWidget(header_frame)
    
    def clear_content(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def switch_tab(self, tab_id):
        if tab_id == self.current_tab: return
        if self.is_scanning and tab_id != 'scan':
            reply = QMessageBox.question(self, "Verificação em Andamento", "Deseja parar a verificação e trocar de aba?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No: return
            self.stop_scan()
        
        for btn_id, btn in self.nav_buttons.items():
            btn.setProperty("active", btn_id == tab_id)
            btn.setStyle(btn.style())
        
        self.current_tab = tab_id
        titles = {'home': 'Início', 'scan': 'Verificação', 'realtime': 'Proteção em Tempo Real', 'fallen-angel': 'Modo Anjo Caído', 'quarantine': 'Quarentena', 'backup': 'Backup', 'firewall': 'Firewall', 'performance': 'Performance', 'settings': 'Configurações'}
        self.page_title.setText(titles.get(tab_id, 'Início'))
        
        page_map = {
            'home': self.show_home_page, 'scan': self.show_scan_page, 'quarantine': self.show_quarantine_page,
            'fallen-angel': self.show_fallen_angel_page, 'realtime': self.show_realtime_page, 'backup': self.show_backup_page,
            'firewall': self.show_firewall_page, 'settings': self.show_settings_page}
        
        page_map.get(tab_id, lambda: self.show_simple_page(tab_id))()
    
    def create_status_card(self, title="Sistema Protegido", desc="Proteção celestial enhanced ativa"):
        card = QFrame()
        card.setObjectName("status_card_main")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        text_layout = QVBoxLayout()
        status_title = QLabel(title)
        status_title.setObjectName("status_title")
        status_desc = QLabel(desc)
        status_desc.setObjectName("status_desc")
        status_desc.setWordWrap(True)
        text_layout.addWidget(status_title)
        text_layout.addWidget(status_desc)
        text_layout.addStretch()
        layout.addLayout(text_layout, 1)
        return card
    
    def create_stat_card(self, icon, label, value):
        card = QFrame()
        card.setObjectName("stat_card")
        card.setFixedHeight(120)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        value_label = QLabel(str(value))
        value_label.setObjectName("stat_value")
        value_label.setAlignment(Qt.AlignCenter)
        
        label_label = QLabel(label)
        label_label.setObjectName("stat_label")
        label_label.setAlignment(Qt.AlignCenter)
        label_label.setWordWrap(True)
        
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        return card
    
    def show_home_page(self):
        self.clear_content()
        self.content_layout.addWidget(self.create_status_card())
        
        stats_frame = QFrame()
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(20)
        stats_data = [("", "Arquivos Verificados", f"{self.system_data['files_scanned']:,}"), ("", "Ameaças Bloqueadas", str(self.system_data['threats_blocked'])), ("", "Em Quarentena", str(self.system_data['quarantine_items'])), ("", "Processos Eliminados", str(self.system_data['processes_killed']))]
        for i, (icon, label, value) in enumerate(stats_data):
            stats_layout.addWidget(self.create_stat_card(icon, label, value), 0, i)
        self.content_layout.addWidget(stats_frame)
        
        stats_btn = QPushButton("Mostrar Estatísticas Detalhadas")
        stats_btn.setObjectName("primary_button")
        stats_btn.setFixedHeight(40)
        stats_btn.clicked.connect(self.show_detailed_stats_popup)
        stats_btn.setCursor(Qt.PointingHandCursor)
        self.content_layout.addWidget(stats_btn)
        
        activity_card = QFrame()
        activity_card.setObjectName("activity_card")
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        activity_layout.setSpacing(15)
        title = QLabel("Atividade Recente")
        title.setObjectName("activity_title")
        activity_layout.addWidget(title)
        
        activities = [("", "Proteção em tempo real ativa", "agora"), ("", f"Modo Anjo Caído {'ativo' if self.fallen_angel_active else 'inativo'}", f"{'com ML' if self.fallen_angel_active and ML_AVAILABLE else ''}"), ("", f"Última verificação: {self.system_data['last_scan_time']}", ""), ("", f"Itens em quarentena: {self.system_data['quarantine_items']}", ""), ("", "Sistema otimizado e protegido", "")]
        for icon, activity, time_str in activities:
            item_layout = QHBoxLayout()
            activity_label = QLabel(activity)
            activity_label.setObjectName("activity_text")
            if time_str:
                time_label = QLabel(time_str)
                time_label.setObjectName("activity_time")
                item_layout.addWidget(time_label)
            item_layout.addWidget(activity_label, 1)
            activity_layout.addLayout(item_layout)
        
        self.content_layout.addWidget(activity_card)
        self.content_layout.addStretch()
    
    def show_detailed_stats_popup(self):
        try:
            ml_status = "ATIVO" if self.fallen_angel_active and ML_AVAILABLE else "INATIVO"
            ml_engine = "LightGBM" if LIGHTGBM_AVAILABLE else "Heurístico"
            stats_text = f"ESTATÍSTICAS DETALHADAS - ANGLE GUARD\n\nVERIFICAÇÕES:\n• Arquivos verificados: {self.system_data['files_scanned']:,}\n• Última verificação: {self.system_data['last_scan_time']}\n• Arquivos na última verificação: {self.system_data['last_scan_files']:,}\n• Duração da última verificação: {self.system_data['last_scan_duration']}\n\nPROTEÇÃO:\n• Ameaças bloqueadas: {self.system_data['threats_blocked']}\n• Detecções ML: {self.system_data['ml_detections']}\n• Nível de proteção: {self.system_data['protection_level']}\n\nQUARENTENA:\n• Itens em quarentena: {self.system_data['quarantine_items']}\n\nMODO ANJO CAÍDO:\n• Status: {'ATIVO' if self.fallen_angel_active else 'INATIVO'}\n• Sistema ML: {ml_status}\n• Engine ML: {ml_engine}\n• Processos eliminados: {self.system_data['processes_killed']}\n\nREDE:\n• WiFi: {'Ativo' if self.system_data['wifi_enabled'] else 'Inativo'}\n• USB: {'Ativo' if self.system_data['usb_enabled'] else 'Inativo'}\n\nSISTEMA:\n• Inicialização automática: {'Ativa' if self.system_data['startup_enabled'] else 'Inativa'}\n• Cache ML: {'Ativo' if ML_AVAILABLE else 'Inativo'}\n• Anti-oscilação: {'Ativo' if self.fallen_angel_active else 'Inativo'}"
            if TKINTER_AVAILABLE:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showinfo("Estatísticas Detalhadas", stats_text)
                root.destroy()
            else:
                QMessageBox.information(self, "Estatísticas Detalhadas", stats_text)
        except Exception as e:
            print(f"Erro ao mostrar estatísticas: {e}")
    
    def show_scan_page(self):
        self.clear_content()
        if self.is_scanning and hasattr(self, 'scan_progress_card'):
            self.content_layout.addWidget(self.scan_progress_card)
        
        options_frame = QFrame()
        options_layout = QGridLayout(options_frame)
        options_layout.setSpacing(20)
        scan_options = [("", "Verificação Rápida", "Análise de arquivos críticos", "quick"), ("", "Verificação Completa", "Análise de todo o sistema", "full"), ("", "Verificação Anjo Caído", "Verificação AGRESSIVA com ML", "fallen_angel"), ("", "Verificação Personalizada", "Escolha diretórios", "custom")]
        for i, (icon, title, desc, scan_type) in enumerate(scan_options):
            row, col = divmod(i, 2)
            options_layout.addWidget(self.create_scan_option_card(icon, title, desc, scan_type), row, col)
        self.content_layout.addWidget(options_frame)
        
        results_card = QFrame()
        results_card.setObjectName("scan_results_card")
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(15)
        results_title = QLabel("Última Verificação")
        results_title.setObjectName("activity_title")
        results_layout.addWidget(results_title)
        
        results_info = QLabel(f"Horário: {self.system_data['last_scan_time']}\nArquivos: {self.system_data['last_scan_files']:,}\nDuração: {self.system_data['last_scan_duration']}\nAmeaças: {self.system_data['threats_blocked']}") if self.system_data['last_scan_time'] != 'Nunca' else QLabel("Nenhuma verificação realizada.")
        results_info.setObjectName("activity_text")
        results_info.setWordWrap(True)
        results_layout.addWidget(results_info)
        self.content_layout.addWidget(results_card)
        self.content_layout.addStretch()
    
    def create_scan_option_card(self, icon, title, desc, scan_type):
        card = QFrame()
        card.setObjectName("scan_option")
        card.setFixedHeight(200)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        title_label = QLabel(title)
        title_label.setObjectName("scan_title")
        title_label.setAlignment(Qt.AlignCenter)
        
        desc_label = QLabel(desc)
        desc_label.setObjectName("scan_desc")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        if scan_type == "fallen_angel":
            ml_info = QLabel(f"ML Engine: {'LightGBM' if LIGHTGBM_AVAILABLE else 'Heurístico'}")
            ml_info.setObjectName("scan_ml_info")
            ml_info.setAlignment(Qt.AlignCenter)
            layout.addWidget(ml_info)
        
        if not self.is_scanning:
            card.mousePressEvent = lambda event: self.start_scan_type(scan_type)
            card.setCursor(Qt.PointingHandCursor)
        else:
            card.setEnabled(False)
        return card
    
    def create_scan_progress_card(self):
        card = QFrame()
        card.setObjectName("scan_progress_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        mode_text = "VERIFICAÇÃO ANJO CAÍDO" if self.fallen_angel_active else "Verificação em Andamento"
        if self.fallen_angel_active and ML_AVAILABLE:
            mode_text += " (ML ATIVO)"
        title = QLabel(mode_text)
        title.setObjectName("scan_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.scan_progress_bar = QProgressBar()
        self.scan_progress_bar.setObjectName("scan_progress")
        self.scan_progress_bar.setFixedHeight(25)
        self.scan_progress_bar.setRange(0, 100)
        self.scan_progress_bar.setValue(0)
        layout.addWidget(self.scan_progress_bar)
        
        self.scan_progress_label = QLabel("Preparando verificação...")
        self.scan_progress_label.setObjectName("scan_progress_text")
        self.scan_progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.scan_progress_label)
        
        self.current_file_label = QLabel("")
        self.current_file_label.setObjectName("scan_file_text")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)
        
        stop_btn = QPushButton("Parar Verificação")
        stop_btn.setObjectName("stop_button")
        stop_btn.setFixedHeight(35)
        stop_btn.clicked.connect(self.stop_scan)
        stop_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(stop_btn)
        return card
    
    def show_quarantine_page(self):
        self.clear_content()
        quarantined_files = self.quarantine_manager.get_quarantined_files()
        
        if not quarantined_files:
            clean_frame = QFrame()
            clean_frame.setObjectName("status_card")
            layout = QVBoxLayout(clean_frame)
            layout.setContentsMargins(60, 60, 60, 60)
            layout.setAlignment(Qt.AlignCenter)
            layout.setSpacing(20)
            title = QLabel("Sistema Limpo")
            title.setObjectName("status_title")
            title.setAlignment(Qt.AlignCenter)
            desc = QLabel("Nenhuma ameaça em quarentena")
            desc.setObjectName("status_desc")
            desc.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            layout.addWidget(desc)
            self.content_layout.addWidget(clean_frame)
        else:
            quarantine_frame = QFrame()
            quarantine_frame.setObjectName("quarantine_list")
            layout = QVBoxLayout(quarantine_frame)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            title = QLabel(f"Arquivos em Quarentena ({len(quarantined_files)})")
            title.setObjectName("activity_title")
            layout.addWidget(title)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)
            
            for file_data in quarantined_files:
                ml_enabled, model_used = (False, "Heuristic")
                if len(file_data) >= 9:
                    file_id, original_path, threat_type, description, quarantined_at, reason, confidence, ml_enabled_val, model_used = file_data
                    ml_enabled = bool(ml_enabled_val)
                else:
                    file_id, original_path, threat_type, description, quarantined_at, reason, confidence = file_data[:7]
                
                scroll_layout.addWidget(self.create_quarantine_file_card(file_id, original_path, threat_type, description, quarantined_at, reason, confidence, ml_enabled, model_used))
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
            self.content_layout.addWidget(quarantine_frame)
        self.content_layout.addStretch()
    
    def create_quarantine_file_card(self, file_id, original_path, threat_type, description, quarantined_at, reason, confidence, ml_enabled=False, model_used="Heuristic"):
        card = QFrame()
        card.setObjectName("quarantine_file_card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        info_layout = QVBoxLayout()
        filename_label = QLabel(os.path.basename(original_path))
        filename_label.setObjectName("quarantine_filename")
        info_layout.addWidget(filename_label)

        path_label = QLabel(f"Caminho: {original_path}")
        path_label.setObjectName("quarantine_path")
        path_label.setWordWrap(True)
        info_layout.addWidget(path_label)

        threat_label = QLabel(f"Tipo: {threat_type}")
        threat_label.setObjectName("quarantine_threat")
        info_layout.addWidget(threat_label)

        if confidence > 0:
            confidence_label = QLabel(f"Confiança: {confidence:.1%}")
            confidence_label.setObjectName("quarantine_confidence")
            info_layout.addWidget(confidence_label)
        if ml_enabled:
            ml_label = QLabel(f"Detectado por ML ({model_used})")
            ml_label.setObjectName("quarantine_ml")
            info_layout.addWidget(ml_label)
        if reason:
            reason_label = QLabel(f"Motivo: {reason}")
            reason_label.setObjectName("quarantine_reason")
            reason_label.setWordWrap(True)
            info_layout.addWidget(reason_label)
        
        date_label = QLabel(f"Quarentena: {quarantined_at}")
        date_label.setObjectName("quarantine_date")
        info_layout.addWidget(date_label)
        
        layout.addLayout(info_layout, 1)
        
        actions_layout = QVBoxLayout()
        restore_btn = QPushButton("Restaurar")
        restore_btn.setObjectName("restore_button")
        restore_btn.setFixedSize(100, 30)
        restore_btn.setCursor(Qt.PointingHandCursor)
        restore_btn.clicked.connect(lambda: self.restore_quarantine_file(file_id))
        
        delete_btn = QPushButton("Deletar")
        delete_btn.setObjectName("delete_button")
        delete_btn.setFixedSize(100, 30)
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_quarantine_file(file_id))

        actions_layout.addWidget(restore_btn)
        actions_layout.addWidget(delete_btn)
        layout.addLayout(actions_layout)
        return card
    
    def show_fallen_angel_page(self):
        self.clear_content()
        warning_frame = QFrame()
        warning_frame.setObjectName("fallen_angel_warning")
        warning_frame.setFixedHeight(250)

        layout = QVBoxLayout(warning_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        title = QLabel("MODO ANJO CAÍDO")
        title.setObjectName("fallen_angel_title")
        title.setAlignment(Qt.AlignCenter)
        
        desc = QLabel("PROTEÇÃO MÁXIMA BERSERK COM ML OFFLINE")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: white; font-weight: bold;")
        
        status_text = "ATIVADO" + (" (ML ATIVO)" if ML_AVAILABLE else "") if self.fallen_angel_active else "ATIVAR MODO ANJO CAÍDO"
        activate_btn = QPushButton(status_text)
        activate_btn.setObjectName("fallen_angel_button")
        activate_btn.setFixedSize(350, 50)
        activate_btn.setCursor(Qt.PointingHandCursor)
        activate_btn.clicked.connect(self.activate_fallen_angel)
        
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(activate_btn)
        self.content_layout.addWidget(warning_frame)
        
        features_card = QFrame()
        features_card.setObjectName("fallen_angel_info")
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(20, 20, 20, 20)
        features_layout.setSpacing(15)
        
        features_title = QLabel("Funcionalidades Ativadas")
        features_title.setObjectName("fallen_angel_info_title")
        features_layout.addWidget(features_title)

        if self.fallen_angel_active:
            ml_status = "ML ATIVO" if ML_AVAILABLE else "ML INDISPONÍVEL"
            engine_type = "LightGBM" if LIGHTGBM_AVAILABLE else "Heurístico"
            
            status_info = QLabel(f"Status: {ml_status} ({engine_type})")
            status_info.setObjectName("fallen_angel_info_title")
            status_info.setAlignment(Qt.AlignCenter)
            features_layout.addWidget(status_info)
            
            kill_status = QLabel(f"Processos Eliminados: {self.system_data['processes_killed']}")
            kill_status.setObjectName("fallen_angel_info_title")
            kill_status.setAlignment(Qt.AlignCenter)
            features_layout.addWidget(kill_status)
        
        self.content_layout.addWidget(features_card)
        self.content_layout.addStretch()
    
    def show_realtime_page(self):
        self.clear_content()
        status_title = "Proteção Ativa" if self.realtime_protection.monitoring else "Proteção Inativa"
        status_desc = "Monitoramento em tempo real ativo" if self.realtime_protection.monitoring else "Proteção desativada"
        self.content_layout.addWidget(self.create_status_card(status_title, status_desc))
        
        controls_frame = QFrame()
        controls_frame.setObjectName("realtime_controls")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(15)
        
        controls_title = QLabel("Controles de Proteção")
        controls_title.setObjectName("activity_title")
        controls_layout.addWidget(controls_title)
        
        toggle_layout = QHBoxLayout()
        toggle_layout.addWidget(QLabel("Proteção em Tempo Real:", objectName="activity_text"))
        toggle_layout.addStretch()
        
        self.realtime_toggle = QPushButton("Desativar" if self.realtime_protection.monitoring else "Ativar")
        self.realtime_toggle.setObjectName("toggle_button")
        self.realtime_toggle.setFixedSize(120, 35)
        self.realtime_toggle.setCursor(Qt.PointingHandCursor)
        self.realtime_toggle.clicked.connect(self.toggle_realtime_protection)
        toggle_layout.addWidget(self.realtime_toggle)
        controls_layout.addLayout(toggle_layout)
        
        angel_layout = QHBoxLayout()
        angel_layout.addWidget(QLabel("Modo Anjo Caído:", objectName="activity_text"))
        angel_status_text = "ATIVO" + (" (ML)" if ML_AVAILABLE else "") if self.fallen_angel_active else "Inativo"
        angel_status = QLabel(angel_status_text)
        angel_status.setObjectName("activity_text")
        angel_status.setStyleSheet(f"color: {'#ff4444' if self.fallen_angel_active else '#55ff55'};")
        angel_layout.addWidget(angel_status)
        angel_layout.addStretch()
        controls_layout.addLayout(angel_layout)
        
        self.content_layout.addWidget(controls_frame)
        self.content_layout.addStretch()
    
    def show_firewall_page(self):
        self.clear_content()
        firewall_title = "Firewall Ativo" if self.network_manager.wifi_enabled else "Conectividade Limitada"
        firewall_desc = "Monitoramento de rede ativo" if self.network_manager.wifi_enabled else "WiFi e USB bloqueados"
        self.content_layout.addWidget(self.create_status_card(firewall_title, firewall_desc))
        
        controls_frame = QFrame()
        controls_frame.setObjectName("firewall_controls")
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(20)
        controls_layout.addWidget(QLabel("Controles de Firewall", objectName="activity_title"))
        
        wifi_layout = QHBoxLayout()
        wifi_layout.addWidget(QLabel("WiFi:", objectName="activity_text"))
        wifi_status = QLabel("Ativado" if self.network_manager.wifi_enabled else "Desativado")
        wifi_status.setObjectName("activity_text")
        wifi_status.setStyleSheet(f"color: {'#55FF7F' if self.network_manager.wifi_enabled else '#FF5555'};")
        wifi_layout.addWidget(wifi_status)
        wifi_layout.addStretch()
        self.wifi_toggle = QPushButton("Desativar" if self.network_manager.wifi_enabled else "Ativar")
        self.wifi_toggle.setObjectName("toggle_button")
        self.wifi_toggle.setFixedSize(120, 35)
        self.wifi_toggle.setCursor(Qt.PointingHandCursor)
        self.wifi_toggle.clicked.connect(self.toggle_wifi)
        wifi_layout.addWidget(self.wifi_toggle)
        controls_layout.addLayout(wifi_layout)
        
        usb_layout = QHBoxLayout()
        usb_layout.addWidget(QLabel("Portas USB:", objectName="activity_text"))
        usb_status = QLabel("Ativado" if self.network_manager.usb_enabled else "Desativado")
        usb_status.setObjectName("activity_text")
        usb_status.setStyleSheet(f"color: {'#55FF7F' if self.network_manager.usb_enabled else '#FF5555'};")
        usb_layout.addWidget(usb_status)
        usb_layout.addStretch()
        self.usb_toggle = QPushButton("Desativar" if self.network_manager.usb_enabled else "Ativar")
        self.usb_toggle.setObjectName("toggle_button")
        self.usb_toggle.setFixedSize(120, 35)
        self.usb_toggle.setCursor(Qt.PointingHandCursor)
        self.usb_toggle.clicked.connect(self.toggle_usb)
        usb_layout.addWidget(self.usb_toggle)
        controls_layout.addLayout(usb_layout)
        
        emergency_btn = QPushButton("BLOQUEIO DE EMERGÊNCIA")
        emergency_btn.setObjectName("emergency_button")
        emergency_btn.setFixedHeight(50)
        emergency_btn.setCursor(Qt.PointingHandCursor)
        emergency_btn.clicked.connect(self.emergency_lockdown)
        controls_layout.addWidget(emergency_btn)
        self.content_layout.addWidget(controls_frame)
        self.content_layout.addStretch()
    
    def show_settings_page(self):
        self.clear_content()
        general_frame = QFrame()
        general_frame.setObjectName("settings_card")
        general_layout = QVBoxLayout(general_frame)
        general_layout.setContentsMargins(20, 20, 20, 20)
        general_layout.setSpacing(20)
        general_layout.addWidget(QLabel("Configurações Gerais", objectName="activity_title"))
        
        if WINDOWS_AVAILABLE and self.startup_control:
            startup_layout = QHBoxLayout()
            startup_layout.addWidget(QLabel("Iniciar com o Windows:", objectName="activity_text"))
            startup_status = QLabel("Ativado" if self.startup_control.is_enabled() else "Desativado")
            startup_status.setObjectName("activity_text")
            startup_status.setStyleSheet(f"color: {'#55FF7F' if self.startup_control.is_enabled() else '#FF5555'};")
            startup_layout.addWidget(startup_status)
            startup_layout.addStretch()
            self.startup_toggle = QPushButton("Desativar" if self.startup_control.is_enabled() else "Ativar")
            self.startup_toggle.setObjectName("toggle_button")
            self.startup_toggle.setFixedSize(120, 35)
            self.startup_toggle.setCursor(Qt.PointingHandCursor)
            self.startup_toggle.clicked.connect(self.toggle_startup)
            startup_layout.addWidget(self.startup_toggle)
            general_layout.addLayout(startup_layout)
        
        for name, desc, value_func, handler in [("Tema escuro", "Interface com tema escuro", lambda: self.dark_mode, self.toggle_theme_handler), ("Proteção em tempo real", "Monitoramento contínuo", lambda: self.realtime_protection.monitoring, self.toggle_realtime_protection_handler), ("Pop-ups de alerta", "Mostrar alertas em tempo real", lambda: self.alert_system.popup_enabled, self.toggle_popup_alerts)]:
            setting_layout = QHBoxLayout()
            info_layout = QVBoxLayout()
            name_label = QLabel(name)
            name_label.setObjectName("activity_text")
            info_layout.addWidget(name_label)
            desc_label = QLabel(desc)
            desc_label.setObjectName("quarantine_date")
            desc_label.setWordWrap(True)
            info_layout.addWidget(desc_label)
            setting_layout.addLayout(info_layout, 1)
            toggle = QCheckBox()
            toggle.setChecked(value_func())
            toggle.stateChanged.connect(handler)
            setting_layout.addWidget(toggle)
            general_layout.addLayout(setting_layout)
        
        ml_info_layout = QVBoxLayout()
        ml_title = QLabel("Sistema de Machine Learning")
        ml_title.setObjectName("activity_text")
        ml_info_layout.addWidget(ml_title)
        ml_status = "Ativo (modo anjo caído)" if ML_AVAILABLE else "Indisponível"
        engine_info = f"Engine: {'LightGBM' if LIGHTGBM_AVAILABLE else 'Heurístico fallback'}"
        ml_desc = QLabel(f"Status: {ml_status}\n{engine_info}")
        ml_desc.setObjectName("quarantine_date")
        ml_desc.setWordWrap(True)
        ml_info_layout.addWidget(ml_desc)
        general_layout.addLayout(ml_info_layout)
        
        self.content_layout.addWidget(general_frame)
        self.content_layout.addStretch()

    def toggle_theme_handler(self, state): self.toggle_theme()
    def toggle_realtime_protection_handler(self, state): self.toggle_realtime_protection()
    
    def show_backup_page(self):
        self.clear_content()
        self.content_layout.addWidget(self.create_status_card("Sistema de Backup", "Backups automáticos configurados"))
        options_frame = QFrame()
        options_layout = QGridLayout(options_frame)
        options_layout.setSpacing(20)
        backup_options = [("", "Backup Completo", "Backup de arquivos importantes"), ("", "Backup Rápido", "Backup de arquivos críticos"), ("", "Backup Incremental", "Backup de alterações"), ("", "Backup Agendado", "Configurar backups")]
        for i, (icon, title, desc) in enumerate(backup_options):
            row, col = divmod(i, 2)
            options_layout.addWidget(self.create_backup_option_card(icon, title, desc), row, col)
        self.content_layout.addWidget(options_frame)
        self.content_layout.addStretch()
    
    def create_backup_option_card(self, icon, title, desc):
        card = QFrame()
        card.setObjectName("backup_option")
        card.setFixedHeight(150)
        card.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setObjectName("backup_title")
        title_label.setAlignment(Qt.AlignCenter)
        
        desc_label = QLabel(desc)
        desc_label.setObjectName("backup_desc")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        card.mousePressEvent = lambda event: self.start_backup(title)
        return card
    
    def show_simple_page(self, page_id):
        self.clear_content()
        if page_id == 'performance':
            self.content_layout.addWidget(self.create_status_card("Performance", "Sistema otimizado"))
        self.content_layout.addStretch()
    
    def start_quick_scan(self):
        if self.is_scanning: return
        dirs = [os.path.expanduser(p) for p in ["~/Downloads", "~/Desktop", "~/Documents"]]
        self._start_scan(dirs, "quick", False)
    
    def start_scan_type(self, scan_type):
        if self.is_scanning: return
        scan_map = {"quick": self.start_quick_scan, "full": self.start_full_scan, "fallen_angel": self.start_fallen_angel_scan, "custom": self.start_custom_scan}
        scan_map.get(scan_type, lambda: None)()
    
    def start_full_scan(self):
        if self.is_scanning: return
        dirs = [f"{chr(c)}:\\" for c in range(ord('A'), ord('Z') + 1) if os.path.exists(f"{chr(c)}:\\")] if os.name == 'nt' else ["/", "/home", "/usr"]
        self._start_scan(dirs, "full", False)
    
    def start_fallen_angel_scan(self):
        if self.is_scanning: return
        if not self.fallen_angel_active:
            self.activate_fallen_angel()
        dirs = ["C:\\"] if os.name == 'nt' else ["/"]
        self._start_scan(dirs, "fallen_angel", True)
    
    def start_custom_scan(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório")
        if directory and not self.is_scanning:
            self._start_scan([directory], "custom", self.fallen_angel_active)
    
    def _start_scan(self, directories: List[str], scan_type: str, fallen_angel_mode: bool):
        try:
            self.is_scanning = True
            self.scan_progress_card = self.create_scan_progress_card()
            if self.current_tab == 'scan':
                self.content_layout.insertWidget(0, self.scan_progress_card)
            
            self.current_scan_worker = self.scanner.start_scan(directories, scan_type, fallen_angel_mode)
            self.current_scan_worker.progress_updated.connect(self.update_scan_progress)
            self.current_scan_worker.file_scanned.connect(self.on_file_scanned)
            self.current_scan_worker.threat_found.connect(self.on_threat_found)
            self.current_scan_worker.scan_completed.connect(self.on_scan_completed)
            self.current_scan_worker.scan_status.connect(self.on_scan_status)
            self.current_scan_worker.start()
        except Exception as e:
            print(f"Erro ao iniciar verificação: {e}")
            self.is_scanning = False
    
    def stop_scan(self):
        if self.current_scan_worker and self.current_scan_worker.isRunning():
            self.current_scan_worker.request_stop()
        self.scanner.stop_scan()
        self.is_scanning = False
        if hasattr(self, 'scan_progress_card'):
            self.scan_progress_card.deleteLater()
            delattr(self, 'scan_progress_card')
        if self.current_tab == 'scan':
            QTimer.singleShot(100, self.show_scan_page)
    
    def update_scan_progress(self, progress):
        if hasattr(self, 'scan_progress_bar'):
            self.scan_progress_bar.setValue(progress)
            if hasattr(self, 'scan_progress_label'):
                mode_text = "MODO ANJO CAÍDO" + (" (ML)" if ML_AVAILABLE else "") if self.fallen_angel_active else "modo normal"
                self.scan_progress_label.setText(f"Progresso: {progress}% ({mode_text})")
    
    def on_file_scanned(self, filename):
        if hasattr(self, 'current_file_label'):
            self.current_file_label.setText(f"Verificando: {filename[:47] + '...' if len(filename) > 50 else filename}")
    
    def on_scan_status(self, status):
        if hasattr(self, 'scan_progress_label'):
            self.scan_progress_label.setText(status)
    
    def on_threat_found(self, file_path, threat_type, description):
        try:
            confidence = 0.8 if threat_type == "Malware" else 0.6
            ml_enabled = self.fallen_angel_active and ML_AVAILABLE
            model_used = "LightGBM" if LIGHTGBM_AVAILABLE and ml_enabled else "Heuristic"
            if self.quarantine_manager.quarantine_file(file_path, threat_type, description, f"Detectado como {threat_type}", confidence, ml_enabled, model_used):
                self.system_data['threats_blocked'] += 1
                self.system_data['quarantine_items'] += 1
                if ml_enabled: self.system_data['ml_detections'] += 1
                self.alert_system.show_threat_alert({'file_path': file_path, 'threat_type': threat_type, 'confidence': confidence, 'model_used': model_used})
        except Exception as e:
            print(f"Erro ao processar ameaça: {e}")
    
    def on_scan_completed(self, files_scanned, threats_found, threat_list):
        self.is_scanning = False
        self.system_data['files_scanned'] += files_scanned
        self.system_data['last_scan_files'] = files_scanned
        self.system_data['last_scan_time'] = datetime.now().strftime("%H:%M")
        if hasattr(self, 'scan_progress_card'):
            self.scan_progress_card.deleteLater()
            delattr(self, 'scan_progress_card')
        self.save_system_data()
        
        if self.current_tab in ['home', 'scan', 'quarantine']:
            QTimer.singleShot(100, getattr(self, f"show_{self.current_tab}_page"))
        
        self.show_scan_result_popup(files_scanned, threats_found)
    
    def show_scan_result_popup(self, files_scanned, threats_found):
        try:
            if TKINTER_AVAILABLE:
                ml_info = f"\nEngine ML: {'LightGBM' if LIGHTGBM_AVAILABLE else 'Heurístico'}" if self.fallen_angel_active and ML_AVAILABLE else ""
                text = f"Verificação concluída!\n\nArquivos: {files_scanned:,}\nAmeaças: {threats_found}\nArquivos movidos para quarentena.{ml_info}" if threats_found > 0 else f"Verificação concluída!\n\nArquivos: {files_scanned:,}\nNenhuma ameaça encontrada.\nSistema limpo.{ml_info}"
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                (messagebox.showwarning if threats_found > 0 else messagebox.showinfo)("Verificação Concluída", text)
                root.destroy()
        except Exception as e:
            print(f"Erro ao mostrar popup: {e}")

    def on_threat_alert(self, threat_info): pass
    
    def on_process_killed_alert(self, process_info):
        self.system_data['processes_killed'] += 1
    
    def toggle_wifi(self):
        if self.network_manager.toggle_wifi():
            self.system_data['wifi_enabled'] = self.network_manager.wifi_enabled
            self.save_system_data()
            if self.current_tab == 'firewall': self.show_firewall_page()
        else:
            QMessageBox.warning(self, "Erro", "Falha ao alterar WiFi. Execute como administrador.")
    
    def toggle_usb(self):
        if self.network_manager.toggle_usb():
            self.system_data['usb_enabled'] = self.network_manager.usb_enabled
            self.save_system_data()
            if self.current_tab == 'firewall': self.show_firewall_page()
        else:
            QMessageBox.warning(self, "Erro", "Falha ao alterar USB. Execute como administrador.")
    
    def emergency_lockdown(self):
        reply = QMessageBox.question(self, "Bloqueio de Emergência", "ATENÇÃO: Desativar WiFi e USB!\n\nContinuar?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.network_manager.emergency_lockdown():
                self.system_data.update({'wifi_enabled': False, 'usb_enabled': False})
                self.save_system_data()
                QMessageBox.information(self, "Bloqueio Ativado", "WiFi e USB foram desabilitados.")
                if self.current_tab == 'firewall': self.show_firewall_page()
            else:
                QMessageBox.warning(self, "Erro", "Falha no bloqueio. Execute como administrador.")
    
    def toggle_startup(self):
        if self.startup_control and self.startup_control.toggle():
            self.system_data['startup_enabled'] = self.startup_control.is_enabled()
            self.save_system_data()
            if self.current_tab == 'settings': self.show_settings_page()
            QMessageBox.information(self, "Configuração Alterada", f"Inicialização automática {'ativada' if self.startup_control.is_enabled() else 'desativada'}.")
        else:
            QMessageBox.warning(self, "Erro", "Falha ao alterar configuração de inicialização.")
    
    def activate_fallen_angel(self):
        self.fallen_angel_active = not self.fallen_angel_active
        self.process_killer.set_fallen_angel_mode(self.fallen_angel_active)
        if self.fallen_angel_active:
            engine = f" com ML ({'LightGBM' if LIGHTGBM_AVAILABLE else 'Heurístico'})" if ML_AVAILABLE else ""
            warning_text = f"MODO ANJO CAÍDO ATIVADO!\n\nEste modo é agressivo e pode eliminar processos .\n\nUse apenas em situações de emergência.{engine}"
            QMessageBox.warning(self, "MODO ANJO CAÍDO ATIVADO", warning_text)
            if not self.realtime_protection.monitoring:
                self.realtime_protection.start_monitoring()
        else:
            QMessageBox.information(self, "Modo Normal", "Modo Anjo Caído desativado.\nProteção retornada ao normal.")
        self.show_fallen_angel_page()
    
    def toggle_realtime_protection(self):
        if self.realtime_protection.monitoring:
            self.realtime_protection.stop_monitoring()
        else:
            self.realtime_protection.start_monitoring()
        if self.current_tab == 'realtime': self.show_realtime_page()
    
    def toggle_popup_alerts(self, state):
        self.alert_system.popup_enabled = bool(state)
    
    def restore_quarantine_file(self, file_id):
        if self.quarantine_manager.restore_file(file_id):
            self.system_data['quarantine_items'] -= 1
            self.save_system_data()
            self.show_quarantine_page()
            QMessageBox.information(self, "Sucesso", "Arquivo restaurado com sucesso!")
        else:
            QMessageBox.warning(self, "Erro", "Erro ao restaurar arquivo!")
    
    def delete_quarantine_file(self, file_id):
        reply = QMessageBox.question(self, "Confirmar Exclusão", "Tem certeza que deseja deletar este arquivo permanentemente?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes and self.quarantine_manager.delete_quarantine_file(file_id):
            self.system_data['quarantine_items'] -= 1
            self.save_system_data()
            self.show_quarantine_page()
            QMessageBox.information(self, "Sucesso", "Arquivo deletado permanentemente!")
    
    def start_backup(self, backup_type):
        progress = QProgressDialog(f"Realizando {backup_type.lower()}...", "Cancelar", 0, 100, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.show()
        for i in range(101):
            if progress.wasCanceled(): break
            progress.setValue(i)
            QApplication.processEvents()
            time.sleep(0.01)
        progress.close()

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_btn.setText("☀️" if self.dark_mode else "🌙")
        self.apply_theme()
    
    def apply_theme(self):
        dark_style = """QMainWindow{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0f0f0f,stop:1 #0f0f0f);color:#fff;font-family:'Segoe UI',sans-serif}QWidget{background-color:transparent;color:#fff}QFrame#sidebar{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a1a1a,stop:1 #2d2d2d);border-right:2px solid #444}QFrame#sidebar_header{border-bottom:2px solid #444}QLabel#logo{background:transparent; border-radius:15px;}QLabel#app_title{color:#ffd700;font-size:20px;font-weight:700}QLabel#app_subtitle{color:#ccc;font-size:12px;font-weight:600}QPushButton#theme_toggle{background-color:#404040;border:2px solid #666;border-radius:8px;color:#fff}QPushButton#theme_toggle:hover{background-color:#ffd700;color:#000}QLabel#nav_section_title{color:#888;font-size:11px;font-weight:700}QPushButton#nav_item{background-color:transparent;border:none;color:#ccc;text-align:left;padding:12px 20px;margin:2px 10px;border-radius:10px;font-weight:500}QPushButton#nav_item:hover{background-color:rgba(255,215,0,.2);color:#ffd700}QPushButton#nav_item[active=true]{background-color:rgba(255,215,0,.3);color:#ffd700;border-left:4px solid #ffd700;font-weight:600}QPushButton#nav_item_special{border:none;color:#ff4444;text-align:left;padding:12px 20px;margin:2px 10px;border-radius:10px;font-weight:700}QPushButton#nav_item_special:hover{background-color:rgba(255,68,68,.2)}QFrame#main_content,QScrollArea#content_scroll{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #0f0f0f,stop:1 #0f0f0f)}QFrame#main_header{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a1a1a,stop:1 #2d2d2d);border-bottom:2px solid #444}QLabel#page_title{font-size:24px;font-weight:700}QPushButton#primary_button{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffd700,stop:1 #d4af37);color:#000;border:none;border-radius:10px;font-weight:600}QPushButton#primary_button:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ffb700,stop:1 #d4af37)}QFrame#status_card,QFrame#activity_card,QFrame#stat_card,QFrame#scan_option,QFrame#quarantine_list,QFrame#scan_progress_card,QFrame#realtime_controls,QFrame#backup_option,QFrame#scan_results_card,QFrame#firewall_controls,QFrame#settings_card{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #2d2d2d,stop:1 #404040);border:2px solid #555;border-radius:16px}QFrame#status_card_main{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(255,215,0,.3),stop:1 rgba(255,215,0,.1));border:2px solid #ffd700}QLabel#status_title{color:#ffd700;font-size:24px;font-weight:700}QLabel#status_desc{font-size:16px}QLabel#stat_value{color:#ffd700;font-size:24px;font-weight:700}QLabel#stat_label{font-weight:600}QLabel#activity_title,QLabel#scan_title,QLabel#backup_title{color:#ffd700;font-size:18px;font-weight:700}QLabel#activity_text{font-size:15px}QLabel#activity_time{color:#ccc;font-size:13px}QLabel#scan_desc,QLabel#backup_desc{font-size:14px}QLabel#scan_ml_info{color:#6f6;font-size:12px;font-weight:700}QProgressBar#scan_progress{border:2px solid #555;border-radius:8px;background-color:#2d2d2d;text-align:center;color:#fff}QProgressBar#scan_progress::chunk{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ffd700,stop:1 #ffb700);border-radius:6px}QPushButton#stop_button,QPushButton#toggle_button,QPushButton#delete_button{background-color:#c44;color:#fff;border:none;border-radius:8px;font-weight:600}QPushButton#stop_button:hover,QPushButton#toggle_button:hover,QPushButton#delete_button:hover{background-color:#a22}QFrame#quarantine_file_card{background-color:#404040;border:1px solid #666;border-radius:10px}QLabel#quarantine_filename{color:#ffd700;font-weight:700;font-size:16px}QLabel#quarantine_path,QLabel#quarantine_date{color:#ccc;font-size:12px}QLabel#quarantine_threat{color:#f66}QLabel#quarantine_confidence{color:#6f6}QLabel#quarantine_ml{color:#6ff;font-weight:700}QLabel#quarantine_reason{color:#fa4}QPushButton#restore_button{background-color:#4a4;color:#fff;border:none;border-radius:6px;font-weight:600}QPushButton#restore_button:hover{background-color:#393}QFrame#fallen_angel_warning{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #800,stop:1 red);border:2px solid red;border-radius:15px}QLabel#fallen_angel_title{color:#ff0;font-size:28px;font-weight:700}QPushButton#fallen_angel_button{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #800,stop:1 red);color:#ff0;border:2px solid #ff0;border-radius:10px;font-weight:700;font-size:16px}QPushButton#fallen_angel_button:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 red,stop:1 #800)}QFrame#fallen_angel_info{background:rgba(139,0,0,.3);border:2px solid rgba(255,0,0,.5);border-radius:16px}QLabel#fallen_angel_info_title{color:#f44;font-size:18px;font-weight:700}QCheckBox::indicator:unchecked{background-color:#404040;border:2px solid #666}QCheckBox::indicator:checked{background-color:#ffd700;border:2px solid #ffb700}QScrollArea{border:none}QScrollArea#nav_scroll{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a1a1a,stop:1 #2d2d2d)}QScrollBar:vertical{background-color:#404040;width:12px;border-radius:6px}QScrollBar::handle:vertical{background-color:#ffd700;border-radius:6px;min-height:20px}QScrollBar::handle:vertical:hover{background-color:#ffb700}QPushButton#emergency_button{background-color:#c44;color:#fff;border:2px solid red;border-radius:8px;font-weight:700;font-size:16px}QPushButton#emergency_button:hover{background-color:#a22}"""
        light_style = """QMainWindow{background:#f0f3f6;color:#2c3e50}QFrame#sidebar{background:#fff;border-right:1px solid #dcdcdc}QLabel#app_title{color:#2c3e50}QPushButton#nav_item[active=true]{background-color:#e8f0fe;color:#1967d2;border-left:4px solid #1967d2}QFrame#status_card_main{background:rgba(255,215,0,.15);border:2px solid rgba(255,215,0,.6)}QFrame,QFrame#status_card,QFrame#activity_card,QFrame#stat_card,QFrame#scan_option,QFrame#quarantine_list,QFrame#scan_progress_card,QFrame#realtime_controls,QFrame#backup_option,QFrame#scan_results_card,QFrame#firewall_controls,QFrame#settings_card{background-color:#fff;border:1px solid #dcdcdc;border-radius:12px}QLabel#logo{background:transparent;}"""
        self.setStyleSheet(dark_style if self.dark_mode else light_style)
    
    def load_system_data(self):
        data_file = self.app_data_dir / "system_data.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f: self.system_data.update(json.load(f))
            except Exception: pass
        self.system_data['quarantine_items'] = len(self.quarantine_manager.get_quarantined_files())
        self.system_data.update(self.network_manager.get_network_status())
        if self.startup_control:
            self.system_data['startup_enabled'] = self.startup_control.is_enabled()
    
    def save_system_data(self):
        data_file = self.app_data_dir / "system_data.json"
        try:
            with open(data_file, 'w') as f: json.dump(self.system_data, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Angle Guard", "A proteção continua ativa em segundo plano.", QSystemTrayIcon.Information, 2000)

    def quit_application(self):
        reply = QMessageBox.question(self, "Confirmar Saída", "Deseja fechar o Angle Guard?\nIsso encerrará a proteção.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.tray_icon.hide()
                if self.is_scanning: self.stop_scan()
                self.realtime_protection.stop_monitoring()
                if hasattr(self.process_killer.detection_system, 'cleanup_timer') and self.process_killer.detection_system.cleanup_timer:
                    self.process_killer.detection_system.cleanup_timer.cancel()
                self.save_system_data()
                print("Encerrando Angle Guard...")
            except Exception as e:
                print(f"Erro durante fechamento: {e}")
            finally:
                QApplication.instance().quit()

def create_test_threat():
    try:
        downloads_dir = Path.home() / "Downloads"
        test_file = downloads_dir / "Senhas.txt"
        with open(test_file, 'w') as f:
            f.write(r'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*')
        print(f"Arquivo de teste criado: {test_file}")
    except Exception as e:
        print(f"Erro ao criar arquivo de teste: {e}")

def main():
    if os.name == 'nt':
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("Não executando como administrador, tentando elevar...")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit(0)
        except Exception as e:
            print(f"Falha ao tentar elevar privilégios: {e}. Por favor, execute como administrador.")
            input("Pressione Enter para sair...")
            sys.exit(1)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    try:
        app.setFont(QFont("Segoe UI", 11))
    except Exception:
        pass
        
    window = AngleGuard()
    create_test_threat()
    window.show()
    
    print("Angle Guard iniciado com sucesso!")
    
    sys.exit(app.exec_() if QT_VERSION == 5 else app.exec())

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")
        sys.exit(1)
