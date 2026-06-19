# 🍌 BananaLens — Panduan Instalasi & Penggunaan

---

## 📁 Struktur Folder

```
banana_app/
├── app.py                  ← Flask backend
├── requirements.txt        ← Library Python
├── model/
│   └── banana.h5           ← ⚠️ MODEL WAJIB ADA DI SINI
├── templates/
│   └── index.html
└── static/
    ├── css/style.css
    ├── js/main.js
    └── uploads/            ← otomatis dibuat
```

---

## ⚙️ LANGKAH INSTALASI (Windows)

### STEP 1 — Pastikan Python 3.11 terinstall
```
python --version
→ Python 3.11.9
```

### STEP 2 — Masuk ke folder proyek
```
cd C:\banana_app
```

### STEP 3 — Install semua library
```
python -m pip install -r requirements.txt
```
⏳ Proses ini 5-10 menit (TensorFlow ~500MB)

### STEP 4 — Letakkan model
Salin file `banana.h5` ke:
```
C:\banana_app\model\banana.h5
```

### STEP 5 — Jalankan server

MODE LAPTOP (HTTP) — untuk pakai di browser laptop:
```
python app.py
```
Buka: http://localhost:5000

MODE HP (HTTPS) — untuk pakai kamera HP:
```
python -m pip install pyopenssl
python app.py --ssl
```
Cari IP laptop dulu:
```
ipconfig
→ IPv4 Address: 192.168.x.x
```
Buka di HP: https://192.168.x.x:5000
→ Browser warning "Not Safe" → klik Advanced → Proceed (normal)

---

## 📱 3 MODE APLIKASI

### Mode 1 — Upload Gambar
- Drag & drop atau klik pilih file
- Format: JPG, PNG, WEBP
- Klik Analisis → hasil tampil

### Mode 2 — Kamera Foto
- Pilih sumber: Depan / Belakang / Webcam
- Klik "Ambil Foto"
- Klik "Analisis" → hasil tampil

### Mode 3 — Real-time Scan
- Pilih sumber kamera
- Kamera langsung aktif dan scan otomatis
- Atur interval: 1 / 2 / 3 detik
- Arahkan pisang → hasil update otomatis
- Tombol Pause untuk berhenti sementara
- Tombol Stop untuk matikan kamera

---

## ❓ TROUBLESHOOTING

| Masalah | Solusi |
|---|---|
| Model belum dimuat | Pastikan banana.h5 ada di folder model/ |
| Kamera tidak muncul | Klik Allow saat browser minta izin kamera |
| HP tidak bisa akses | Jalankan python app.py --ssl dan pastikan 1 WiFi |
| Port sudah dipakai | Ganti port=5000 ke port=5001 di app.py |
| pip not recognized | Gunakan python -m pip install ... |

---

## 🛑 Cara Stop Server
Tekan Ctrl + C di Command Prompt
