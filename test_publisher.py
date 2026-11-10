"""
Skrip Mock Publisher MQTT untuk Pengujian Dashboard Motor DC PID
Mengirim data dummy Setpoint, RPM Aktual, dan Output PID ke Mosquitto localhost.

Jalankan dengan:
python test_publisher.py
"""

import time
import random
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

TOPIC_SETPOINT = "motor/setpoint"
TOPIC_RPM = "motor/rpm_actual"
TOPIC_PID = "motor/pid_output"
TOPIC_PARAMS = "motor/pid_params"

try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="Python-Motor-Mock-Sender")
except AttributeError:
    client = mqtt.Client(client_id="Python-Motor-Mock-Sender")

print(f"Menghubungkan ke broker {BROKER}:{PORT}...")
try:
    client.connect(BROKER, PORT, 60)
except Exception as e:
    print(f"Gagal terhubung ke broker: {e}")
    print("Pastikan mosquitto sudah berjalan di localhost:1883!")
    exit(1)

client.loop_start()

setpoint = 1500.0
rpm = 0.0
kp, ki, kd = 1.25, 0.08, 0.02
integral = 0.0
prev_error = 0.0

print("🚀 Mulai mengirim data loop kontrol motor DC...")
try:
    while True:
        # Simulasi perubahan sesekali setpoint
        if random.random() < 0.03:
            setpoint = random.choice([1200.0, 1500.0, 1800.0, 2000.0])
            print(f"🎯 Setpoint berubah ke: {setpoint} RPM")

        # PID Calculation
        error = setpoint - rpm
        integral += error * 0.1
        integral = max(-100.0, min(100.0, integral))
        derivative = (error - prev_error) / 0.1
        prev_error = error

        pid_val = (kp * error) + (ki * integral) + (kd * derivative)
        pid_clamped = max(0.0, min(100.0, pid_val))

        # Model Dinamika Motor DC
        target_rpm = (pid_clamped / 100.0) * 2100.0
        rpm += (target_rpm - rpm) * 0.3 + (random.random() - 0.5) * 5.0
        rpm = max(0.0, rpm)

        # Publish data ke topik terpisah
        client.publish(TOPIC_SETPOINT, f"{setpoint:.1f}")
        client.publish(TOPIC_RPM, f"{rpm:.1f}")
        client.publish(TOPIC_PID, f"{pid_clamped:.1f}")

        print(f"Sent -> SP: {setpoint:.1f} | RPM: {rpm:.1f} | PID: {pid_clamped:.1f}%")
        time.sleep(0.2)
except KeyboardInterrupt:
    print("\nPengiriman dihentikan.")
    client.loop_stop()
    client.disconnect()

