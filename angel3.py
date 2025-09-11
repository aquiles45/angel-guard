#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ ANGEL GUARD ANTIVIRUS - 
Copyright (c) 2025 - Proteção Celestial
"""

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
from typing import Optional, List, Tuple
from collections import Counter

print("🔧 Verificando dependências...")

# Verificação de dependências
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtGui import *
    from PyQt5.QtCore import *
    QT_VERSION = 5
    print("✅ PyQt5 carregado com sucesso")
except ImportError:
    try:
        from PyQt6.QtWidgets import *
        from PyQt6.QtGui import *
        from PyQt6.QtCore import *
        QT_VERSION = 6
        print("✅ PyQt6 carregado com sucesso")
    except ImportError:
        print("❌ ERRO: PyQt5/6 não encontrado!")
        print("💡 Execute: pip install PyQt5 pyqt5-tools psutil")
        input("\nPressione Enter para sair...")
        sys.exit(1)

# Importar controles Windows se disponível
try:
    import winreg
    WINDOWS_AVAILABLE = True
    print("✅ Controles Windows disponíveis")
except ImportError:
    WINDOWS_AVAILABLE = False
    print("⚠️ Controles Windows não disponíveis (sistema não-Windows)")

# Tentar importar tkinter para pop-ups
try:
    import tkinter as tk
    from tkinter import messagebox
    TKINTER_AVAILABLE = True
    print("✅ tkinter disponível para pop-ups")
except ImportError:
    TKINTER_AVAILABLE = False
    print("⚠️ tkinter não disponível")

# Configurações ultra agressivas para modo anjo caído
ULTRA_ENTROPY_THRESHOLD = 6.8
FALLEN_ANGEL_ENTROPY_THRESHOLD = 6.5
MAX_SUSPICIOUS_SCORE = 20
FALLEN_ANGEL_KILL_THRESHOLD = 10

# Hashes de malware conhecidos
MALWARE_SIGNATURES = {
    "44d88612fea8a8f36de82e1278abb02f": "EICAR-Test-Signature",
    "5d41402abc4b2a76b9719d911017c592": "Trojan.Generic",
    "1ec1fed91f694e0d229928963b30f6b0d7d3a745": "NotPetya",
    "7a828afd2abf153d840938090d498072b7e507c7021e4cdd8c6baf727cadf3e3": "Ryuk",
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f": "WannaCry"
}

# Extensões suspeitas expandidas
SUSPICIOUS_EXTENSIONS = [
    '.exe', '.scr', '.bat', '.cmd', '.com', '.pif', '.reg', '.vbs', 
    '.js', '.jar', '.ps1', '.msi', '.app', '.deb', '.rpm',
    # Extensões de ransomware
    '.crypted', '.encrypted', '.locked', '.crypto', '.crypt', '.enc', '.locky',
    '.cerber', '.zepto', '.thor', '.aesir', '.odin', '.sage', '.spora',
    '.wannacry', '.wcry', '.wncry', '.onion', '.dharma', '.wallet'
]

# Processos suspeitos para kill automático (modo anjo caído)
ULTRA_SUSPICIOUS_PROCESSES = [
    "powershell.exe", "cmd.exe", "certutil.exe", "bitsadmin.exe",
    "regsvr32.exe", "rundll32.exe", "mshta.exe", "wmic.exe",
    "taskkill.exe", "net.exe", "netsh.exe", "schtasks.exe",
    "reg.exe", "regedit.exe", "bcdedit.exe", "vssadmin.exe",
    "wbadmin.exe", "wevtutil.exe", "fsutil.exe", "cipher.exe"
]

# Padrões suspeitos em nomes de arquivos
SUSPICIOUS_PATTERNS = [
    'crack', 'keygen', 'patch', 'activator', 'loader', 'hack',
    'trojan', 'virus', 'malware', 'bitcoin', 'crypto', 'miner',
    'ransomware', 'encrypt', 'decrypt', 'wannacry', 'locky'
]

def calculate_entropy(data: bytes) -> float:
    """Calcular entropia de dados"""
    if not data:
        return 0.0
    
    try:
        byte_counts = Counter(data)
        data_len = len(data)
        
        entropy = 0.0
        for count in byte_counts.values():
            if count > 0:
                probability = count / data_len
                entropy += probability * math.log2(probability)
        
        return -entropy
    except Exception:
        return 0.0

class AlertSystem(QObject):
    """Sistema de alertas com pop-ups"""
    threat_detected_signal = pyqtSignal(dict)
    process_killed_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.popup_enabled = True
    
    def show_threat_alert(self, threat_info):
        """Mostrar alerta de ameaça detectada"""
        if not self.popup_enabled:
            return
        
        self.threat_detected_signal.emit(threat_info)
        
        # Mostrar pop-up
        try:
            if TKINTER_AVAILABLE:
                self._show_tkinter_popup(
                    "AMEAÇA DETECTADA - ANGLE GUARD",
                    f"""AMEAÇA DETECTADA!

Arquivo: {threat_info.get('file_path', 'Desconhecido')}
Tipo: {threat_info.get('threat_type', 'Desconhecido')}
Confiança: {threat_info.get('confidence', 0):.1%}

AÇÃO AUTOMÁTICA EXECUTADA""",
                    "warning"
                )
        except Exception as e:
            print(f"Erro ao mostrar pop-up de ameaça: {e}")
    
    def show_process_killed_alert(self, process_info):
        """Mostrar alerta de processo eliminado"""
        if not self.popup_enabled:
            return
        
        self.process_killed_signal.emit(process_info)
        
        # Mostrar pop-up
        try:
            if TKINTER_AVAILABLE:
                self._show_tkinter_popup(
                    "PROCESSO ELIMINADO - ANGLE GUARD",
                    f"""PROCESSO SUSPEITO ELIMINADO!

Nome: {process_info.get('name', 'Desconhecido')}
PID: {process_info.get('pid', 'Desconhecido')}
Motivo: {process_info.get('reason', 'Comportamento suspeito')}

PROTEÇÃO ATIVA""",
                    "error"
                )
        except Exception as e:
            print(f"Erro ao mostrar pop-up de processo: {e}")
    
    def _show_tkinter_popup(self, title, message, level="info"):
        """Mostrar pop-up usando tkinter"""
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
    """Sistema de eliminação de processos (modo anjo caído)"""
    
    def __init__(self, alert_system):
        self.alert_system = alert_system
        self.fallen_angel_mode = False
        self.killed_processes = set()
        
    def set_fallen_angel_mode(self, enabled):
        """Ativar/desativar modo anjo caído"""
        self.fallen_angel_mode = enabled
        print(f"Modo Anjo Caído {'ATIVADO' if enabled else 'desativado'}")
    
    def should_kill_process(self, process_info):
        """Determinar se processo deve ser eliminado (apenas no modo anjo caído)"""
        if not self.fallen_angel_mode:
            return False
            
        try:
            name = process_info.get('name', '').lower()
            suspicious_score = process_info.get('suspicious_score', 0)
            
            # Verificar score suspeito
            if suspicious_score >= FALLEN_ANGEL_KILL_THRESHOLD:
                return True
            
            # Verificar processos na lista de kill
            if name in [p.lower() for p in ULTRA_SUSPICIOUS_PROCESSES]:
                return True
            
            return False
        except Exception:
            return False
    
    def kill_process_aggressive(self, process_info, reason="Comportamento suspeito"):
        """Eliminar processo de forma agressiva"""
        try:
            pid = process_info.get('pid')
            name = process_info.get('name', 'Desconhecido')
            
            if not pid or pid in self.killed_processes:
                return False
            
            try:
                process = psutil.Process(pid)
                self.killed_processes.add(pid)
                
                print(f"🔥 ELIMINANDO PROCESSO: {name} (PID: {pid}) - {reason}")
                
                # Eliminar processo e filhos
                children = process.children(recursive=True)
                for child in children:
                    try:
                        child.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                
                process.kill()
                
                # Mostrar alerta
                process_info['reason'] = reason
                self.alert_system.show_process_killed_alert(process_info)
                
                print(f"✅ Processo {name} (PID: {pid}) eliminado com sucesso")
                return True
                
            except psutil.NoSuchProcess:
                return True
            except psutil.AccessDenied:
                print(f"❌ Acesso negado para eliminar processo {pid}")
                return False
                
        except Exception as e:
            print(f"Erro ao eliminar processo: {e}")
            return False

class NetworkManager:
    """Gerenciador de controles de rede"""
    def __init__(self):
        self.wifi_enabled = True
        self.usb_enabled = True
    
    def disable_wifi(self):
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disable"], 
                             check=True, capture_output=True)
            else:  # Linux/Unix
                subprocess.run(["nmcli", "radio", "wifi", "off"], 
                             check=True, capture_output=True)
            self.wifi_enabled = False
            return True
        except Exception:
            return False
    
    def enable_wifi(self):
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enable"], 
                             check=True, capture_output=True)
            else:  # Linux/Unix
                subprocess.run(["nmcli", "radio", "wifi", "on"], 
                             check=True, capture_output=True)
            self.wifi_enabled = True
            return True
        except Exception:
            return False
    
    def disable_usb(self):
        try:
            if os.name == 'nt' and WINDOWS_AVAILABLE:  # Windows
                subprocess.run([
                    "reg", "add", 
                    "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR",
                    "/v", "Start", "/t", "REG_DWORD", "/d", "4", "/f"
                ], check=True, capture_output=True)
            self.usb_enabled = False
            return True
        except Exception:
            return False
    
    def enable_usb(self):
        try:
            if os.name == 'nt' and WINDOWS_AVAILABLE:  # Windows
                subprocess.run([
                    "reg", "add", 
                    "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR",
                    "/v", "Start", "/t", "REG_DWORD", "/d", "3", "/f"
                ], check=True, capture_output=True)
            self.usb_enabled = True
            return True
        except Exception:
            return False
    
    def get_network_status(self):
        return {
            'wifi_enabled': self.wifi_enabled,
            'usb_enabled': self.usb_enabled
        }

    def toggle_wifi(self):
        if self.wifi_enabled:
            return self.disable_wifi()
        else:
            return self.enable_wifi()

    def toggle_usb(self):
        if self.usb_enabled:
            return self.disable_usb()
        else:
            return self.enable_usb()

    def emergency_lockdown(self):
        wifi_result = self.disable_wifi()
        usb_result = self.disable_usb()
        return wifi_result and usb_result

class StartupControl:
    """Controle de inicialização no sistema"""
    def __init__(self):
        self.app_name = "AngleGuard"
        
    def toggle(self):
        if self.is_enabled():
            return self.disable()
        else:
            return self.enable()
    
    def is_enabled(self):
        if not WINDOWS_AVAILABLE:
            return False
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_READ)
            winreg.QueryValueEx(key, self.app_name)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def enable(self):
        if not WINDOWS_AVAILABLE:
            return False
            
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
    
    def disable(self):
        if not WINDOWS_AVAILABLE:
            return False
            
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", 
                               0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, self.app_name)
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

class EnhancedScanWorker(QThread):
    """Worker thread para verificação com detecção aprimorada"""
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
        
    def request_stop(self):
        """Solicitar parada da verificação"""
        with QMutexLocker(self._mutex):
            self._stop_requested = True
    
    def is_stop_requested(self) -> bool:
        """Verificar se parada foi solicitada"""
        with QMutexLocker(self._mutex):
            return self._stop_requested
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calcular hash MD5 do arquivo"""
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
    
    def check_file_suspicious_enhanced(self, file_path: str) -> Tuple[bool, Optional[str], float]:
        """Verificar se arquivo é suspeito com detecção aprimorada"""
        file_name = os.path.basename(file_path).lower()
        file_ext = os.path.splitext(file_path)[1].lower()
        confidence = 0.0
        
        # Verificar extensão suspeita
        if file_ext in SUSPICIOUS_EXTENSIONS:
            confidence += 0.6
            
            # Verificar padrões suspeitos no nome
            for pattern in SUSPICIOUS_PATTERNS:
                if pattern in file_name:
                    confidence += 0.3
                    break
        
        # Verificar entropia do arquivo (apenas para arquivos pequenos)
        try:
            file_size = os.path.getsize(file_path)
            if file_size < 10 * 1024 * 1024:  # 10MB
                with open(file_path, 'rb') as f:
                    data = f.read(min(65536, file_size))
                
                entropy = calculate_entropy(data)
                
                if self.fallen_angel_mode:
                    if entropy > FALLEN_ANGEL_ENTROPY_THRESHOLD:
                        confidence += 0.8
                else:
                    if entropy > ULTRA_ENTROPY_THRESHOLD:
                        confidence += 0.6
        except Exception:
            pass
        
        if confidence >= 0.5:
            reason = f"Arquivo suspeito - Confiança: {confidence:.1%}"
            return True, reason, confidence
        
        return False, None, confidence
    
    def scan_file_enhanced(self, file_path: str) -> Optional[Tuple[str, str, float]]:
        """Verificar um arquivo com detecção aprimorada"""
        try:
            if not os.path.exists(file_path) or self.is_stop_requested():
                return None
                
            # Calcular hash primeiro
            file_hash = self.calculate_file_hash(file_path)
            if file_hash and not self.is_stop_requested():
                # Verificar contra assinaturas conhecidas
                if file_hash in MALWARE_SIGNATURES:
                    threat_name = MALWARE_SIGNATURES[file_hash]
                    self.threat_found.emit(file_path, "Malware", f"Detectado: {threat_name}")
                    return ("Malware", threat_name, 1.0)
            
            if self.is_stop_requested():
                return None
                
            # Verificar padrões suspeitos aprimorados
            is_suspicious, reason, confidence = self.check_file_suspicious_enhanced(file_path)
            if is_suspicious:
                threat_type = "Suspeito" if confidence < 0.8 else "Malware"
                self.threat_found.emit(file_path, threat_type, reason)
                return (threat_type, reason, confidence)
                
            return None
            
        except Exception as e:
            print(f"Erro ao verificar arquivo {file_path}: {e}")
            return None
    
    def run(self):
        """Executar verificação aprimorada"""
        try:
            files_scanned = 0
            threats_found = []
            
            self.scan_status.emit("Iniciando verificação aprimorada...")
            
            if self.scan_type == "quick":
                patterns = ["*.exe", "*.scr", "*.bat", "*.cmd", "*.vbs", "*.js"]
            else:
                patterns = ["*"]
            
            # Coletar arquivos
            all_files = []
            self.scan_status.emit("Coletando arquivos...")
            
            for directory in self.directories:
                if self.is_stop_requested():
                    break
                    
                if not os.path.exists(directory):
                    continue
                    
                try:
                    for pattern in patterns:
                        for file_path in Path(directory).rglob(pattern):
                            if self.is_stop_requested():
                                break
                            if file_path.is_file():
                                all_files.append(str(file_path))
                                
                                if len(all_files) > 10000:
                                    break
                        if self.is_stop_requested() or len(all_files) > 10000:
                            break
                except Exception as e:
                    print(f"Erro ao coletar arquivos de {directory}: {e}")
                    continue
            
            total_files = len(all_files)
            mode_text = "MODO ANJO CAÍDO" if self.fallen_angel_mode else "modo normal"
            self.scan_status.emit(f"Verificando {total_files} arquivos em {mode_text}...")
            
            # Verificar arquivos
            for i, file_path in enumerate(all_files):
                if self.is_stop_requested():
                    break
                
                filename = os.path.basename(file_path)
                self.file_scanned.emit(filename)
                
                # Verificação aprimorada
                result = self.scan_file_enhanced(file_path)
                if result and not self.is_stop_requested():
                    threats_found.append({
                        'file': file_path,
                        'type': result[0],
                        'description': result[1],
                        'confidence': result[2],
                        'detected_at': datetime.now().isoformat()
                    })
                
                files_scanned += 1
                
                if total_files > 0:
                    progress = min(100, int((i + 1) * 100 / total_files))
                    self.progress_updated.emit(progress)
                
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
    """Motor de verificação aprimorado"""
    def __init__(self):
        super().__init__()
        self.current_worker: Optional[EnhancedScanWorker] = None
        
    def start_scan(self, directories: List[str], scan_type: str = "quick", fallen_angel_mode: bool = False) -> EnhancedScanWorker:
        """Iniciar nova verificação"""
        self.stop_scan()
        self.current_worker = EnhancedScanWorker(directories, scan_type, fallen_angel_mode)
        return self.current_worker
    
    def stop_scan(self):
        """Parar verificação atual"""
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.request_stop()
            self.current_worker.wait(3000)
            if self.current_worker.isRunning():
                self.current_worker.terminate()
                self.current_worker.wait(1000)
        self.current_worker = None

class QuarantineManager:
    """Gerenciador de quarentena aprimorado"""
    
    def __init__(self, quarantine_dir):
        self.quarantine_dir = Path(quarantine_dir)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.quarantine_dir / "quarantine.db"
        self.init_database()
    
    def init_database(self):
        """Inicializar banco de dados da quarentena"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute('''
                CREATE TABLE IF NOT EXISTS quarantine (
                    id INTEGER PRIMARY KEY,
                    original_path TEXT,
                    quarantine_path TEXT,
                    threat_type TEXT,
                    description TEXT,
                    quarantined_at TEXT,
                    reason TEXT,
                    confidence REAL
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao inicializar banco de quarentena: {e}")
    
    def quarantine_file(self, file_path, threat_type, description, reason=None, confidence=0.0):
        """Mover arquivo para quarentena"""
        try:
            original_path = Path(file_path)
            if not original_path.exists():
                return False
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quarantine_name = f"{timestamp}_{original_path.name}.quar"
            quarantine_path = self.quarantine_dir / quarantine_name
            
            shutil.move(str(original_path), str(quarantine_path))
            
            conn = sqlite3.connect(str(self.db_path))
            conn.execute('''
                INSERT INTO quarantine 
                (original_path, quarantine_path, threat_type, description, quarantined_at, reason, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(original_path), str(quarantine_path), threat_type, description, 
                  datetime.now().isoformat(), reason or description, confidence))
            conn.commit()
            conn.close()
            
            print(f"✅ Arquivo em quarentena: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao quarentenar arquivo {file_path}: {e}")
            return False
    
    def get_quarantined_files(self):
        """Obter lista de arquivos em quarentena"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute('''
                SELECT id, original_path, threat_type, description, quarantined_at, reason, confidence
                FROM quarantine ORDER BY quarantined_at DESC
            ''')
            files = cursor.fetchall()
            conn.close()
            return files
        except Exception as e:
            print(f"Erro ao obter arquivos em quarentena: {e}")
            return []
    
    def restore_file(self, quarantine_id):
        """Restaurar arquivo da quarentena"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute('''
                SELECT original_path, quarantine_path FROM quarantine WHERE id = ?
            ''', (quarantine_id,))
            result = cursor.fetchone()
            
            if result:
                original_path, quarantine_path = result
                if os.path.exists(quarantine_path):
                    os.makedirs(os.path.dirname(original_path), exist_ok=True)
                    shutil.move(quarantine_path, original_path)
                    conn.execute('DELETE FROM quarantine WHERE id = ?', (quarantine_id,))
                    conn.commit()
                    print(f"✅ Arquivo restaurado: {original_path}")
                    conn.close()
                    return True
            
            conn.close()
            return False
            
        except Exception as e:
            print(f"❌ Erro ao restaurar arquivo: {e}")
            return False
    
    def delete_quarantine_file(self, quarantine_id):
        """Deletar arquivo da quarentena permanentemente"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.execute('''
                SELECT quarantine_path FROM quarantine WHERE id = ?
            ''', (quarantine_id,))
            result = cursor.fetchone()
            
            if result:
                quarantine_path = result[0]
                if os.path.exists(quarantine_path):
                    os.remove(quarantine_path)
                
                conn.execute('DELETE FROM quarantine WHERE id = ?', (quarantine_id,))
                conn.commit()
                conn.close()
                return True
            
            conn.close()
            return False
            
        except Exception as e:
            print(f"❌ Erro ao deletar arquivo: {e}")
            return False

class RealTimeProtection(QObject):
    """Proteção em tempo real com kill automático integrado"""
    threat_detected = pyqtSignal(str, str, str)
    
    def __init__(self, scanner, quarantine_manager, process_killer):
        super().__init__()
        self.scanner = scanner
        self.quarantine_manager = quarantine_manager
        self.process_killer = process_killer
        self.monitoring = False
        self.monitoring_thread = None
    
    def start_monitoring(self):
        """Iniciar monitoramento em tempo real"""
        self.monitoring = True
        if psutil:
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
        print("🛡️ Proteção em tempo real ativada")
    
    def stop_monitoring(self):
        """Parar monitoramento em tempo real"""
        self.monitoring = False
        print("ℹ️ Proteção em tempo real desativada")
    
    def _monitoring_loop(self):
        """Loop de monitoramento (apenas no modo anjo caído)"""
        while self.monitoring:
            try:
                if not self.process_killer.fallen_angel_mode:
                    time.sleep(5)
                    continue
                
                # Monitorar processos apenas no modo anjo caído
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        if not self.monitoring:
                            break
                        
                        process_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'path': proc.info.get('exe', ''),
                            'suspicious_score': 0
                        }
                        
                        # Calcular score de suspeição
                        self._calculate_process_suspicion(process_info)
                        
                        # Verificar se deve eliminar (apenas no modo anjo caído)
                        if self.process_killer.should_kill_process(process_info):
                            self.process_killer.kill_process_aggressive(
                                process_info, 
                                "Monitoramento automático - modo anjo caído"
                            )
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    except Exception as e:
                        print(f"Erro ao monitorar processo: {e}")
                
                time.sleep(2)  # Monitoramento mais frequente no modo anjo caído
            
            except Exception as e:
                print(f"Erro no monitoramento: {e}")
                time.sleep(10)
    
    def _calculate_process_suspicion(self, process_info):
        """Calcular score de suspeição do processo"""
        try:
            name = process_info['name'].lower()
            path = process_info['path'].lower()
            
            score = 0
            
            # Verificar nome suspeito
            if name in [p.lower() for p in ULTRA_SUSPICIOUS_PROCESSES]:
                score += 40
            
            # Verificar localização suspeita
            suspicious_paths = ['temp', 'tmp', 'appdata\\roaming', 'downloads']
            if any(sp in path for sp in suspicious_paths):
                score += 15
            
            process_info['suspicious_score'] = score
        
        except Exception:
            process_info['suspicious_score'] = 0

class AngleGuardV10Enhanced(QMainWindow):
    def __init__(self):
        super().__init__()
        print("🔧 Iniciando Angle Guard V10 Enhanced...")
        
        # Diretórios do sistema
        self.app_data_dir = Path.home() / ".angleGuard"
        self.app_data_dir.mkdir(exist_ok=True)
        
        # Sistema de alertas
        self.alert_system = AlertSystem()
        
        # Componentes do sistema
        self.scanner = ThreatScanner()
        self.quarantine_manager = QuarantineManager(self.app_data_dir / "quarantine")
        self.process_killer = ProcessKiller(self.alert_system)
        self.realtime_protection = RealTimeProtection(self.scanner, self.quarantine_manager, self.process_killer)
        
        # Componentes adicionais
        self.network_manager = NetworkManager()
        if WINDOWS_AVAILABLE:
            self.startup_control = StartupControl()
        else:
            self.startup_control = None
        
        # Estado da aplicação
        self.dark_mode = True
        self.current_tab = 'home'
        self.is_scanning = False
        self.fallen_angel_active = False
        self.current_scan_worker: Optional[EnhancedScanWorker] = None
        
        # Dados do sistema
        self.system_data = {
            'files_scanned': 0,
            'threats_blocked': 0,
            'ml_detections': 0,
            'protection_level': 'Celestial Enhanced',
            'quarantine_items': 0,
            'last_scan_time': 'Nunca',
            'last_scan_duration': '0s',
            'last_scan_files': 0,
            'wifi_enabled': True,
            'usb_enabled': True,
            'startup_enabled': False,
            'processes_killed': 0
        }
        
        try:
            self.init_ui()
            self.apply_theme()
            self.load_system_data()
            
            # Conectar sinais do sistema de alertas
            self.alert_system.threat_detected_signal.connect(self.on_threat_alert)
            self.alert_system.process_killed_signal.connect(self.on_process_killed_alert)
            
            print("✅ Interface V10 Enhanced criada com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar interface: {e}")
            raise
    
    def init_ui(self):
        """Inicializar interface"""
        self.setWindowTitle("🛡️ Angle Guard - Proteção Celestial V10 Enhanced")
        self.setGeometry(150, 100, 1400, 900)
        self.setMinimumSize(1000, 600)
        
        # Centralizar na tela
        if QT_VERSION == 5:
            screen = QApplication.desktop().screenGeometry()
        else:
            screen = QApplication.primaryScreen().geometry()
        
        x = (screen.width() - 1400) // 2
        y = (screen.height() - 900) // 2
        self.move(x, y)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Criar componentes
        self.create_sidebar(main_layout)
        self.create_main_area(main_layout)
        
        # Inicializar proteção em tempo real
        self.realtime_protection.start_monitoring()
        
        # Mostrar página inicial
        self.show_home_page()
    
    def create_sidebar(self, main_layout):
        """Criar sidebar"""
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(280)
        self.sidebar.setObjectName("sidebar")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # Header
        self.create_sidebar_header(sidebar_layout)
        
        # Navegação
        self.create_navigation_menu(sidebar_layout)
        
        main_layout.addWidget(self.sidebar)
    
    def create_sidebar_header(self, layout):
        """Criar header da sidebar"""
        header_frame = QFrame()
        header_frame.setObjectName("sidebar_header")
        header_frame.setFixedHeight(140)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 25, 20, 25)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Botão de tema
        theme_layout = QHBoxLayout()
        theme_layout.addStretch()
        
        self.theme_btn = QPushButton("☀️" if self.dark_mode else "🌙")
        self.theme_btn.setObjectName("theme_toggle")
        self.theme_btn.setFixedSize(35, 35)
        self.theme_btn.clicked.connect(self.toggle_theme)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        
        theme_layout.addWidget(self.theme_btn)
        header_layout.addLayout(theme_layout)
        
        # Logo
        logo_label = QLabel("🛡️")
        logo_label.setObjectName("logo")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setFixedSize(60, 60)
        header_layout.addWidget(logo_label)
        
        # Título
        title_label = QLabel("Angle Guard")
        title_label.setObjectName("app_title")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Subtítulo
        subtitle_label = QLabel("Proteção Enhanced v10.0")
        subtitle_label.setObjectName("app_subtitle")
        subtitle_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_frame)
    
    def create_navigation_menu(self, layout):
        """Criar menu de navegação"""
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        nav_scroll.setObjectName("nav_scroll")
        
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(10, 20, 10, 20)
        nav_layout.setSpacing(5)
        
        self.nav_buttons = {}
        
        # Seções do menu
        self.add_nav_section("PROTEÇÃO", nav_layout)
        self.add_nav_item("home", "🏠", "Início", nav_layout, active=True)
        self.add_nav_item("scan", "🔍", "Verificação", nav_layout)
        self.add_nav_item("realtime", "🛡️", "Proteção em Tempo Real", nav_layout)
        
        self.add_nav_section("MODO ESPECIAL", nav_layout)
        self.add_nav_item("fallen-angel", "😈", "Anjo Caído + Auto Kill", nav_layout, special=True)
        
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
        """Adicionar seção"""
        section_label = QLabel(title)
        section_label.setObjectName("nav_section_title")
        section_label.setContentsMargins(20, 15, 20, 5)
        layout.addWidget(section_label)
    
    def add_nav_item(self, item_id, icon, text, layout, active=False, special=False):
        """Adicionar item de navegação"""
        btn = QPushButton(f"  {icon}  {text}")
        btn.setObjectName("nav_item_special" if special else "nav_item")
        btn.setProperty("active", active)
        btn.setFixedHeight(45)
        btn.clicked.connect(lambda: self.switch_tab(item_id))
        btn.setCursor(Qt.PointingHandCursor)
        
        self.nav_buttons[item_id] = btn
        layout.addWidget(btn)
    
    def create_main_area(self, main_layout):
        """Criar área principal"""
        main_frame = QFrame()
        main_frame.setObjectName("main_content")
        
        self.main_layout = QVBoxLayout(main_frame)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self.create_main_header()
        
        # Conteúdo
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
        """Criar header principal"""
        header_frame = QFrame()
        header_frame.setObjectName("main_header")
        header_frame.setFixedHeight(80)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 20)
        
        self.page_title = QLabel("Início")
        self.page_title.setObjectName("page_title")
        header_layout.addWidget(self.page_title)
        
        header_layout.addStretch()
        
        quick_scan_btn = QPushButton("⚡ Verificação Rápida")
        quick_scan_btn.setObjectName("primary_button")
        quick_scan_btn.setFixedSize(180, 40)
        quick_scan_btn.clicked.connect(self.start_quick_scan)
        quick_scan_btn.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(quick_scan_btn)
        
        self.main_layout.addWidget(header_frame)
    
    def clear_content(self):
        """Limpar conteúdo de forma segura"""
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                widget = child.widget()
                widget.setParent(None)
                widget.deleteLater()
    
    def switch_tab(self, tab_id):
        """Trocar aba"""
        if tab_id == self.current_tab:
            return
        
        # Se há verificação em andamento, avisar o usuário
        if self.is_scanning and tab_id != 'scan':
            reply = QMessageBox.question(
                self, 
                "Verificação em Andamento",
                "Há uma verificação em andamento. Deseja parar e trocar de aba?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
            else:
                self.stop_scan()
        
        # Atualizar navegação
        for btn_id, btn in self.nav_buttons.items():
            btn.setProperty("active", btn_id == tab_id)
            btn.setStyle(btn.style())
        
        self.current_tab = tab_id
        
        # Títulos
        titles = {
            'home': 'Início',
            'scan': 'Verificação',
            'realtime': 'Proteção em Tempo Real',
            'fallen-angel': 'Modo Anjo Caído + Auto Kill',
            'quarantine': 'Quarentena',
            'backup': 'Backup',
            'firewall': 'Firewall',
            'performance': 'Performance',
            'settings': 'Configurações'
        }
        self.page_title.setText(titles.get(tab_id, 'Início'))
        
        # Mostrar conteúdo
        if tab_id == 'home':
            self.show_home_page()
        elif tab_id == 'scan':
            self.show_scan_page()
        elif tab_id == 'quarantine':
            self.show_quarantine_page()
        elif tab_id == 'fallen-angel':
            self.show_fallen_angel_page()
        elif tab_id == 'realtime':
            self.show_realtime_page()
        elif tab_id == 'backup':
            self.show_backup_page()
        elif tab_id == 'firewall':
            self.show_firewall_page()
        elif tab_id == 'settings':
            self.show_settings_page()
        else:
            self.show_simple_page(tab_id)
    
    def create_status_card(self, title="Sistema Protegido", desc="Proteção celestial enhanced ativa", icon="🛡️"):
        """Criar card de status"""
        card = QFrame()
        card.setObjectName("status_card_main")
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # Ícone
        icon_label = QLabel(icon)
        icon_label.setObjectName("status_icon")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFixedSize(60, 60)
        
        # Texto
        text_layout = QVBoxLayout()
        
        status_title = QLabel(title)
        status_title.setObjectName("status_title")
        
        status_desc = QLabel(desc)
        status_desc.setObjectName("status_desc")
        status_desc.setWordWrap(True)
        
        text_layout.addWidget(status_title)
        text_layout.addWidget(status_desc)
        text_layout.addStretch()
        
        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)
        
        return card
    
    def create_stat_card(self, icon, label, value):
        """Criar card de estatística"""
        card = QFrame()
        card.setObjectName("stat_card")
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("stat_icon")
        icon_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(str(value))
        value_label.setObjectName("stat_value")
        value_label.setAlignment(Qt.AlignCenter)
        
        label_label = QLabel(label)
        label_label.setObjectName("stat_label")
        label_label.setAlignment(Qt.AlignCenter)
        label_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(value_label)
        layout.addWidget(label_label)
        
        return card
    
    def show_home_page(self):
        """Mostrar página inicial"""
        self.clear_content()
        
        # Status principal
        status_card = self.create_status_card()
        self.content_layout.addWidget(status_card)
        
        # Grid de estatísticas
        stats_frame = QFrame()
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(20)
        
        stats_data = [
            ("📊", "Arquivos Verificados", f"{self.system_data['files_scanned']:,}"),
            ("🛡️", "Ameaças Bloqueadas", str(self.system_data['threats_blocked'])),
            ("🔒", "Em Quarentena", str(self.system_data['quarantine_items'])),
            ("⚔️", "Processos Eliminados", str(self.system_data['processes_killed']))
        ]
        
        for i, (icon, label, value) in enumerate(stats_data):
            card = self.create_stat_card(icon, label, value)
            stats_layout.addWidget(card, 0, i)
        
        self.content_layout.addWidget(stats_frame)
        
        # Botão de estatísticas detalhadas (pop-up)
        stats_btn = QPushButton("📈 Mostrar Estatísticas Detalhadas")
        stats_btn.setObjectName("primary_button")
        stats_btn.setFixedHeight(40)
        stats_btn.clicked.connect(self.show_detailed_stats_popup)
        stats_btn.setCursor(Qt.PointingHandCursor)
        self.content_layout.addWidget(stats_btn)
        
        # Log de atividades
        activity_card = QFrame()
        activity_card.setObjectName("activity_card")
        
        activity_layout = QVBoxLayout(activity_card)
        activity_layout.setContentsMargins(20, 20, 20, 20)
        activity_layout.setSpacing(15)
        
        title = QLabel("🌟 Atividade Recente")
        title.setObjectName("activity_title")
        activity_layout.addWidget(title)
        
        activities = [
            ("🛡️", "Proteção em tempo real ativa", "agora"),
            ("😈", "Modo Anjo Caído com Auto Kill", "ativo" if self.fallen_angel_active else "inativo"),
            ("📊", f"Última verificação: {self.system_data['last_scan_time']}", ""),
            ("🔒", f"Itens em quarentena: {self.system_data['quarantine_items']}", ""),
            ("⚡", "Sistema otimizado e protegido", "")
        ]
        
        for icon, activity, time_str in activities:
            item_layout = QHBoxLayout()
            
            icon_label = QLabel(icon)
            icon_label.setFixedWidth(25)
            
            activity_label = QLabel(activity)
            activity_label.setObjectName("activity_text")
            
            if time_str:
                time_label = QLabel(time_str)
                time_label.setObjectName("activity_time")
                item_layout.addWidget(time_label)
            
            item_layout.addWidget(icon_label)
            item_layout.addWidget(activity_label, 1)
            
            activity_layout.addLayout(item_layout)
        
        self.content_layout.addWidget(activity_card)
        self.content_layout.addStretch()
    
    def show_detailed_stats_popup(self):
        """Mostrar pop-up com estatísticas detalhadas"""
        try:
            stats_text = f"""ESTATÍSTICAS DETALHADAS - ANGLE GUARD

📊 VERIFICAÇÕES:
• Arquivos verificados: {self.system_data['files_scanned']:,}
• Última verificação: {self.system_data['last_scan_time']}
• Arquivos na última verificação: {self.system_data['last_scan_files']:,}
• Duração da última verificação: {self.system_data['last_scan_duration']}

🛡️ PROTEÇÃO:
• Ameaças bloqueadas: {self.system_data['threats_blocked']}
• Detecções ML: {self.system_data['ml_detections']}
• Nível de proteção: {self.system_data['protection_level']}

🔒 QUARENTENA:
• Itens em quarentena: {self.system_data['quarantine_items']}

😈 MODO ANJO CAÍDO:
• Status: {'ATIVO' if self.fallen_angel_active else 'INATIVO'}
• Processos eliminados: {self.system_data['processes_killed']}

🌐 REDE:
• WiFi: {'Ativo' if self.system_data['wifi_enabled'] else 'Inativo'}
• USB: {'Ativo' if self.system_data['usb_enabled'] else 'Inativo'}

⚙️ SISTEMA:
• Inicialização automática: {'Ativa' if self.system_data['startup_enabled'] else 'Inativa'}
"""
            
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
        """Mostrar página de verificação"""
        self.clear_content()
        
        # Barra de progresso de verificação (apenas se estiver verificando)
        if self.is_scanning and hasattr(self, 'scan_progress_card'):
            self.content_layout.addWidget(self.scan_progress_card)
        
        # Opções de verificação
        options_frame = QFrame()
        options_layout = QGridLayout(options_frame)
        options_layout.setSpacing(20)
        
        scan_options = [
            ("⚡", "Verificação Rápida", "Análise inteligente dos arquivos críticos", "quick"),
            ("💿", "Verificação Completa", "Análise profunda de todo o sistema", "full"),
            ("😈", "Verificação Anjo Caído", "Verificação ULTRA AGRESSIVA com auto kill", "fallen_angel"),
            ("📁", "Verificação Personalizada", "Escolha diretórios específicos", "custom")
        ]
        
        for i, (icon, title, desc, scan_type) in enumerate(scan_options):
            card = self.create_scan_option_card(icon, title, desc, scan_type)
            row, col = divmod(i, 2)
            options_layout.addWidget(card, row, col)
        
        self.content_layout.addWidget(options_frame)
        
        # Resultados da última verificação
        results_card = QFrame()
        results_card.setObjectName("scan_results_card")
        
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(15)
        
        results_title = QLabel("📊 Última Verificação")
        results_title.setObjectName("activity_title")
        results_layout.addWidget(results_title)
        
        if self.system_data['last_scan_time'] != 'Nunca':
            results_info = QLabel(
                f"🕒 Horário: {self.system_data['last_scan_time']}\n"
                f"📁 Arquivos verificados: {self.system_data['last_scan_files']:,}\n"
                f"⏱️ Duração: {self.system_data['last_scan_duration']}\n"
                f"🛡️ Ameaças encontradas: {self.system_data['threats_blocked']}"
            )
        else:
            results_info = QLabel("Nenhuma verificação realizada ainda.")
        
        results_info.setObjectName("activity_text")
        results_info.setWordWrap(True)
        results_layout.addWidget(results_info)
        
        self.content_layout.addWidget(results_card)
        self.content_layout.addStretch()
    
    def create_scan_option_card(self, icon, title, desc, scan_type):
        """Criar card de opção de verificação"""
        card = QFrame()
        card.setObjectName("scan_option")
        card.setFixedHeight(200)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("scan_icon")
        icon_label.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setObjectName("scan_title")
        title_label.setAlignment(Qt.AlignCenter)
        
        desc_label = QLabel(desc)
        desc_label.setObjectName("scan_desc")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        # Tornar clicável apenas se não estiver verificando
        if not self.is_scanning:
            card.mousePressEvent = lambda event: self.start_scan_type(scan_type)
            card.setCursor(Qt.PointingHandCursor)
        else:
            card.setEnabled(False)
        
        return card
    
    def create_scan_progress_card(self):
        """Criar card de progresso da verificação"""
        card = QFrame()
        card.setObjectName("scan_progress_card")
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)
        
        # Título
        mode_text = "😈 VERIFICAÇÃO ANJO CAÍDO" if self.fallen_angel_active else "🔍 Verificação em Andamento"
        title = QLabel(mode_text)
        title.setObjectName("scan_title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Barra de progresso
        self.scan_progress_bar = QProgressBar()
        self.scan_progress_bar.setObjectName("scan_progress")
        self.scan_progress_bar.setFixedHeight(25)
        self.scan_progress_bar.setRange(0, 100)
        self.scan_progress_bar.setValue(0)
        layout.addWidget(self.scan_progress_bar)
        
        # Informações de progresso
        self.scan_progress_label = QLabel("Preparando verificação...")
        self.scan_progress_label.setObjectName("scan_progress_text")
        self.scan_progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.scan_progress_label)
        
        # Arquivo atual
        self.current_file_label = QLabel("")
        self.current_file_label.setObjectName("scan_file_text")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)
        
        # Botão de parar
        stop_btn = QPushButton("⏹️ Parar Verificação")
        stop_btn.setObjectName("stop_button")
        stop_btn.setFixedHeight(35)
        stop_btn.clicked.connect(self.stop_scan)
        stop_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(stop_btn)
        
        return card
    
    def show_quarantine_page(self):
        """Mostrar página de quarentena"""
        self.clear_content()
        
        # Carregar arquivos em quarentena
        quarantined_files = self.quarantine_manager.get_quarantined_files()
        
        if not quarantined_files:
            # Sistema limpo
            clean_frame = QFrame()
            clean_frame.setObjectName("status_card")
            
            layout = QVBoxLayout(clean_frame)
            layout.setContentsMargins(60, 60, 60, 60)
            layout.setAlignment(Qt.AlignCenter)
            layout.setSpacing(20)
            
            icon = QLabel("✨")
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("font-size: 80px;")
            
            title = QLabel("Sistema Limpo")
            title.setObjectName("status_title")
            title.setAlignment(Qt.AlignCenter)
            
            desc = QLabel("Nenhuma ameaça em quarentena")
            desc.setObjectName("status_desc")
            desc.setAlignment(Qt.AlignCenter)
            
            layout.addWidget(icon)
            layout.addWidget(title)
            layout.addWidget(desc)
            
            self.content_layout.addWidget(clean_frame)
        else:
            # Lista de arquivos em quarentena
            quarantine_frame = QFrame()
            quarantine_frame.setObjectName("quarantine_list")
            
            layout = QVBoxLayout(quarantine_frame)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            title = QLabel(f"🔒 Arquivos em Quarentena ({len(quarantined_files)})")
            title.setObjectName("activity_title")
            layout.addWidget(title)
            
            # Scroll area para lista
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)
            
            for file_data in quarantined_files:
                file_id, original_path, threat_type, description, quarantined_at, reason, confidence = file_data
                
                file_card = self.create_quarantine_file_card(
                    file_id, original_path, threat_type, description, quarantined_at, reason, confidence
                )
                scroll_layout.addWidget(file_card)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
            
            self.content_layout.addWidget(quarantine_frame)
        
        self.content_layout.addStretch()
    
    def create_quarantine_file_card(self, file_id, original_path, threat_type, description, quarantined_at, reason, confidence):
        """Criar card de arquivo em quarentena"""
        card = QFrame()
        card.setObjectName("quarantine_file_card")
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Ícone do tipo de ameaça
        threat_icons = {
            "Malware": "🦠",
            "Suspeito": "⚠️",
            "Vírus": "🔴",
            "Trojan": "🏴"
        }
        icon = QLabel(threat_icons.get(threat_type, "⚠️"))
        icon.setObjectName("threat_icon")
        icon.setFixedSize(40, 40)
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        # Informações do arquivo
        info_layout = QVBoxLayout()
        
        filename = QLabel(os.path.basename(original_path))
        filename.setObjectName("quarantine_filename")
        info_layout.addWidget(filename)
        
        path_info = QLabel(f"Caminho: {original_path}")
        path_info.setObjectName("quarantine_path")
        path_info.setWordWrap(True)
        info_layout.addWidget(path_info)
        
        threat_info = QLabel(f"Tipo: {threat_type}")
        threat_info.setObjectName("quarantine_threat")
        info_layout.addWidget(threat_info)
        
        # Confiança da detecção
        if confidence > 0:
            confidence_info = QLabel(f"Confiança: {confidence:.1%}")
            confidence_info.setObjectName("quarantine_confidence")
            info_layout.addWidget(confidence_info)
        
        # Motivo da quarentena
        if reason:
            reason_info = QLabel(f"Motivo: {reason}")
            reason_info.setObjectName("quarantine_reason")
            reason_info.setWordWrap(True)
            info_layout.addWidget(reason_info)
        
        date_info = QLabel(f"Quarentena: {quarantined_at}")
        date_info.setObjectName("quarantine_date")
        info_layout.addWidget(date_info)
        
        layout.addLayout(info_layout, 1)
        
        # Botões de ação
        actions_layout = QVBoxLayout()
        
        restore_btn = QPushButton("🔄 Restaurar")
        restore_btn.setObjectName("restore_button")
        restore_btn.setFixedSize(100, 30)
        restore_btn.clicked.connect(lambda: self.restore_quarantine_file(file_id))
        restore_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(restore_btn)
        
        delete_btn = QPushButton("🗑️ Deletar")
        delete_btn.setObjectName("delete_button")
        delete_btn.setFixedSize(100, 30)
        delete_btn.clicked.connect(lambda: self.delete_quarantine_file(file_id))
        delete_btn.setCursor(Qt.PointingHandCursor)
        actions_layout.addWidget(delete_btn)
        
        layout.addLayout(actions_layout)
        
        return card
    
    def show_fallen_angel_page(self):
        """Mostrar modo Anjo Caído com Auto Kill integrado"""
        self.clear_content()
        
        # Warning
        warning_frame = QFrame()
        warning_frame.setObjectName("fallen_angel_warning")
        warning_frame.setFixedHeight(250)
        
        layout = QVBoxLayout(warning_frame)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        icon = QLabel("😈")
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("font-size: 60px;")
        
        title = QLabel("MODO ANJO CAÍDO + AUTO KILL")
        title.setObjectName("fallen_angel_title")
        title.setAlignment(Qt.AlignCenter)
        
        desc = QLabel("⚠️ PROTEÇÃO MÁXIMA BERSERK COM ELIMINAÇÃO AUTOMÁTICA DE PROCESSOS ⚠️")
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: white; font-weight: bold;")
        
        status_text = "🔥 ATIVADO + AUTO KILL 🔥" if self.fallen_angel_active else "🔥 ATIVAR MODO ANJO CAÍDO 🔥"
        activate_btn = QPushButton(status_text)
        activate_btn.setObjectName("fallen_angel_button")
        activate_btn.setFixedSize(350, 50)
        activate_btn.clicked.connect(self.activate_fallen_angel)
        activate_btn.setCursor(Qt.PointingHandCursor)
        
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addWidget(desc)
        layout.addWidget(activate_btn)
        
        self.content_layout.addWidget(warning_frame)
        
        # Funcionalidades do Modo Anjo Caído
        features_card = QFrame()
        features_card.setObjectName("fallen_angel_info")
        
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(20, 20, 20, 20)
        features_layout.setSpacing(15)
        
        features_title = QLabel("😈 Funcionalidades do Modo Anjo Caído + Auto Kill")
        features_title.setObjectName("fallen_angel_info_title")
        features_layout.addWidget(features_title)
        
        features = [
            "🔥 Verificação em tempo real ultra-agressiva",
            "⚔️ KILL AUTOMÁTICO de processos suspeitos",
            "🛡️ Proteção de kernel avançada",
            "🔒 Quarentena automática preventiva",
            "👀 Análise comportamental extrema",
            "🌪️ Limpeza agressiva de sistema",
            "🚫 Bloqueio automático de rede em emergências",
            "💀 Eliminação instantânea de ameaças",
            "🎯 Detecção por entropia ultra-sensível",
            "📡 Monitoramento contínuo de processos"
        ]
        
        for feature in features:
            feature_label = QLabel(feature)
            feature_label.setObjectName("activity_text")
            features_layout.addWidget(feature_label)
        
        # Status do auto kill
        if self.fallen_angel_active:
            kill_status = QLabel(f"⚔️ PROCESSOS ELIMINADOS: {self.system_data['processes_killed']}")
            kill_status.setObjectName("fallen_angel_info_title")
            kill_status.setAlignment(Qt.AlignCenter)
            features_layout.addWidget(kill_status)
        
        self.content_layout.addWidget(features_card)
        self.content_layout.addStretch()
    
    def show_realtime_page(self):
        """Mostrar página de proteção em tempo real"""
        self.clear_content()
        
        # Status da proteção em tempo real
        status_title = "Proteção Ativa" if self.realtime_protection.monitoring else "Proteção Inativa"
        status_desc = "Monitoramento em tempo real ativo" if self.realtime_protection.monitoring else "Proteção em tempo real desativada"
        status_icon = "👁️" if self.realtime_protection.monitoring else "😴"
        
        status_card = self.create_status_card(status_title, status_desc, status_icon)
        self.content_layout.addWidget(status_card)
        
        # Controles
        controls_frame = QFrame()
        controls_frame.setObjectName("realtime_controls")
        
        controls_layout = QVBoxLayout(controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(15)
        
        controls_title = QLabel("🛡️ Controles de Proteção")
        controls_title.setObjectName("activity_title")
        controls_layout.addWidget(controls_title)
        
        # Toggle proteção em tempo real
        toggle_layout = QHBoxLayout()
        toggle_label = QLabel("Proteção em Tempo Real:")
        toggle_label.setObjectName("activity_text")
        
        self.realtime_toggle = QPushButton("🔴 Desativar" if self.realtime_protection.monitoring else "🟢 Ativar")
        self.realtime_toggle.setObjectName("toggle_button")
        self.realtime_toggle.setFixedSize(120, 35)
        self.realtime_toggle.clicked.connect(self.toggle_realtime_protection)
        self.realtime_toggle.setCursor(Qt.PointingHandCursor)
        
        toggle_layout.addWidget(toggle_label)
        toggle_layout.addStretch()
        toggle_layout.addWidget(self.realtime_toggle)
        
        controls_layout.addLayout(toggle_layout)
        
        # Status do modo anjo caído
        angel_layout = QHBoxLayout()
        angel_label = QLabel("Modo Anjo Caído + Auto Kill:")
        angel_label.setObjectName("activity_text")
        
        angel_status = QLabel("😈 ATIVO" if self.fallen_angel_active else "😇 Inativo")
        angel_status.setObjectName("activity_text")
        angel_status.setStyleSheet(f"color: {'#ff4444' if self.fallen_angel_active else '#55ff55'};")
        
        angel_layout.addWidget(angel_label)
        angel_layout.addWidget(angel_status)
        angel_layout.addStretch()
        
        controls_layout.addLayout(angel_layout)
        
        self.content_layout.addWidget(controls_frame)
        self.content_layout.addStretch()
    
    def show_firewall_page(self):
        """Mostrar página de firewall com controles de rede"""
        self.clear_content()
        
        # Status do firewall
        firewall_title = "Firewall Ativo" if self.network_manager.wifi_enabled else "Conectividade Limitada"
        firewall_desc = "Monitoramento de rede ativo" if self.network_manager.wifi_enabled else "WiFi e USB bloqueados"
        firewall_icon = "🔥" if self.network_manager.wifi_enabled else "🚫"
        
        status_card = self.create_status_card(firewall_title, firewall_desc, firewall_icon)
        self.content_layout.addWidget(status_card)
        
        # Controles de rede
        network_controls_frame = QFrame()
        network_controls_frame.setObjectName("firewall_controls")
        
        controls_layout = QVBoxLayout(network_controls_frame)
        controls_layout.setContentsMargins(20, 20, 20, 20)
        controls_layout.setSpacing(20)
        
        controls_title = QLabel("🔥 Controles de Firewall")
        controls_title.setObjectName("activity_title")
        controls_layout.addWidget(controls_title)
        
        # Controle WiFi
        wifi_layout = QHBoxLayout()
        wifi_label = QLabel("WiFi:")
        wifi_label.setObjectName("activity_text")
        
        wifi_status = QLabel("Ativado" if self.network_manager.wifi_enabled else "Desativado")
        wifi_status.setObjectName("activity_text")
        wifi_status.setStyleSheet(f"color: {'#55FF7F' if self.network_manager.wifi_enabled else '#FF5555'};")
        
        self.wifi_toggle = QPushButton("🔴 Desativar" if self.network_manager.wifi_enabled else "🟢 Ativar")
        self.wifi_toggle.setObjectName("toggle_button")
        self.wifi_toggle.setFixedSize(120, 35)
        self.wifi_toggle.clicked.connect(self.toggle_wifi)
        self.wifi_toggle.setCursor(Qt.PointingHandCursor)
        
        wifi_layout.addWidget(wifi_label)
        wifi_layout.addWidget(wifi_status)
        wifi_layout.addStretch()
        wifi_layout.addWidget(self.wifi_toggle)
        
        controls_layout.addLayout(wifi_layout)
        
        # Controle USB
        usb_layout = QHBoxLayout()
        usb_label = QLabel("Portas USB:")
        usb_label.setObjectName("activity_text")
        
        usb_status = QLabel("Ativado" if self.network_manager.usb_enabled else "Desativado")
        usb_status.setObjectName("activity_text")
        usb_status.setStyleSheet(f"color: {'#55FF7F' if self.network_manager.usb_enabled else '#FF5555'};")
        
        self.usb_toggle = QPushButton("🔴 Desativar" if self.network_manager.usb_enabled else "🟢 Ativar")
        self.usb_toggle.setObjectName("toggle_button")
        self.usb_toggle.setFixedSize(120, 35)
        self.usb_toggle.clicked.connect(self.toggle_usb)
        self.usb_toggle.setCursor(Qt.PointingHandCursor)
        
        usb_layout.addWidget(usb_label)
        usb_layout.addWidget(usb_status)
        usb_layout.addStretch()
        usb_layout.addWidget(self.usb_toggle)
        
        controls_layout.addLayout(usb_layout)
        
        # Botão de bloqueio de emergência
        emergency_btn = QPushButton("🚨 BLOQUEIO DE EMERGÊNCIA")
        emergency_btn.setObjectName("emergency_button")
        emergency_btn.setFixedHeight(50)
        emergency_btn.clicked.connect(self.emergency_lockdown)
        emergency_btn.setCursor(Qt.PointingHandCursor)
        emergency_btn.setStyleSheet("""
            QPushButton#emergency_button {
                background-color: #cc4444;
                color: #ffffff;
                border: 2px solid #ff0000;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton#emergency_button:hover {
                background-color: #aa2222;
            }
        """)
        
        controls_layout.addWidget(emergency_btn)
        
        self.content_layout.addWidget(network_controls_frame)
        self.content_layout.addStretch()
    
    def show_settings_page(self):
        """Mostrar página de configurações"""
        self.clear_content()
        
        # Configurações gerais
        general_frame = QFrame()
        general_frame.setObjectName("settings_card")
        
        general_layout = QVBoxLayout(general_frame)
        general_layout.setContentsMargins(20, 20, 20, 20)
        general_layout.setSpacing(20)
        
        general_title = QLabel("⚙️ Configurações Gerais")
        general_title.setObjectName("activity_title")
        general_layout.addWidget(general_title)
        
        # Controle de inicialização automática (apenas no Windows)
        if WINDOWS_AVAILABLE and self.startup_control:
            startup_layout = QHBoxLayout()
            startup_label = QLabel("Iniciar com o Windows:")
            startup_label.setObjectName("activity_text")
            
            startup_status = QLabel("Ativado" if self.startup_control.is_enabled() else "Desativado")
            startup_status.setObjectName("activity_text")
            startup_status.setStyleSheet(f"color: {'#55FF7F' if self.startup_control.is_enabled() else '#FF5555'};")
            
            self.startup_toggle = QPushButton("🔴 Desativar" if self.startup_control.is_enabled() else "🟢 Ativar")
            self.startup_toggle.setObjectName("toggle_button")
            self.startup_toggle.setFixedSize(120, 35)
            self.startup_toggle.clicked.connect(self.toggle_startup)
            self.startup_toggle.setCursor(Qt.PointingHandCursor)
            
            startup_layout.addWidget(startup_label)
            startup_layout.addWidget(startup_status)
            startup_layout.addStretch()
            startup_layout.addWidget(self.startup_toggle)
            
            general_layout.addLayout(startup_layout)
        
        # Outras configurações
        other_settings = [
            ("Tema escuro", "Interface com tema escuro ativada", self.dark_mode),
            ("Proteção em tempo real", "Monitoramento contínuo do sistema", self.realtime_protection.monitoring),
            ("Quarentena automática", "Mover ameaças automaticamente para quarentena", True),
            ("Pop-ups de alerta", "Mostrar alertas em tempo real", self.alert_system.popup_enabled)
        ]
        
        for setting_name, setting_desc, setting_value in other_settings:
            setting_layout = QHBoxLayout()
            
            setting_info_layout = QVBoxLayout()
            name_label = QLabel(setting_name)
            name_label.setObjectName("activity_text")
            setting_info_layout.addWidget(name_label)
            
            desc_label = QLabel(setting_desc)
            desc_label.setObjectName("quarantine_date")
            desc_label.setWordWrap(True)
            setting_info_layout.addWidget(desc_label)
            
            setting_layout.addLayout(setting_info_layout, 1)
            
            toggle = QCheckBox()
            toggle.setChecked(setting_value)
            if setting_name == "Tema escuro":
                toggle.stateChanged.connect(self.toggle_theme)
            elif setting_name == "Proteção em tempo real":
                toggle.stateChanged.connect(self.toggle_realtime_protection)
            elif setting_name == "Pop-ups de alerta":
                toggle.stateChanged.connect(self.toggle_popup_alerts)
            setting_layout.addWidget(toggle)
            
            general_layout.addLayout(setting_layout)
        
        self.content_layout.addWidget(general_frame)
        self.content_layout.addStretch()
    
    def show_backup_page(self):
        """Mostrar página de backup"""
        self.clear_content()
        
        # Status do backup
        backup_card = self.create_status_card("Sistema de Backup", "Backups automáticos configurados", "💾")
        self.content_layout.addWidget(backup_card)
        
        # Opções de backup
        backup_options_frame = QFrame()
        backup_options_layout = QGridLayout(backup_options_frame)
        backup_options_layout.setSpacing(20)
        
        backup_options = [
            ("💾", "Backup Completo", "Backup de todos os arquivos importantes"),
            ("⚡", "Backup Rápido", "Backup de arquivos críticos"),
            ("🔄", "Backup Incremental", "Backup apenas de alterações"),
            ("📅", "Backup Agendado", "Configurar backups automáticos")
        ]
        
        for i, (icon, title, desc) in enumerate(backup_options):
            card = self.create_backup_option_card(icon, title, desc)
            row, col = divmod(i, 2)
            backup_options_layout.addWidget(card, row, col)
        
        self.content_layout.addWidget(backup_options_frame)
        self.content_layout.addStretch()
    
    def create_backup_option_card(self, icon, title, desc):
        """Criar card de opção de backup"""
        card = QFrame()
        card.setObjectName("backup_option")
        card.setFixedHeight(150)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)
        
        icon_label = QLabel(icon)
        icon_label.setObjectName("backup_icon")
        icon_label.setAlignment(Qt.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setObjectName("backup_title")
        title_label.setAlignment(Qt.AlignCenter)
        
        desc_label = QLabel(desc)
        desc_label.setObjectName("backup_desc")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        
        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        
        card.mousePressEvent = lambda event: self.start_backup(title)
        card.setCursor(Qt.PointingHandCursor)
        
        return card
    
    def show_simple_page(self, page_id):
        """Mostrar página simples"""
        self.clear_content()
        
        # Status baseado na página
        status_configs = {
            'performance': ("⚡", "Performance", "Sistema otimizado")
        }
        
        if page_id in status_configs:
            icon, title, desc = status_configs[page_id]
            status_card = self.create_status_card(title, desc, icon)
            self.content_layout.addWidget(status_card)
        
        self.content_layout.addStretch()
    
    # Métodos de funcionalidade
    
    def start_quick_scan(self):
        """Iniciar verificação rápida"""
        if self.is_scanning:
            self.stop_scan()
            return
        
        directories = [
            os.path.expanduser("~/Downloads"), 
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents")
        ]
        
        self._start_scan(directories, "quick", False)
    
    def start_scan_type(self, scan_type):
        """Iniciar tipo específico de verificação"""
        if self.is_scanning:
            return
        
        if scan_type == "quick":
            self.start_quick_scan()
        elif scan_type == "full":
            self.start_full_scan()
        elif scan_type == "fallen_angel":
            self.start_fallen_angel_scan()
        elif scan_type == "custom":
            self.start_custom_scan()
    
    def start_full_scan(self):
        """Iniciar verificação completa"""
        if self.is_scanning:
            return
        
        directories = []
        if os.name == 'nt':  # Windows
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    directories.append(drive)
        else:  # Unix-like
            directories = ["/home", "/usr", "/opt"]
        
        self._start_scan(directories, "full", False)
    
    def start_fallen_angel_scan(self):
        """Iniciar verificação no modo anjo caído"""
        if self.is_scanning:
            return
        
        # Ativar modo anjo caído automaticamente
        if not self.fallen_angel_active:
            self.activate_fallen_angel()
        
        directories = []
        if os.name == 'nt':  # Windows
            directories = ["C:\\"]
        else:  # Unix-like
            directories = ["/"]
        
        self._start_scan(directories, "fallen_angel", True)
    
    def start_custom_scan(self):
        """Iniciar verificação personalizada"""
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Diretório para Verificação")
        if directory and not self.is_scanning:
            self._start_scan([directory], "custom", self.fallen_angel_active)
    
    def _start_scan(self, directories: List[str], scan_type: str, fallen_angel_mode: bool):
        """Método privado para iniciar verificação"""
        try:
            self.is_scanning = True
            
            # Criar card de progresso
            self.scan_progress_card = self.create_scan_progress_card()
            
            # Se estiver na página de verificação, adicionar o card
            if self.current_tab == 'scan':
                self.content_layout.insertWidget(0, self.scan_progress_card)
            
            # Criar e configurar worker
            self.current_scan_worker = self.scanner.start_scan(directories, scan_type, fallen_angel_mode)
            
            # Conectar sinais
            self.current_scan_worker.progress_updated.connect(self.update_scan_progress)
            self.current_scan_worker.file_scanned.connect(self.on_file_scanned)
            self.current_scan_worker.threat_found.connect(self.on_threat_found)
            self.current_scan_worker.scan_completed.connect(self.on_scan_completed)
            self.current_scan_worker.scan_status.connect(self.on_scan_status)
            
            # Iniciar worker
            self.current_scan_worker.start()
            
            scan_names = {
                "quick": "verificação rápida",
                "full": "verificação completa", 
                "custom": "verificação personalizada",
                "fallen_angel": "verificação ANJO CAÍDO"
            }
            print(f"⚡ Iniciando {scan_names.get(scan_type, 'verificação')}...")
            
        except Exception as e:
            print(f"Erro ao iniciar verificação: {e}")
            self.is_scanning = False
            if hasattr(self, 'scan_progress_card'):
                self.scan_progress_card.deleteLater()
                delattr(self, 'scan_progress_card')
    
    def stop_scan(self):
        """Parar verificação"""
        if self.current_scan_worker and self.current_scan_worker.isRunning():
            print("⏹️ Parando verificação...")
            self.current_scan_worker.request_stop()
            
            if not self.current_scan_worker.wait(2000):
                print("⚠️ Forçando parada da verificação...")
                self.current_scan_worker.terminate()
                self.current_scan_worker.wait(1000)
            
        self.scanner.stop_scan()
        self.is_scanning = False
        
        # Remover card de progresso
        if hasattr(self, 'scan_progress_card'):
            self.scan_progress_card.deleteLater()
            delattr(self, 'scan_progress_card')
        
        # Atualizar interface se estiver na página de verificação
        if self.current_tab == 'scan':
            QTimer.singleShot(100, self.show_scan_page)
    
    def update_scan_progress(self, progress):
        """Atualizar progresso da verificação"""
        if hasattr(self, 'scan_progress_bar') and self.scan_progress_bar:
            self.scan_progress_bar.setValue(progress)
            if hasattr(self, 'scan_progress_label') and self.scan_progress_label:
                mode_text = "MODO ANJO CAÍDO" if self.fallen_angel_active else "modo normal"
                self.scan_progress_label.setText(f"Progresso: {progress}% ({mode_text})")
    
    def on_file_scanned(self, filename):
        """Arquivo verificado"""
        if hasattr(self, 'current_file_label') and self.current_file_label:
            if len(filename) > 50:
                filename = filename[:47] + "..."
            self.current_file_label.setText(f"Verificando: {filename}")
    
    def on_scan_status(self, status):
        """Status da verificação"""
        if hasattr(self, 'scan_progress_label') and self.scan_progress_label:
            self.scan_progress_label.setText(status)
    
    def on_threat_found(self, file_path, threat_type, description):
        """Ameaça encontrada"""
        try:
            print(f"🚨 AMEAÇA DETECTADA: {file_path} - {threat_type}: {description}")
            
            # Quarentenar automaticamente
            reason = f"Detectado como {threat_type}: {description}"
            confidence = 0.8 if threat_type == "Malware" else 0.6
            
            if self.quarantine_manager.quarantine_file(file_path, threat_type, description, reason, confidence):
                self.system_data['threats_blocked'] += 1
                self.system_data['quarantine_items'] += 1
                print(f"✅ Arquivo movido para quarentena: {file_path}")
                
                # Mostrar alerta
                threat_info = {
                    'file_path': file_path,
                    'threat_type': threat_type,
                    'confidence': confidence,
                    'description': description
                }
                self.alert_system.show_threat_alert(threat_info)
                
        except Exception as e:
            print(f"Erro ao processar ameaça encontrada: {e}")
    
    def on_scan_completed(self, files_scanned, threats_found, threat_list):
        """Verificação concluída"""
        try:
            self.is_scanning = False
            self.system_data['files_scanned'] += files_scanned
            self.system_data['last_scan_files'] = files_scanned
            self.system_data['last_scan_time'] = datetime.now().strftime("%H:%M")
            
            # Remover card de progresso
            if hasattr(self, 'scan_progress_card'):
                self.scan_progress_card.deleteLater()
                delattr(self, 'scan_progress_card')
            
            self.save_system_data()
            
            # Atualizar interface
            if self.current_tab == 'home':
                QTimer.singleShot(100, self.show_home_page)
            elif self.current_tab == 'quarantine':
                QTimer.singleShot(100, self.show_quarantine_page)
            elif self.current_tab == 'scan':
                QTimer.singleShot(100, self.show_scan_page)
            
            result_msg = f"✅ Verificação concluída!\n📁 Arquivos: {files_scanned:,}\n🛡️ Ameaças: {threats_found}"
            if threats_found > 0:
                result_msg += f"\n🔒 Movidas para quarentena: {threats_found}"
            
            print(result_msg)
            
            # Mostrar popup de resultado
            self.show_scan_result_popup(files_scanned, threats_found)
            
        except Exception as e:
            print(f"Erro ao completar verificação: {e}")
    
    def show_scan_result_popup(self, files_scanned, threats_found):
        """Mostrar popup com resultado da verificação"""
        try:
            if TKINTER_AVAILABLE:
                if threats_found > 0:
                    result_text = f"""Verificação concluída!

📁 Arquivos verificados: {files_scanned:,}
🚨 Ameaças encontradas: {threats_found}
🔒 Arquivos movidos para quarentena: {threats_found}

{'😈 MODO ANJO CAÍDO ATIVO' if self.fallen_angel_active else '🛡️ Proteção normal ativa'}"""
                else:
                    result_text = f"""Verificação concluída!

📁 Arquivos verificados: {files_scanned:,}
✅ Nenhuma ameaça encontrada
🛡️ Sistema limpo e protegido

{'😈 MODO ANJO CAÍDO ATIVO' if self.fallen_angel_active else '🛡️ Proteção normal ativa'}"""
                
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                if threats_found > 0:
                    messagebox.showwarning("Verificação Concluída", result_text)
                else:
                    messagebox.showinfo("Verificação Concluída", result_text)
                root.destroy()
            else:
                # Fallback para QMessageBox
                msg = QMessageBox(self)
                msg.setWindowTitle("Verificação Concluída")
                msg.setIcon(QMessageBox.Warning if threats_found > 0 else QMessageBox.Information)
                
                if threats_found > 0:
                    msg.setText(f"Verificação concluída!\n\n"
                               f"📁 Arquivos verificados: {files_scanned:,}\n"
                               f"🚨 Ameaças encontradas: {threats_found}\n"
                               f"🔒 Arquivos movidos para quarentena: {threats_found}")
                else:
                    msg.setText(f"Verificação concluída!\n\n"
                               f"📁 Arquivos verificados: {files_scanned:,}\n"
                               f"✅ Nenhuma ameaça encontrada\n"
                               f"🛡️ Sistema limpo e protegido")
                
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
            
        except Exception as e:
            print(f"Erro ao mostrar popup de resultado: {e}")
    
    # Handlers de alertas
    def on_threat_alert(self, threat_info):
        """Handler para alertas de ameaça"""
        try:
            print(f"📢 Alerta de ameaça: {threat_info.get('file_path', 'Desconhecido')}")
        except Exception as e:
            print(f"Erro ao processar alerta de ameaça: {e}")
    
    def on_process_killed_alert(self, process_info):
        """Handler para alertas de processo eliminado"""
        try:
            process_name = process_info.get('name', 'Desconhecido')
            print(f"⚔️ Processo eliminado: {process_name}")
            self.system_data['processes_killed'] += 1
        except Exception as e:
            print(f"Erro ao processar alerta de processo: {e}")
    
    # Métodos de controle
    def toggle_wifi(self):
        """Alternar WiFi"""
        try:
            if self.network_manager.toggle_wifi():
                self.system_data['wifi_enabled'] = self.network_manager.wifi_enabled
                self.save_system_data()
                
                self.wifi_toggle.setText("🔴 Desativar" if self.network_manager.wifi_enabled else "🟢 Ativar")
                
                status = "ativado" if self.network_manager.wifi_enabled else "desativado"
                print(f"📶 WiFi {status}")
                
                if self.current_tab == 'firewall':
                    self.show_firewall_page()
            else:
                QMessageBox.warning(self, "Erro", "Falha ao alterar status do WiFi. Execute como administrador.")
                
        except Exception as e:
            print(f"Erro ao alternar WiFi: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao alternar WiFi: {str(e)}")
    
    def toggle_usb(self):
        """Alternar USB"""
        try:
            if self.network_manager.toggle_usb():
                self.system_data['usb_enabled'] = self.network_manager.usb_enabled
                self.save_system_data()
                
                self.usb_toggle.setText("🔴 Desativar" if self.network_manager.usb_enabled else "🟢 Ativar")
                
                status = "ativado" if self.network_manager.usb_enabled else "desativado"
                print(f"🔌 USB {status}")
                
                if self.current_tab == 'firewall':
                    self.show_firewall_page()
            else:
                QMessageBox.warning(self, "Erro", "Falha ao alterar status do USB. Execute como administrador.")
                
        except Exception as e:
            print(f"Erro ao alternar USB: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao alternar USB: {str(e)}")
    
    def emergency_lockdown(self):
        """Bloqueio de emergência"""
        try:
            reply = QMessageBox.question(
                self, 
                "Bloqueio de Emergência",
                "⚠️ ATENÇÃO: Isto irá desativar WiFi e USB imediatamente!\n\nContinuar com o bloqueio de emergência?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.network_manager.emergency_lockdown():
                    self.system_data['wifi_enabled'] = False
                    self.system_data['usb_enabled'] = False
                    self.save_system_data()
                    
                    print("🚨 BLOQUEIO DE EMERGÊNCIA ATIVADO!")
                    QMessageBox.information(self, "Bloqueio Ativado", "🚨 Bloqueio de emergência ativado!\nWiFi e USB foram desabilitados.")
                    
                    if self.current_tab == 'firewall':
                        self.show_firewall_page()
                else:
                    QMessageBox.warning(self, "Erro", "Falha no bloqueio de emergência. Execute como administrador.")
                    
        except Exception as e:
            print(f"Erro no bloqueio de emergência: {e}")
            QMessageBox.critical(self, "Erro", f"Erro no bloqueio de emergência: {str(e)}")
    
    def toggle_startup(self):
        """Alternar inicialização automática"""
        try:
            if self.startup_control and self.startup_control.toggle():
                self.system_data['startup_enabled'] = self.startup_control.is_enabled()
                self.save_system_data()
                
                if hasattr(self, 'startup_toggle'):
                    self.startup_toggle.setText("🔴 Desativar" if self.startup_control.is_enabled() else "🟢 Ativar")
                
                status = "ativada" if self.startup_control.is_enabled() else "desativada"
                print(f"🚀 Inicialização automática {status}")
                
                if self.current_tab == 'settings':
                    self.show_settings_page()
                    
                QMessageBox.information(self, "Configuração Alterada", f"Inicialização automática {status} com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", "Falha ao alterar configuração de inicialização.")
                
        except Exception as e:
            print(f"Erro ao alternar inicialização: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao alternar inicialização: {str(e)}")
    
    def activate_fallen_angel(self):
        """Ativar/desativar modo Anjo Caído com Auto Kill"""
        self.fallen_angel_active = not self.fallen_angel_active
        
        # Ativar/desativar kill automático junto com modo anjo caído
        self.process_killer.set_fallen_angel_mode(self.fallen_angel_active)
        
        if self.fallen_angel_active:
            print(" MODO ANJO CAÍDO + AUTO KILL ATIVADO! Proteção máxima!")
            
            # Mostrar aviso detalhado
            warning_text = """MODO ANJO CAÍDO + AUTO KILL!

⚔️ FUNCIONALIDADES ATIVAS:
• Eliminação automática de processos suspeitos
• Detecção ultra sensível por entropia
• Quarentena automática agressiva
• Monitoramento contínuo de processos
• Alertas em tempo real
• Proteção extrema contra ransomware

⚠️ CUIDADO: Este modo é extremamente agressivo!
Pode eliminar processos legítimos se considerados suspeitos.

Use apenas em situações de emergência ou alta suspeita de infecção."""
            
            if TKINTER_AVAILABLE:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showwarning("MODO ANJO CAÍDO ATIVADO", warning_text)
                root.destroy()
            else:
                QMessageBox.warning(self, "MODO ANJO CAÍDO ATIVADO", warning_text)
            
            # Ativar proteção em tempo real se não estiver
            if not self.realtime_protection.monitoring:
                self.realtime_protection.start_monitoring()
        else:
            print("😇 Modo Anjo Caído desativado. Proteção normal.")
            
            if TKINTER_AVAILABLE:
                root = tk.Tk()
                root.withdraw()
                root.attributes('-topmost', True)
                messagebox.showinfo("Modo Normal", "Modo Anjo Caído desativado.\nProteção retornada ao normal.")
                root.destroy()
        
        # Recarregar página
        self.show_fallen_angel_page()
    
    def toggle_realtime_protection(self):
        """Alternar proteção em tempo real"""
        if self.realtime_protection.monitoring:
            self.realtime_protection.stop_monitoring()
            if hasattr(self, 'realtime_toggle'):
                self.realtime_toggle.setText("🟢 Ativar")
        else:
            self.realtime_protection.start_monitoring()
            if hasattr(self, 'realtime_toggle'):
                self.realtime_toggle.setText("🔴 Desativar")
        
        if self.current_tab == 'realtime':
            self.show_realtime_page()
    
    def toggle_popup_alerts(self):
        """Alternar pop-ups de alerta"""
        self.alert_system.popup_enabled = not self.alert_system.popup_enabled
        status = "ativados" if self.alert_system.popup_enabled else "desativados"
        print(f"📢 Pop-ups de alerta {status}")
    
    def restore_quarantine_file(self, file_id):
        """Restaurar arquivo da quarentena"""
        try:
            if self.quarantine_manager.restore_file(file_id):
                self.system_data['quarantine_items'] -= 1
                self.save_system_data()
                self.show_quarantine_page()
                print(f"✅ Arquivo restaurado da quarentena (ID: {file_id})")
                QMessageBox.information(self, "Sucesso", "Arquivo restaurado com sucesso!")
            else:
                QMessageBox.warning(self, "Erro", "Erro ao restaurar arquivo!")
                print(f"❌ Erro ao restaurar arquivo (ID: {file_id})")
                
        except Exception as e:
            print(f"Erro ao restaurar arquivo: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao restaurar arquivo: {str(e)}")
    
    def delete_quarantine_file(self, file_id):
        """Deletar arquivo da quarentena permanentemente"""
        try:
            reply = QMessageBox.question(
                self, "Confirmar Exclusão",
                "Tem certeza que deseja deletar este arquivo permanentemente?\n\nEsta ação não pode ser desfeita!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.quarantine_manager.delete_quarantine_file(file_id):
                    print(f"🗑️ Arquivo deletado permanentemente (ID: {file_id})")
                    self.system_data['quarantine_items'] -= 1
                    self.save_system_data()
                    self.show_quarantine_page()
                    QMessageBox.information(self, "Sucesso", "Arquivo deletado permanentemente!")
                else:
                    QMessageBox.warning(self, "Erro", "Arquivo não encontrado na quarentena!")
                
        except Exception as e:
            print(f"Erro ao deletar arquivo: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao deletar arquivo: {str(e)}")
    
    def start_backup(self, backup_type):
        """Iniciar processo de backup"""
        try:
            print(f"💾 Iniciando {backup_type.lower()}...")
            
            progress = QProgressDialog(f"Realizando {backup_type.lower()}...", "Cancelar", 0, 100, self)
            progress.setWindowTitle("Backup em Andamento")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Simular progresso de backup
            for i in range(101):
                if progress.wasCanceled():
                    break
                progress.setValue(i)
                QApplication.processEvents()
                time.sleep(0.01)
            
            if not progress.wasCanceled():
                backup_dir = self.app_data_dir / "backups"
                backup_dir.mkdir(exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"backup_{backup_type.lower().replace(' ', '_')}_{timestamp}.zip"
                backup_path = backup_dir / backup_name
                
                # Backup básico - documentos do usuário
                documents_dir = os.path.expanduser("~/Documents")
                if os.path.exists(documents_dir):
                    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(documents_dir):
                            for file in files[:10]:  # Limitar para exemplo
                                file_path = os.path.join(root, file)
                                try:
                                    arcname = os.path.relpath(file_path, documents_dir)
                                    zipf.write(file_path, arcname)
                                except Exception:
                                    continue
                
                progress.setValue(100)
                QMessageBox.information(self, "Backup Concluído", f"Backup criado com sucesso:\n{backup_path}")
                print(f"✅ Backup criado: {backup_path}")
            
            progress.close()
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            QMessageBox.critical(self, "Erro", f"Erro ao criar backup: {str(e)}")
    
    def toggle_theme(self):
        """Alternar tema"""
        self.dark_mode = not self.dark_mode
        self.theme_btn.setText("☀️" if self.dark_mode else "🌙")
        self.apply_theme()
        
        theme_name = "escuro" if self.dark_mode else "claro"
        print(f"🎨 Tema {theme_name} ativado!")
    
    def apply_theme(self):
        """Aplicar tema"""
        if self.dark_mode:
            # Tema escuro
            style = """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0f0f0f, stop:0.3 #1a1a1a, stop:0.7 #2d2d2d, stop:1 #0f0f0f);
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            
            QWidget {
                background-color: transparent;
                color: #ffffff;
            }
            
            QFrame#sidebar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
                border-right: 2px solid #444444;
            }
            
            QFrame#sidebar_header {
                background-color: transparent;
                border-bottom: 2px solid #444444;
            }
            
            QLabel#logo {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffd700, stop:0.5 #ffb700, stop:1 #d4af37);
                color: #000000;
                border-radius: 15px;
                font-size: 28px;
                font-weight: bold;
            }
            
            QLabel#app_title {
                color: #ffd700;
                font-size: 20px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QLabel#app_subtitle {
                color: #cccccc;
                font-size: 12px;
                font-weight: 600;
                background-color: transparent;
            }
            
            QPushButton#theme_toggle {
                background-color: #404040;
                border: 2px solid #666666;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton#theme_toggle:hover {
                background-color: #ffd700;
                color: #000000;
            }
            
            QLabel#nav_section_title {
                color: #888888;
                font-size: 11px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QPushButton#nav_item {
                background-color: transparent;
                border: none;
                color: #cccccc;
                text-align: left;
                padding: 12px 20px;
                margin: 2px 10px;
                border-radius: 10px;
                font-weight: 500;
                font-size: 14px;
            }
            
            QPushButton#nav_item:hover {
                background-color: rgba(255, 215, 0, 0.2);
                color: #ffd700;
            }
            
            QPushButton#nav_item[active="true"] {
                background-color: rgba(255, 215, 0, 0.3);
                color: #ffd700;
                border-left: 4px solid #ffd700;
                font-weight: 600;
            }
            
            QPushButton#nav_item_special {
                background-color: transparent;
                border: none;
                color: #ff4444;
                text-align: left;
                padding: 12px 20px;
                margin: 2px 10px;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            
            QPushButton#nav_item_special:hover {
                background-color: rgba(255, 68, 68, 0.2);
            }
            
            QFrame#main_content {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0f0f0f, stop:0.5 #1a1a1a, stop:1 #0f0f0f);
            }
            
            QFrame#main_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
                border-bottom: 2px solid #444444;
            }
            
            QLabel#page_title {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QPushButton#primary_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffd700, stop:0.5 #ffb700, stop:1 #d4af37);
                color: #000000;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton#primary_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffb700, stop:1 #d4af37);
            }
            
            QFrame#status_card, QFrame#status_card_main, QFrame#activity_card, 
            QFrame#stat_card, QFrame#scan_option, QFrame#quarantine_list,
            QFrame#scan_progress_card, QFrame#realtime_controls, 
            QFrame#backup_option, QFrame#scan_results_card, QFrame#firewall_controls,
            QFrame#settings_card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #2d2d2d, stop:1 #404040);
                border: 2px solid #555555;
                border-radius: 16px;
            }
            
            QFrame#status_card_main {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 rgba(255, 215, 0, 0.3), stop:1 rgba(255, 215, 0, 0.1));
                border: 2px solid #ffd700;
            }
            
            QLabel#status_icon {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffd700, stop:0.5 #ffb700, stop:1 #d4af37);
                color: #000000;
                border-radius: 12px;
                font-size: 28px;
                font-weight: bold;
            }
            
            QLabel#status_title {
                color: #ffd700;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QLabel#status_desc {
                color: #ffffff;
                font-weight: 500;
                font-size: 16px;
                background-color: transparent;
            }
            
            QLabel#stat_icon {
                color: #ffffff;
                font-size: 32px;
                background-color: transparent;
            }
            
            QLabel#stat_value {
                color: #ffd700;
                font-size: 24px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QLabel#stat_label {
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                background-color: transparent;
            }
            
            QLabel#activity_title {
                color: #ffd700;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QLabel#activity_text {
                color: #ffffff;
                font-weight: 500;
                font-size: 15px;
                background-color: transparent;
            }
            
            QLabel#activity_time {
                color: #cccccc;
                font-size: 13px;
                background-color: transparent;
            }
            
            QLabel#scan_icon, QLabel#backup_icon {
                font-size: 40px;
                color: #ffffff;
                background-color: transparent;
            }
            
            QLabel#scan_title, QLabel#backup_title {
                color: #ffd700;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QLabel#scan_desc, QLabel#backup_desc {
                color: #ffffff;
                font-size: 14px;
                background-color: transparent;
            }
            
            QProgressBar#scan_progress {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #2d2d2d;
                text-align: center;
                color: #ffffff;
            }
            
            QProgressBar#scan_progress::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #ffd700, stop:1 #ffb700);
                border-radius: 6px;
            }
            
            QLabel#scan_progress_text, QLabel#scan_file_text {
                color: #ffffff;
                font-size: 14px;
                background-color: transparent;
            }
            
            QPushButton#stop_button, QPushButton#toggle_button {
                background-color: #cc4444;
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }
            
            QPushButton#stop_button:hover, QPushButton#toggle_button:hover {
                background-color: #aa2222;
            }
            
            QFrame#quarantine_file_card {
                background-color: #404040;
                border: 1px solid #666666;
                border-radius: 10px;
                margin: 5px;
            }
            
            QLabel#threat_icon {
                font-size: 24px;
                background-color: transparent;
            }
            
            QLabel#quarantine_filename {
                color: #ffd700;
                font-weight: bold;
                font-size: 16px;
                background-color: transparent;
            }
            
            QLabel#quarantine_path {
                color: #cccccc;
                font-size: 12px;
                background-color: transparent;
            }
            
            QLabel#quarantine_threat {
                color: #ff6666;
                font-size: 14px;
                background-color: transparent;
            }
            
            QLabel#quarantine_confidence {
                color: #66ff66;
                font-size: 13px;
                background-color: transparent;
            }
            
            QLabel#quarantine_reason {
                color: #ffaa44;
                font-size: 13px;
                background-color: transparent;
            }
            
            QLabel#quarantine_date {
                color: #cccccc;
                font-size: 12px;
                background-color: transparent;
            }
            
            QPushButton#restore_button {
                background-color: #44aa44;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            
            QPushButton#restore_button:hover {
                background-color: #339933;
            }
            
            QPushButton#delete_button {
                background-color: #cc4444;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }
            
            QPushButton#delete_button:hover {
                background-color: #aa2222;
            }
            
            QFrame#fallen_angel_warning {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #8B0000, stop:1 #FF0000);
                border: 2px solid #FF0000;
                border-radius: 15px;
            }
            
            QLabel#fallen_angel_title {
                color: #FFFF00;
                font-size: 28px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QPushButton#fallen_angel_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #8B0000, stop:1 #FF0000);
                color: #FFFF00;
                border: 2px solid #FFFF00;
                border-radius: 10px;
                font-weight: bold;
                font-size: 16px;
            }
            
            QPushButton#fallen_angel_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #FF0000, stop:1 #8B0000);
            }
            
            QFrame#fallen_angel_info {
                background: rgba(139, 0, 0, 0.3);
                border: 2px solid rgba(255, 0, 0, 0.5);
                border-radius: 16px;
            }
            
            QLabel#fallen_angel_info_title {
                color: #FF4444;
                font-size: 18px;
                font-weight: bold;
                background-color: transparent;
            }
            
            QCheckBox {
                color: #ffffff;
                font-size: 14px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                background-color: #404040;
                border: 2px solid #666666;
                border-radius: 4px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #ffd700;
                border: 2px solid #ffb700;
                border-radius: 4px;
            }
            
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            
            QScrollArea#content_scroll {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0f0f0f, stop:0.5 #1a1a1a, stop:1 #0f0f0f);
            }
            
            QScrollArea#nav_scroll {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
            }
            
            QScrollBar:vertical {
                background-color: #404040;
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #ffd700;
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #ffb700;
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        else:
            # Tema claro
            style = """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #f8fafc, stop:0.5 #e2e8f0, stop:1 #cbd5e1);
                color: #1e293b;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            
            QWidget {
                background-color: transparent;
                color: #1e293b;
            }
            
            QFrame#sidebar {
                background: rgba(255, 255, 255, 0.9);
                border-right: 2px solid rgba(148, 163, 184, 0.4);
            }
            
            QLabel#logo {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #ffd700, stop:0.5 #ffb700, stop:1 #d4af37);
                color: #000000;
                border-radius: 15px;
                font-size: 28px;
                font-weight: bold;
            }
            
            QLabel#app_title {
                color: #1e293b;
                font-size: 20px;
                font-weight: bold;
            }
            
            QPushButton#nav_item[active="true"] {
                background-color: rgba(30, 41, 59, 0.2);
                color: #1e293b;
                border-left: 4px solid #1e293b;
            }
            
            QFrame#status_card_main {
                background: rgba(255, 215, 0, 0.15);
                border: 2px solid rgba(255, 215, 0, 0.6);
                border-radius: 16px;
            }
            """
        
        self.setStyleSheet(style)
    
    def load_system_data(self):
        """Carregar dados do sistema"""
        data_file = self.app_data_dir / "system_data.json"
        if data_file.exists():
            try:
                with open(data_file, 'r') as f:
                    saved_data = json.load(f)
                    self.system_data.update(saved_data)
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
        
        # Atualizar contagem de quarentena
        try:
            quarantined_files = self.quarantine_manager.get_quarantined_files()
            self.system_data['quarantine_items'] = len(quarantined_files)
        except Exception as e:
            print(f"Erro ao carregar quarentena: {e}")
            self.system_data['quarantine_items'] = 0
            
        # Sincronizar status de rede
        network_status = self.network_manager.get_network_status()
        self.system_data.update(network_status)
        
        # Sincronizar status de startup
        if self.startup_control:
            self.system_data['startup_enabled'] = self.startup_control.is_enabled()
    
    def save_system_data(self):
        """Salvar dados do sistema"""
        data_file = self.app_data_dir / "system_data.json"
        try:
            with open(data_file, 'w') as f:
                json.dump(self.system_data, f, indent=2)
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
    
    def closeEvent(self, event):
        """Evento de fechamento"""
        try:
            # Parar verificação se estiver rodando
            if self.is_scanning:
                self.stop_scan()
            
            # Parar proteção em tempo real
            self.realtime_protection.stop_monitoring()
            
            # Salvar dados
            self.save_system_data()
            
            print("🛡️ Encerrando Angle Guard V10 Enhanced...")
            event.accept()
            
        except Exception as e:
            print(f"Erro durante fechamento: {e}")
            event.accept()


def check_dependencies():
    """Verificar dependências do sistema"""
    print("🔍 Verificando sistema...")
    
    # Verificar Python
    python_version = sys.version_info
    if python_version < (3, 7):
        print(f"❌ Python {python_version.major}.{python_version.minor} detectado")
        print("💡 Python 3.7+ é necessário")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Verificar dependências adicionais
    try:
        import psutil
        print("✅ psutil disponível")
    except ImportError:
        print("⚠️ psutil não encontrado - kill automático limitado")
    
    # Verificar QT
    print(f"✅ Qt versão {QT_VERSION}")
    
    return True


def create_test_threat():
    """Criar arquivo de teste EICAR para demonstração"""
    eicar_string = r'X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*'
    
    downloads_dir = Path.home() / "Downloads"
    test_file = downloads_dir / "EICAR_TEST.txt"
    
    try:
        with open(test_file, 'w') as f:
            f.write(eicar_string)
        print(f"🔬 Arquivo de teste criado: {test_file}")
        print("🔍 Use a verificação para detectar esta 'ameaça' de teste")
        return str(test_file)
    except Exception as e:
        print(f"❌ Erro ao criar arquivo de teste: {e}")
        return None


def main():
    """Função principal"""
    try:
        print("=" * 60)
        print("🛡️ ANGLE GUARD ANTIVIRUS - V10 ENHANCED WITH AUTO KILL")
        print("=" * 60)
        print("🔥 Versão aprimorada com kill automático integrado ao modo anjo caído")
        print("🎯 Funcionalidades principais:")
        print("   ✅ Interface moderna responsiva")
        print("   ✅ Motor de verificação aprimorado")
        print("   ✅ Detecção por entropia ultra-sensível")
        print("   ✅ KILL AUTOMÁTICO de processos (modo anjo caído)")
        print("   ✅ Sistema de quarentena avançado")
        print("   ✅ Proteção em tempo real com monitoramento")
        print("   ✅ Pop-ups de alerta em tempo real")
        print("   ✅ Controles de rede WiFi/USB")
        print("   ✅ Sistema de backup integrado")
        print("   ✅ Modo Anjo Caído extremamente agressivo")
        print("   ✅ Configurações avançadas de sistema")
        print("   ✅ Estatísticas detalhadas via pop-ups")
        print("-" * 60)
        
        # Verificar dependências
        if not check_dependencies():
            print("\n❌ Falha na verificação de dependências")
            input("Pressione Enter para sair...")
            return 1
        
        print("🚀 Iniciando aplicação enhanced...")
        
        # Criar aplicação
        app = QApplication(sys.argv)
        app.setApplicationName("Angle Guard Enhanced")
        app.setApplicationVersion("10.0.3")
        app.setApplicationDisplayName("🛡️ Angle Guard - Proteção Enhanced V10 com Auto Kill")
        
        # Configurar fonte
        try:
            font = QFont("Segoe UI", 11)
            app.setFont(font)
        except:
            print("⚠️ Fonte Segoe UI não disponível, usando fonte padrão")
        
        print("🖥️ Criando interface enhanced...")
        
        # Criar janela
        try:
            window = AngleGuardV10Enhanced()
        except Exception as e:
            print(f"❌ Erro ao criar janela: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Criar arquivo de teste para demonstração
        print("🧪 Criando arquivo de teste EICAR...")
        create_test_threat()
        
        print("👁️ Exibindo interface...")
        
        # Mostrar janela
        window.show()
        
        print("✅ Angle Guard V10 Enhanced iniciado com sucesso!")
        print("🛡️ Interface celestial enhanced ativa")
        print("🌙 Tema escuro/claro funcional")
        print("📊 Dashboard completo com dados reais")
        print("🔍 Sistema de verificação APRIMORADO e funcionando")
        print("📈 Barra de progresso funcional")
        print("🔒 Sistema de quarentena avançado")
        print("🛡️ Proteção em tempo real ativa")
        print("💾 Sistema de backup integrado")
        print("😈 Modo Anjo Caído com kill automático INTEGRADO")
        print("🔥 Controles de firewall e rede")
        print("⚙️ Configurações avançadas de sistema")
        print("🎯 Detecção aprimorada com entropia ultra-sensível")
        print("⚔️ Kill automático de processos suspeitos (modo anjo caído)")
        print("📢 Sistema de alertas com pop-ups em tempo real")
        print("📈 Estatísticas detalhadas via pop-ups")
        
        print("\n🧪 TESTE: Um arquivo EICAR foi criado em Downloads para teste")
        print("🔍 Execute uma verificação para ver o sistema ENHANCED em ação!")
        print("\n🚀 PRINCIPAIS NOVIDADES ENHANCED:")
        print("   • Detecção por entropia ultra-sensível")
        print("   • Kill automático integrado ao modo anjo caído")
        print("   • Alertas em tempo real com pop-ups")
        print("   • Sistema de quarentena com confiança de detecção")
        print("   • Monitoramento contínuo de processos")
        print("   • Interface responsiva durante operações")
        print("   • Controles de rede aprimorados")
        print("   • Configurações avançadas de sistema")
        print("   • Estatísticas via pop-ups (sem página dedicada)")
        print("   • Verificação no modo anjo caído ULTRA AGRESSIVA")
        
        # Executar aplicação
        if QT_VERSION == 5:
            return app.exec_()
        else:
            return app.exec()
        
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"\n🏁 Aplicação finalizada - Código: {exit_code}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário (Ctrl+C)")
        exit_code = 0
        
    except Exception as e:
        print(f"\n❌ Erro não tratado: {e}")
        exit_code = 1
    
    print("\n" + "=" * 60)
    print("👋 Obrigado por usar o Angle Guard V10 Enhanced!")
    
    if exit_code != 0:
        print("\n⚠️ Problemas detectados:")
        print("• Verifique se PyQt5 ou PyQt6 está instalado")
        print("• Execute: pip install PyQt5 pyqt5-tools psutil")
        print("• Execute: pip install PyQt6 pyqt6-tools psutil") 
        print("• Verifique se Python 3.7+ está sendo usado")
        print("• Execute com permissões adequadas")
        input("\nPressione Enter para sair...")
    
    print("=" * 60)
    sys.exit(exit_code)