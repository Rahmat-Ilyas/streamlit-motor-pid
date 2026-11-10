# Dashboard Monitoring Control Loop Motor DC (PID Controller)

Aplikasi dashboard berbasis **Streamlit** untuk monitoring *real-time* respon kecepatan Motor DC dan kinerja kontroler PID melalui protokol **MQTT**.

---

## 🚀 Fitur Utama

1. **Koneksi MQTT Non-Blocking (Paho-MQTT + Threading):**
   - Berjalan pada background thread terpisah tanpa memblokir thread UI Streamlit.
   - Reconnect otomatis jika koneksi broker terputus.
   - Status koneksi ditampilkan secara jelas di bagian atas dashboard (*Connected / Disconnected*).
2. **Display Nilai Real-Time (3 Metric Cards Besar):**
   - **Setpoint RPM (Target)** — Berwarna Biru (`#3B82F6`)
   - **RPM Aktual (Feedback Sensor)** — Berwarna Hijau (`#10B981`)
   - **Output PID (Persentase 0-100%)** — Berwarna Oranye (`#F59E0B`)
3. **Deteksi Kondisi Abnormal Otomatis:**
   - **🔴 OSILASI TERDETEKSI:** RPM aktual bolak-balik melewati setpoint > 6 kali dalam 60 data point terakhir.
   - **🟡 DEVIASI TINGGI:** Rata-rata $|setpoint - RPM| > 10\%$ dari setpoint dalam 60 data point terakhir DAN output PID tidak mentok.
   - **🟠 SATURASI:** Output PID $\ge 95\%$ atau $\le 5\%$ selama $> 20$ data point beruntun DAN error $> 10\%$.
   - **🟢 NORMAL:** Sistem beroperasi dalam batas toleransi aman.
4. **Grafik Real-Time Multi-Axis (Plotly):**
   - Menampilkan 3 variabel sekaligus: Setpoint (putus-putus biru), RPM Aktual (solid hijau), dan Output PID (solid oranye).
   - Buffer geser 100 data point terakhir (`collections.deque(maxlen=100)`).
   - Menggunakan dual y-axis (kiri: RPM, kanan: Output PID %) agar skala visual tidak terdistorsi.
5. **Histori Data & Ekspor CSV:**
   - Tabel 20 data terbaru yang di-update otomatis.
   - Tombol unduh data historis lengkap dalam format `.csv`.
6. **Section Parameter PID:**
   - Menampilkan nilai $K_p$, $K_i$, $K_d$ yang aktif saat ini.
   - Nilai dapat diterima dari topik MQTT atau disetel secara manual lewat sidebar.
7. **Built-in Motor Simulator (Demo Mode):**
   - Toggle simulator fisik motor DC jika Mosquitto broker belum dinyalakan.

---

## 🛠️ Cara Menjalankan Aplikasi

Masuk ke folder project dan aktifkan virtual environment:

```bash
cd /home/mats-dev/Project/iot-project/streamlit-motor-pid
source .venv/bin/activate
streamlit run app.py
```

Akses dashboard di browser melalui: **`http://localhost:8501`**

---

## 📡 Konfigurasi Topik MQTT Default

| Variabel | Topik MQTT Default | Format Payload | Contoh Nilai |
|---|---|---|---|
| **Setpoint RPM** | `motor/setpoint` | String Angka | `"1500"` |
| **RPM Aktual** | `motor/rpm_actual` | String Angka | `"1492.5"` |
| **Output PID** | `motor/pid_output` | String Angka (0-100) | `"65.4"` |
| **Parameter PID** | `motor/pid_params` | JSON String | `{"kp": 1.25, "ki": 0.08, "kd": 0.02}` |

---

## 🧪 Skrip Pengujian Pengirim Dummy (Test Publisher)

Tersedia skrip pengirim data otomatis untuk demonstrasi via Mosquitto:

```bash
python test_publisher.py
```

