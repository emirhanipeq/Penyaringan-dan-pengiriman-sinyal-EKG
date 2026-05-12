import os
import time
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, iirnotch
from gpiozero import LED

# ─────────────────────────────────────────────────────────
# ⚙️  AYARLAR (Raspberry Pi 5'e Göre)
# ─────────────────────────────────────────────────────────

# Burayı Raspberry Pi'deki klasör yoluna göre güncelledik
DATA_DIR = "/home/emirhan/ekg_projesi/ecg-id-database-1.0.0" 
PERSON   = "Person_07"
RECORD   = "rec_1"

LED_PIN  = 17 # LED'in bağlı olduğu GPIO pini

# ─────────────────────────────────────────────────────────
# 1. SİNYAL İŞLEME FONKSİYONLARI
# ─────────────────────────────────────────────────────────

def read_wfdb(data_dir, person, record):
    base = os.path.join(data_dir, person, record)
    hea_path = base + ".hea"
    dat_path = base + ".dat"

    with open(hea_path, "r") as f:
        lines = f.readlines()

    header = lines[0].split()
    n_ch = int(header[1])
    fs = int(header[2])

    gains, baselines = [], []
    for i in range(1, 1 + n_ch):
        parts = lines[i].split()
        gains.append(float(parts[2]))
        baselines.append(float(parts[4]))

    raw = np.fromfile(dat_path, dtype=np.int16)
    raw = raw.reshape(-1, n_ch)

    signals = np.zeros_like(raw, dtype=float)
    for c in range(n_ch):
        signals[:, c] = (raw[:, c] - baselines[c]) / gains[c]

    return signals, fs

def baseline_correction(signal, fs, cutoff=0.5, order=4):
    nyq = fs / 2
    b, a = butter(order, cutoff / nyq, btype='high', analog=False)
    return filtfilt(b, a, signal)

def apply_notch_filter(signal, fs, freq=50.0, quality_factor=30.0):
    nyq = fs / 2
    freq_norm = freq / nyq
    b, a = iirnotch(freq_norm, quality_factor)
    return filtfilt(b, a, signal)

# ─────────────────────────────────────────────────────────
# 2. ANA ÇALIŞMA BLOĞU
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"--- EKG Kaydı Okunuyor: {PERSON}/{RECORD} ---")
    
    try:
        # Veriyi oku
        signals, fs = read_wfdb(DATA_DIR, PERSON, RECORD)
        raw_ecg = signals[:, 0]
        
        print("Sinyal filtreleniyor (Notch + Baseline)...")
        corrected_base = baseline_correction(raw_ecg, fs, cutoff=0.5)
        corrected_ecg  = apply_notch_filter(corrected_base, fs)
        
        print("Kalp atışları (R-Peaks) tespit ediliyor...")
        threshold = 0.5 * np.max(corrected_ecg)
        r_cor, _  = find_peaks(corrected_ecg, height=threshold, distance=fs//3)
        
        # Performans için listeyi SET (küme) yapısına çeviriyoruz
        r_cor_set = set(r_cor)
        
        print(f"Toplam {len(r_cor)} kalp atışı tespit edildi.")
        print("-------------------------------------------------")
        print("LED Simülasyonu Başlıyor! (Durdurmak için CTRL+C)")
        
        led = LED(LED_PIN)
        delay = 1.0 / fs         # Saniyede fs kadar örnek (Örn: 0.002 sn)
        blink_duration = 0.1     # LED'in yanık kalma süresi (100ms)
        last_blink_time = 0
        
        for i in range(len(corrected_ecg)):
            loop_start = time.perf_counter()
            
            # Eğer o anki örnek bir kalp atışıysa LED'i yak
            if i in r_cor_set:
                led.on()
                last_blink_time = time.perf_counter()
                print(f"[{i}] KALBİN ATIYOR! <3")

            # Süre dolduysa LED'i söndür
            if led.is_active and (time.perf_counter() - last_blink_time) > blink_duration:
                led.off()
                
            # Gerçek zamanlı akış için hassas bekleme
            elapsed_time = time.perf_counter() - loop_start
            if delay > elapsed_time:
                time.sleep(delay - elapsed_time)
                
        print("\nSimülasyon başarıyla tamamlandı.")
        
    except FileNotFoundError:
        print(f"HATA: Veri dosyası bulunamadı! Lütfen yolu kontrol et: {DATA_DIR}")
    except KeyboardInterrupt:
        print("\nSimülasyon durduruldu.")
    finally:
        if 'led' in locals():
            led.off()