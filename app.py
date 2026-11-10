"""
Dashboard Monitoring Control Loop Motor DC dengan PID Controller
Dibuat dengan Streamlit, Plotly, Paho-MQTT, dan Pandas
"""

import streamlit as st
import paho.mqtt.client as mqtt
import plotly.graph_objects as go
import pandas as pd
from collections import deque
import threading
import time
from datetime import datetime
import json
import random

# ==============================================================================
# 1. KONFIGURASI HALAMAN & TEMA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Motor DC PID Control Loop Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk Tema: Sidebar Biru Elegan & Konten Light Bersih
st.markdown("""
<style>
    /* Styling Area Konten Utama (Light Theme) */
    .stApp {
        background-color: #F8FAFC;
        color: #0F172A;
    }
    
    /* Header Utama Konten */
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 18px 24px;
        margin-bottom: 20px;
        background-color: #FFFFFF;
        border: 1.5px solid #DBEAFE;
        border-radius: 14px;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.06);
    }
    .header-branding {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .header-icon-box {
        width: 46px;
        height: 46px;
        border-radius: 12px;
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
    }
    .main-header h1 {
        font-size: 1.5rem;
        font-weight: 800;
        margin: 0;
        color: #1E3A8A;
        letter-spacing: -0.3px;
    }
    .main-header p {
        font-size: 0.85rem;
        color: #64748B;
        margin: 2px 0 0 0;
    }

    /* Metric Cards (Elevated Light White Cards dengan Micro-Bars) */
    .metric-card {
        background-color: #FFFFFF;
        border: 1.5px solid #DBEAFE;
        border-radius: 14px;
        padding: 20px 22px;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.05);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 165px;
        margin-bottom: 8px;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
        border-color: #93C5FD;
    }
    .card-setpoint { border-top: 4px solid #2563EB; }
    .card-rpm { border-top: 4px solid #059669; }
    .card-pid { border-top: 4px solid #D97706; }

    .card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .metric-title {
        font-size: 0.8rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .badge-chip {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
    }
    .chip-blue { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
    .chip-green { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
    .chip-amber { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }

    .metric-value-box {
        display: flex;
        align-items: baseline;
        gap: 6px;
        margin: 12px 0 8px 0;
    }
    .metric-val {
        font-size: 2.35rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
        line-height: 1;
        letter-spacing: -0.5px;
    }
    .metric-unit {
        font-size: 0.95rem;
        color: #64748B;
        font-weight: 700;
    }

    /* Micro Progress Bar di dalam Metric Card */
    .mini-progress-bg {
        width: 100%;
        height: 6px;
        background-color: #F1F5F9;
        border-radius: 4px;
        overflow: hidden;
        margin: 6px 0 10px 0;
    }
    .mini-progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    .fill-blue { background: linear-gradient(90deg, #3B82F6, #2563EB); }
    .fill-green { background: linear-gradient(90deg, #10B981, #059669); }
    .fill-amber { background: linear-gradient(90deg, #F59E0B, #D97706); }

    .metric-footer {
        font-size: 0.75rem;
        color: #64748B;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-top: 1px solid #F1F5F9;
        padding-top: 8px;
    }

    /* Khusus Warna Angka Metrik */
    .card-setpoint .metric-val { color: #2563EB; }
    .card-rpm .metric-val { color: #059669; }
    .card-pid .metric-val { color: #D97706; }

    /* Badge Status Kondisi (Alarm Banner SCADA Style) */
    .condition-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        background-color: #FFFFFF;
        border: 1.5px solid #DBEAFE;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.04);
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 18px;
    }
    .condition-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .condition-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #1E3A8A;
    }
    .badge-status {
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.6px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .badge-normal {
        background-color: #ECFDF5;
        color: #059669;
        border: 1.5px solid #6EE7B7;
    }
    .badge-oscillation {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1.5px solid #FCA5A5;
        animation: pulse-red 1.5s infinite;
    }
    .badge-deviation {
        background-color: #FFFBEB;
        color: #D97706;
        border: 1.5px solid #FCD34D;
    }
    .badge-saturation {
        background-color: #FFF7ED;
        color: #C2410C;
        border: 1.5px solid #FDBA74;
    }

    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
        70% { box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }
        100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); }
    }

    /* PID Parameters Container */
    .pid-section-box {
        background-color: #FFFFFF;
        border: 1.5px solid #DBEAFE;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.04);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 18px;
    }
    .pid-section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .pid-section-title {
        font-size: 0.95rem;
        font-weight: 800;
        color: #1E3A8A;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .pid-formula {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: #64748B;
        background: #F1F5F9;
        padding: 3px 8px;
        border-radius: 6px;
    }

    .pid-item {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 12px 16px;
        display: flex;
        flex-direction: column;
        border-left: 4px solid #2563EB;
        transition: transform 0.2s;
    }
    .pid-item:hover {
        transform: translateY(-1px);
    }
    .pid-label {
        font-size: 0.72rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 3px;
    }
    .pid-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.35rem;
        font-weight: 800;
        color: #1E3A8A;
    }
    .pid-desc {
        font-size: 0.7rem;
        color: #94A3AF;
        margin-top: 2px;
    }

    /* Summary Bar di atas tabel */
    .telemetry-strip {
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }
    .telemetry-pill {
        background: #EFF6FF;
        border: 1px solid #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Code Badge di Area Utama */
    code {
        background-color: #EFF6FF !important;
        color: #1D4ED8 !important;
        border: 1px solid #BFDBFE !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
    }

    /* ==========================================================
       STYLING SIDEBAR BIRU MODERN (BLUE THEME SIDEBAR)
       ========================================================== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A8A 0%, #1E40AF 40%, #1D4ED8 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    
    /* Heading & Teks Standar di Sidebar */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-weight: 800 !important;
        letter-spacing: -0.2px !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.22) !important;
    }
    
    /* Label di atas input form */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] label p,
    section[data-testid="stSidebar"] label span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
    }
    
    /* INPUT FORM DI SIDEBAR (Kotak Putih, Teks Hitam Pekat Sangat Jelas) */
    section[data-testid="stSidebar"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] div[data-baseweb="base-input"],
    section[data-testid="stSidebar"] div[data-baseweb="input"] > div,
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] .stTextInput input,
    section[data-testid="stSidebar"] .stNumberInput input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;   /* Teks gelap tajam, sangat kontras */
        -webkit-text-fill-color: #0F172A !important;
        border: 1.5px solid #BFDBFE !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08) !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="input"]:focus-within,
    section[data-testid="stSidebar"] input:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.45) !important;
    }
    
    /* ==========================================================
       TOMBOL DI SIDEBAR (BORDERLESS, MODERN & SLEEK)
       ========================================================== */
    /* Hapus semua border kasar dari seluruh tombol di sidebar */
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stDownloadButton button {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }
    section[data-testid="stSidebar"] button:focus,
    section[data-testid="stSidebar"] button:active,
    section[data-testid="stSidebar"] button:focus-visible {
        outline: none !important;
        border: none !important;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.4) !important;
    }

    /* Tombol Default / Sekunder (Frosted Glass Translucent Button) */
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: rgba(255, 255, 255, 0.16) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.12) !important;
        padding: 0.45rem 0.55rem !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    section[data-testid="stSidebar"] .stButton > button p,
    section[data-testid="stSidebar"] .stButton > button span,
    section[data-testid="stSidebar"] button[kind="secondary"] p,
    section[data-testid="stSidebar"] button[kind="secondary"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.85rem !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover,
    section[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.28) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2) !important;
    }

    /* Tombol Utama / Primary (Emerald Green Gradient untuk Hubungkan / Terapkan) */
    section[data-testid="stSidebar"] button[kind="primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        border-radius: 8px !important;
        box-shadow: 0 3px 10px rgba(16, 185, 129, 0.4) !important;
        padding: 0.45rem 0.65rem !important;
        transition: all 0.2s ease !important;
        white-space: nowrap !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] p,
    section[data-testid="stSidebar"] button[kind="primary"] span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 14px rgba(16, 185, 129, 0.55) !important;
    }
    
    /* Tombol Download CSV di Sidebar */
    section[data-testid="stSidebar"] .stDownloadButton button {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: none !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        border-radius: 8px !important;
        box-shadow: 0 3px 10px rgba(37, 99, 235, 0.4) !important;
        padding: 0.45rem 0.75rem !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stDownloadButton button p,
    section[data-testid="stSidebar"] .stDownloadButton button span {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    section[data-testid="stSidebar"] .stDownloadButton button:hover {
        background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 5px 14px rgba(37, 99, 235, 0.55) !important;
    }

    /* Expander di Sidebar */
    section[data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: rgba(255, 255, 255, 0.12) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary p,
    section[data-testid="stSidebar"] [data-testid="stExpander"] summary span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Slider & Slider values */
    section[data-testid="stSidebar"] .stSlider * {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. DATA MANAGER DENGAN THREAD SAFETY & MQTT BACKGROUND CLIENT
# ==============================================================================
class MotorPIDManager:
    """Mengelola koneksi MQTT di background thread dan menyimpan buffer data hingga 1000 poin."""
    def __init__(self):
        self.lock = threading.Lock()
        self.buffer = deque(maxlen=1000)
        
        # Variabel Terkini
        self.setpoint = 1500.0
        self.rpm_actual = 0.0
        self.pid_output = 0.0
        
        # Parameter PID
        self.kp = 1.25
        self.ki = 0.08
        self.kd = 0.02
        
        # Status Koneksi & Diagnostik
        self.connected = False
        self.last_error = None
        self.last_update_time = None
        
        # MQTT Client Instance
        self.client = None
        self.broker_host = "localhost"
        self.broker_port = 1883
        
        # Default Topics
        self.topic_setpoint = "motor/setpoint"
        self.topic_rpm = "motor/rpm_actual"
        self.topic_pid = "motor/pid_output"
        self.topic_params = "motor/pid_params"

    def update_reading(self, sp=None, rpm=None, pid=None):
        with self.lock:
            now_dt = datetime.now()
            now_str = now_dt.strftime("%H:%M:%S")
            now_iso = now_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            if sp is not None:
                self.setpoint = float(sp)
            if rpm is not None:
                self.rpm_actual = float(rpm)
            if pid is not None:
                # Clamp PID output ke 0 - 100%
                self.pid_output = max(0.0, min(100.0, float(pid)))
            
            self.last_update_time = now_str
            
            # Catat ke buffer data
            point = {
                "Waktu": now_str,
                "WaktuLengkap": now_iso,
                "Setpoint RPM": round(self.setpoint, 1),
                "RPM Aktual": round(self.rpm_actual, 1),
                "Output PID (%)": round(self.pid_output, 1),
                "Timestamp": now_dt.timestamp()
            }
            self.buffer.append(point)

    def get_snapshot(self):
        with self.lock:
            return {
                "setpoint": self.setpoint,
                "rpm_actual": self.rpm_actual,
                "pid_output": self.pid_output,
                "kp": self.kp,
                "ki": self.ki,
                "kd": self.kd,
                "connected": self.connected,
                "last_error": self.last_error,
                "last_update_time": self.last_update_time,
                "buffer": list(self.buffer)
            }


@st.cache_resource
def get_manager():
    """Singleton data manager agar thread MQTT tidak duplikat saat Streamlit rerun."""
    return MotorPIDManager()


manager = get_manager()


# ==============================================================================
# 3. LOGIKA DETEKSI KONDISI ABNORMAL (KONTROL LOOP)
# ==============================================================================
def detect_abnormal_conditions(buffer_list):
    """
    Mendeteksi anomali pada loop kontrol Motor DC sesuai 4 aturan:
    1. SATURASI: PID >95% atau <5% selama >20 data point DAN error >10% setpoint.
    2. OSILASI: RPM bolak-balik melewati setpoint >6 kali dalam 60 data point terakhir.
    3. DEVIASI TINGGI: Rata-rata |setpoint - rpm| > 10% setpoint dalam 60 point DAN PID tidak mentok.
    4. NORMAL: Tidak memenuhi kriteria abnormal di atas.
    """
    if len(buffer_list) < 5:
        return "NORMAL", "badge-normal", "Mengumpulkan sampel awal..."

    latest = buffer_list[-1]
    sp = latest["Setpoint RPM"]
    rpm = latest["RPM Aktual"]
    pid = latest["Output PID (%)"]
    error = abs(sp - rpm)

    # -------------------------------------------------------------
    # Aturan 1: SATURASI
    # Output PID di atas 95% atau di bawah 5% selama >20 data point berturutan
    # DAN error masih besar (>10% setpoint)
    # -------------------------------------------------------------
    if len(buffer_list) >= 20:
        last_20 = buffer_list[-20:]
        pids_20 = [d["Output PID (%)"] for d in last_20]
        all_high = all(p >= 95.0 for p in pids_20)
        all_low = all(p <= 5.0 for p in pids_20)
        
        is_error_large = (sp > 0 and error > 0.10 * sp) or (sp == 0 and rpm > 10)
        if (all_high or all_low) and is_error_large:
            reason = f"Output PID mentok ({'≥95%' if all_high else '≤5%'}) selama 20 sampel beruntun & error >10%!"
            return "SATURASI", "badge-saturation", reason

    # -------------------------------------------------------------
    # Aturan 2: OSILASI
    # RPM aktual bolak-balik melewati setpoint > 6 kali dalam 60 data point terakhir
    # -------------------------------------------------------------
    recent_60 = buffer_list[-60:]
    signs = []
    for d in recent_60:
        diff = d["RPM Aktual"] - d["Setpoint RPM"]
        # Deadband 1 RPM untuk meredam noise sensor murni
        if diff > 1.0:
            signs.append(1)
        elif diff < -1.0:
            signs.append(-1)
            
    crossings = 0
    for i in range(1, len(signs)):
        if signs[i] != signs[i-1]:
            crossings += 1

    if crossings > 6:
        reason = f"Terdeteksi {crossings} kali osilasi (melewati setpoint) dalam 60 sampel terakhir!"
        return "OSILASI TERDETEKSI", "badge-oscillation", reason

    # -------------------------------------------------------------
    # Aturan 3: DEVIASI TINGGI
    # Rata-rata |setpoint - RPM| > 10% setpoint dalam 60 data terakhir
    # DAN output PID tidak mentok di batas (tidak >=95% atau <=5%)
    # -------------------------------------------------------------
    avg_sp_60 = sum(d["Setpoint RPM"] for d in recent_60) / len(recent_60)
    avg_err_60 = sum(abs(d["Setpoint RPM"] - d["RPM Aktual"]) for d in recent_60) / len(recent_60)
    
    if avg_sp_60 > 0:
        if (avg_err_60 > 0.10 * avg_sp_60) and (5.0 < pid < 95.0):
            reason = f"Rata-rata deviasi ({avg_err_60:.1f} RPM) melebihi 10% setpoint ({0.10*avg_sp_60:.1f} RPM) tanpa saturasi PID."
            return "DEVIASI TINGGI", "badge-deviation", reason

    # -------------------------------------------------------------
    # Aturan 4: NORMAL
    # -------------------------------------------------------------
    return "NORMAL", "badge-normal", "Sistem beroperasi optimal dalam batas toleransi normal."


# ==============================================================================
# 4. MQTT CLIENT & THREADING LOGIC (AUTO-RECONNECT & NON-BLOCKING)
# ==============================================================================
def start_mqtt_client(host, port, topic_sp, topic_rpm, topic_pid, topic_params):
    """Menjalankan client MQTT di thread terpisah dengan reconnect otomatis."""
    manager.broker_host = host
    manager.broker_port = port
    manager.topic_setpoint = topic_sp
    manager.topic_rpm = topic_rpm
    manager.topic_pid = topic_pid
    manager.topic_params = topic_params

    def on_connect(client, userdata, flags, rc, properties=None):
        if rc == 0:
            manager.connected = True
            manager.last_error = None
            client.subscribe([(manager.topic_setpoint, 0),
                              (manager.topic_rpm, 0),
                              (manager.topic_pid, 0),
                              (manager.topic_params, 0)])
        else:
            manager.connected = False
            manager.last_error = f"Gagal terhubung, kode status: {rc}"

    def on_disconnect(client, userdata, disconnect_flags_or_rc, *args):
        manager.connected = False
        manager.last_error = "Koneksi ke broker terputus. Menghubungkan ulang..."

    def on_message(client, userdata, msg):
        topic = msg.topic
        payload_str = msg.payload.decode('utf-8', errors='ignore').strip()
        try:
            if topic == manager.topic_setpoint:
                val = float(payload_str)
                manager.update_reading(sp=val)
            elif topic == manager.topic_rpm:
                val = float(payload_str)
                manager.update_reading(rpm=val)
            elif topic == manager.topic_pid:
                val = float(payload_str)
                manager.update_reading(pid=val)
            elif topic == manager.topic_params:
                # Format JSON params: {"kp": 1.2, "ki": 0.05, "kd": 0.02}
                try:
                    data = json.loads(payload_str)
                    with manager.lock:
                        if "kp" in data: manager.kp = float(data["kp"])
                        if "ki" in data: manager.ki = float(data["ki"])
                        if "kd" in data: manager.kd = float(data["kd"])
                except Exception:
                    pass
        except ValueError:
            pass

    # Stop client lama jika sudah berjalan
    if manager.client:
        try:
            manager.client.loop_stop()
            manager.client.disconnect()
        except Exception:
            pass

    try:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"Streamlit-PID-{random.randint(100,999)}")
        except AttributeError:
            client = mqtt.Client(client_id=f"Streamlit-PID-{random.randint(100,999)}")

        client.on_connect = on_connect
        client.on_disconnect = on_disconnect
        client.on_message = on_message

        # Non-blocking async connect & background loop
        client.connect_async(host, port, keepalive=30)
        client.loop_start()
        manager.client = client
    except Exception as e:
        manager.connected = False
        manager.last_error = f"Tidak dapat menjangkau broker: {e}"


# ==============================================================================
# 5. SIMULATOR MOTOR DC (FALLBACK JIKA BROKER BELUM AKTIF)
# ==============================================================================
_simulator_thread_active = False

def run_dc_motor_simulator():
    """Simulator transfer function orde-1 Motor DC + Kontroler PID untuk pengujian mandiri."""
    global _simulator_thread_active
    _simulator_thread_active = True
    
    sim_rpm = 0.0
    integral = 0.0
    prev_error = 0.0
    
    while _simulator_thread_active:
        with manager.lock:
            sp = manager.setpoint
            kp = manager.kp
            ki = manager.ki
            kd = manager.kd

        # PID Calculation
        error = sp - sim_rpm
        integral += error * 0.1
        derivative = (error - prev_error) / 0.1
        prev_error = error
        
        # Anti-windup
        integral = max(-100.0, min(100.0, integral))
        
        pid_val = (kp * error) + (ki * integral) + (kd * derivative)
        pid_clamped = max(0.0, min(100.0, pid_val))
        
        # Motor Dynamics: tau = 0.3s, Kecepatan maks 2000 RPM saat PID 100%
        target_rpm_physics = (pid_clamped / 100.0) * 2000.0
        # Pertambahan kecepatan orde-1 + noise realistis
        sim_rpm += (target_rpm_physics - sim_rpm) * 0.25 + (random.random() - 0.5) * 4.0
        sim_rpm = max(0.0, sim_rpm)
        
        manager.update_reading(sp=sp, rpm=sim_rpm, pid=pid_clamped)
        time.sleep(0.15)


# ==============================================================================
# 6. SIDEBAR: PENGATURAN KONEKSI & PARAMETER PID
# ==============================================================================
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi MQTT Broker")
    broker_ip = st.text_input("Broker Host / IP", value="localhost")
    broker_port = st.number_input("Broker Port", value=1883, min_value=1, max_value=65535)

    with st.expander("📍 Konfigurasi Topik MQTT", expanded=False):
        top_sp = st.text_input("Topic Setpoint RPM", value="motor/setpoint")
        top_rpm = st.text_input("Topic RPM Aktual", value="motor/rpm_actual")
        top_pid = st.text_input("Topic Output PID", value="motor/pid_output")
        top_params = st.text_input("Topic Parameter PID", value="motor/pid_params")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Hubungkan", key="btn_connect", type="primary", use_container_width=True):
            start_mqtt_client(broker_ip, broker_port, top_sp, top_rpm, top_pid, top_params)
            st.toast("Menghubungkan ke MQTT Broker...", icon="🔌")
    with col_btn2:
        if st.button("Putuskan", key="btn_disconnect", type="secondary", use_container_width=True):
            if manager.client:
                manager.client.loop_stop()
                manager.client.disconnect()
            manager.connected = False
            st.toast("Koneksi MQTT diputus.", icon="⏹")

    st.markdown("---")
    st.markdown("### 🧪 Simulator Internal (Demo)")
    sim_enabled = st.toggle("Aktifkan Simulator Motor DC", value=False, 
                            help="Simulasi loop kontrol otomatis jika Mosquitto broker belum dinyalakan.")
    
    if sim_enabled and not _simulator_thread_active:
        sim_thread = threading.Thread(target=run_dc_motor_simulator, daemon=True)
        sim_thread.start()
    elif not sim_enabled and _simulator_thread_active:
        _simulator_thread_active = False

    st.markdown("---")
    st.markdown("### 🎛️ Atur Parameter PID Manual")
    
    # 1-Click Setpoint Presets
    st.markdown("<span style='font-size:0.75rem; text-transform:uppercase; font-weight:700; color:#BFDBFE;'>Preset Cepat Setpoint:</span>", unsafe_allow_html=True)
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        if st.button("1000", key="p_1000", use_container_width=True):
            with manager.lock: manager.setpoint = 1000.0
            st.toast("Setpoint: 1000 RPM", icon="🎯")
    with c_p2:
        if st.button("1500", key="p_1500", use_container_width=True):
            with manager.lock: manager.setpoint = 1500.0
            st.toast("Setpoint: 1500 RPM", icon="🎯")
    with c_p3:
        if st.button("2000", key="p_2000", use_container_width=True):
            with manager.lock: manager.setpoint = 2000.0
            st.toast("Setpoint: 2000 RPM", icon="🎯")

    input_sp = st.slider("Target Setpoint RPM", min_value=0, max_value=2500, value=int(manager.setpoint), step=50)
    input_kp = st.number_input("Kp (Proportional)", value=float(manager.kp), step=0.1, format="%.2f")
    input_ki = st.number_input("Ki (Integral)", value=float(manager.ki), step=0.01, format="%.3f")
    input_kd = st.number_input("Kd (Derivative)", value=float(manager.kd), step=0.01, format="%.3f")

    if st.button("Terapkan Parameter", key="btn_apply_pid", type="primary", use_container_width=True):
        with manager.lock:
            manager.setpoint = float(input_sp)
            manager.kp = float(input_kp)
            manager.ki = float(input_ki)
            manager.kd = float(input_kd)
        st.toast("Parameter diperbarui!", icon="✅")

    st.markdown("---")
    st.markdown("### ⏱️ Pengaturan Riwayat & Refresh")
    chart_history_len = st.select_slider(
        "Jangkauan Histori Grafik",
        options=[30, 60, 100, 200, 500, 1000],
        value=100,
        format_func=lambda x: f"{x} Sampel" if x < 1000 else "Maksimal (1000)",
        help="Atur seberapa panjang riwayat pergerakan motor yang terlihat pada grafik."
    )
    auto_refresh = st.checkbox("Live Refresh Real-time", value=True)
    refresh_rate = st.slider("Interval Refresh (Detik)", 0.2, 2.0, 0.5, 0.1)

    st.markdown("---")
    st.markdown("### 💾 Ekspor Riwayat Data")
    snap_dl = manager.get_snapshot()
    if len(snap_dl["buffer"]) > 0:
        df_csv = pd.DataFrame(snap_dl["buffer"])
        st.download_button(
            label="📥 Unduh CSV Lengkap",
            data=df_csv.to_csv(index=False).encode('utf-8'),
            file_name=f"motor_pid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="sidebar_dl_csv",
            use_container_width=True
        )
    else:
        st.caption("Belum ada data untuk diunduh.")


# Inisialisasi awal client jika belum pernah dibuat
if manager.client is None and not sim_enabled:
    start_mqtt_client(broker_ip, broker_port, top_sp, top_rpm, top_pid, top_params)


# ==============================================================================
# 7. TAMPILAN DASHBOARD UTAMA
# ==============================================================================

# Header & Status Koneksi MQTT
header_placeholder = st.empty()
# Metric Cards
metrics_placeholder = st.empty()
# Anomaly Condition Badge
condition_placeholder = st.empty()
# PID Parameters Section
pid_placeholder = st.empty()
# Real-time Chart
chart_placeholder = st.empty()
# Table & Export Data
table_placeholder = st.empty()


def render_dashboard():
    """Merender seluruh komponen antarmuka dengan snapshot data terbaru."""
    snap = manager.get_snapshot()
    buffer_data = snap["buffer"]
    
    # 1. Header & Status Koneksi SCADA
    status_color = "#059669" if snap["connected"] or sim_enabled else "#DC2626"
    status_label = "TERHUBUNG (SIMULATOR)" if sim_enabled else ("CONNECTED" if snap["connected"] else "DISCONNECTED")
    last_ts = snap["last_update_time"] or datetime.now().strftime("%H:%M:%S")
    sample_count = len(buffer_data)
    
    header_html = f"""<div class="main-header">
<div class="header-branding">
    <div class="header-icon-box">⚡</div>
    <div>
        <h1>DC Motor PID Control Loop Monitoring</h1>
        <p>Industrial SCADA Telemetry & Performance Analytics via MQTT</p>
    </div>
</div>
<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
    <span style="font-size: 0.8rem; color: #64748B;">Broker: <code>{snap.get('broker_host', 'localhost')}:{snap.get('broker_port', 1883)}</code></span>
    <span style="font-size: 0.8rem; color: #64748B; background: #F1F5F9; padding: 4px 8px; border-radius: 6px;">⏱️ {last_ts}</span>
    <span style="padding: 6px 14px; border-radius: 20px; font-size: 0.82rem; font-weight: 800; background-color: {status_color}18; color: {status_color}; border: 1.5px solid {status_color}66;">
        ● {status_label}
    </span>
</div>
</div>"""
    header_placeholder.markdown(header_html, unsafe_allow_html=True)

    # Tampilkan error jika koneksi gagal dan bukan mode simulator
    if not snap["connected"] and not sim_enabled and snap["last_error"]:
        st.warning(f"⚠️ {snap['last_error']}. Pastikan Mosquitto broker berjalan di {broker_ip}:{broker_port} atau aktifkan **Simulator Internal (Demo)** pada sidebar.")

    # 2. Metric Cards Besar dengan Micro-Gauges
    sp_val = snap["setpoint"]
    rpm_val = snap["rpm_actual"]
    pid_val = snap["pid_output"]
    err_val = sp_val - rpm_val
    abs_err = abs(err_val)

    # Kalkulasi bar persentase (0 - 2500 RPM)
    sp_pct = min(100.0, max(0.0, (sp_val / 2500.0) * 100))
    rpm_pct = min(100.0, max(0.0, (rpm_val / 2500.0) * 100))
    pid_pct = min(100.0, max(0.0, pid_val))

    # Tracking Status Chip
    if abs_err <= 25.0 and sp_val > 0:
        tracking_chip = '<span class="badge-chip chip-green">Terkunci (Locked)</span>'
    elif abs_err <= 150.0 and sp_val > 0:
        tracking_chip = '<span class="badge-chip chip-blue">Tracking...</span>'
    else:
        tracking_chip = '<span class="badge-chip chip-amber">Transien / Deviasi</span>'

    # PID Mode Chip
    if pid_val >= 95.0:
        pid_chip = '<span class="badge-chip chip-amber">Saturasi Penuh (95%+)</span>'
    elif pid_val <= 5.0:
        pid_chip = '<span class="badge-chip chip-blue">Cutoff (&le;5%)</span>'
    else:
        pid_chip = '<span class="badge-chip chip-green">Regulasi Linier</span>'

    with metrics_placeholder.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f"""<div class="metric-card card-setpoint">
<div class="card-top">
    <span class="metric-title">🎯 Setpoint RPM (Target)</span>
    <span class="badge-chip chip-blue">Skala 0 - 2500</span>
</div>
<div class="metric-value-box">
    <span class="metric-val">{sp_val:,.1f}</span>
    <span class="metric-unit">RPM</span>
</div>
<div class="mini-progress-bg">
    <div class="mini-progress-fill fill-blue" style="width: {sp_pct:.1f}%;"></div>
</div>
<div class="metric-footer">
    <span>Kanal: <code>{manager.topic_setpoint}</code></span>
    <span>Referensi: {sp_pct:.0f}% Rentang</span>
</div>
</div>""",
                unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"""<div class="metric-card card-rpm">
<div class="card-top">
    <span class="metric-title">⚡ RPM Aktual (Kondisi Saat Ini)</span>
    {tracking_chip}
</div>
<div class="metric-value-box">
    <span class="metric-val">{rpm_val:,.1f}</span>
    <span class="metric-unit">RPM</span>
</div>
<div class="mini-progress-bg">
    <div class="mini-progress-fill fill-green" style="width: {rpm_pct:.1f}%;"></div>
</div>
<div class="metric-footer">
    <span>Error: <strong style="color: {'#059669' if abs_err <= 25 else '#DC2626'};">{err_val:+,.1f} RPM</strong></span>
    <span>Sensor Encoder Feedback</span>
</div>
</div>""",
                unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f"""<div class="metric-card card-pid">
<div class="card-top">
    <span class="metric-title">🎛️ Output PID (Aktuator)</span>
    {pid_chip}
</div>
<div class="metric-value-box">
    <span class="metric-val">{pid_val:.1f}</span>
    <span class="metric-unit">%</span>
</div>
<div class="mini-progress-bg">
    <div class="mini-progress-fill fill-amber" style="width: {pid_pct:.1f}%;"></div>
</div>
<div class="metric-footer">
    <span>Sinyal Kontrol: <strong>{pid_val:.1f}% PWM</strong></span>
    <span>Kanal: <code>{manager.topic_pid}</code></span>
</div>
</div>""",
                unsafe_allow_html=True
            )

    # 3. Deteksi Kondisi Abnormal (Osilasi, Deviasi Tinggi, Saturasi, Normal)
    cond_status, cond_badge_class, cond_desc = detect_abnormal_conditions(buffer_data)

    condition_html = f"""<div class="condition-wrapper">
<div class="condition-left">
    <span class="condition-title">Status Loop Kontrol:</span>
    <span class="badge-status {cond_badge_class}">{cond_status}</span>
</div>
<div style="font-size: 0.85rem; color: #475569; font-weight: 600;">
    {cond_desc}
</div>
</div>"""
    condition_placeholder.markdown(condition_html, unsafe_allow_html=True)

    # 4. Parameter PID Display Section
    with pid_placeholder.container():
        st.markdown(
            f"""<div class="pid-section-box">
<div class="pid-section-header">
    <span class="pid-section-title">🎛️ Parameter Kontroler PID Aktif</span>
    <span class="pid-formula">u(t) = Kp&middot;e(t) + Ki&middot;&int;e(t)dt + Kd&middot;de(t)/dt</span>
</div>
<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px;">
    <div class="pid-item" style="border-left-color: #2563EB;">
        <span class="pid-label">Gain Proportional (Kp)</span>
        <span class="pid-value">{snap['kp']:.3f}</span>
        <span class="pid-desc">Respon cepat thd error saat ini</span>
    </div>
    <div class="pid-item" style="border-left-color: #059669;">
        <span class="pid-label">Gain Integral (Ki)</span>
        <span class="pid-value">{snap['ki']:.4f}</span>
        <span class="pid-desc">Eliminasi steady-state offset</span>
    </div>
    <div class="pid-item" style="border-left-color: #D97706;">
        <span class="pid-label">Gain Derivative (Kd)</span>
        <span class="pid-value">{snap['kd']:.4f}</span>
        <span class="pid-desc">Meredam overshoot & osilasi</span>
    </div>
</div>
</div>""",
            unsafe_allow_html=True
        )

    # 5. Grafik Real-Time Plotly (Jangkauan Histori Dinamis & Kontinu)
    if len(buffer_data) > 0:
        # Potong data sesuai preferensi jangkauan histori pengguna
        chart_data = buffer_data[-chart_history_len:] if len(buffer_data) > chart_history_len else buffer_data
        times = [datetime.fromtimestamp(d.get("Timestamp", time.time())) for d in chart_data]
        sp_series = [d["Setpoint RPM"] for d in chart_data]
        rpm_series = [d["RPM Aktual"] for d in chart_data]
        pid_series = [d["Output PID (%)"] for d in chart_data]

        fig = go.Figure()

        # Setpoint RPM: Garis putus-putus biru (#2563EB)
        fig.add_trace(go.Scatter(
            x=times,
            y=sp_series,
            mode='lines',
            name='Setpoint RPM',
            line=dict(color='#2563EB', width=2.5, dash='dash'),
            yaxis='y1',
            hovertemplate="Setpoint: %{y:,.1f} RPM<extra></extra>"
        ))

        # RPM Aktual: Garis solid hijau (#059669)
        fig.add_trace(go.Scatter(
            x=times,
            y=rpm_series,
            mode='lines',
            name='RPM Aktual',
            line=dict(color='#059669', width=2.8),
            yaxis='y1',
            hovertemplate="RPM Aktual: %{y:,.1f} RPM<extra></extra>"
        ))

        # Output PID: Garis solid oranye (#D97706) pada sumbu Y kanan
        fig.add_trace(go.Scatter(
            x=times,
            y=pid_series,
            mode='lines',
            name='Output PID (%)',
            line=dict(color='#D97706', width=2.2),
            yaxis='y2',
            hovertemplate="Output PID: %{y:.1f}%<extra></extra>"
        ))

        fig.update_layout(
            title=dict(
                text=f"<b>Respon Dinamis Motor DC & Output PID ({len(chart_data)} Data Point Terakhir)</b>",
                font=dict(color="#1E3A8A", size=15)
            ),
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#F8FAFC',
            margin=dict(l=55, r=55, t=55, b=45),
            height=390,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(color="#334155", size=12)
            ),
            xaxis=dict(
                title=dict(text="Waktu Rekam (Timestamp)", font=dict(color="#64748B", size=12)),
                tickformat='%H:%M:%S',
                color="#64748B",
                gridcolor='#E2E8F0',
                tickangle=-25
            ),
            yaxis=dict(
                title=dict(text="Kecepatan Motor (RPM)", font=dict(color="#059669", size=12)),
                color="#059669",
                gridcolor='#E2E8F0',
                side='left'
            ),
            yaxis2=dict(
                title=dict(text="Output PID (%)", font=dict(color="#D97706", size=12)),
                color="#D97706",
                overlaying='y',
                side='right',
                range=[0, 105],
                showgrid=False
            )
        )
        chart_placeholder.plotly_chart(fig, use_container_width=True)
    else:
        chart_placeholder.info("Menunggu data masuk dari MQTT Broker...")

    # 6. Histori Data: Tabel 20 Data Terakhir dengan Strip Statistik
    with table_placeholder.container():
        st.markdown("### 📋 Histori & Statistik Telemetri")
        if len(buffer_data) > 0:
            df_all = pd.DataFrame(buffer_data)
            df_all["Kondisi"] = cond_status

            # Strip Statistik Telemetri
            avg_rpm = df_all["RPM Aktual"].mean()
            max_rpm = df_all["RPM Aktual"].max()
            avg_pid = df_all["Output PID (%)"].mean()
            
            st.markdown(
                f"""<div class="telemetry-strip">
    <span class="telemetry-pill">📊 Sampel: <strong>{sample_count} Data</strong></span>
    <span class="telemetry-pill">⚡ RPM Rata-rata: <strong>{avg_rpm:.1f} RPM</strong></span>
    <span class="telemetry-pill">🚀 RPM Puncak: <strong>{max_rpm:.1f} RPM</strong></span>
    <span class="telemetry-pill">🎛️ PID Rata-rata: <strong>{avg_pid:.1f}%</strong></span>
    <span class="telemetry-pill">🎯 Error Terkini: <strong>{err_val:+,.1f} RPM</strong></span>
</div>""",
                unsafe_allow_html=True
            )
            
            # 20 Data Paling Baru (Urutan Terbalik)
            df_display = df_all.tail(20)[["Waktu", "Setpoint RPM", "RPM Aktual", "Output PID (%)", "Kondisi"]].iloc[::-1]

            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )
            st.caption("💡 Untuk mengunduh data riwayat lengkap, gunakan tombol **'📥 Unduh CSV Lengkap'** di panel sidebar sebelah kiri.")
        else:
            st.write("Belum ada catatan riwayat.")


# ==============================================================================
# 8. SIKLUS LOOP REAL-TIME (NON-BLOCKING DENGAN PLACEHOLDER)
# ==============================================================================
if auto_refresh:
    # Loop update non-blocking menggunakan st.empty()
    while auto_refresh:
        render_dashboard()
        time.sleep(refresh_rate)
else:
    # Single render jika live stream di-pause
    render_dashboard()
    # Single render jika live stream di-pause
    render_dashboard()

