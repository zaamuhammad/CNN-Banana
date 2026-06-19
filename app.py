import os
import numpy as np
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
# TF 2.19 (Keras 3) — preprocess_input tetap tersedia di sini
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# Keras 3 menyimpan model dalam format .keras secara default,
# tapi .h5 masih didukung dengan parameter berikut
import os
os.environ['TF_USE_LEGACY_KERAS'] = '0'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

IMG_SIZE = (224, 224)

# === Label mapping (folder name -> label tampilan) ===
LABEL_MAP = {
    'matang':          'Matang',
    'mentah':          'Mentah',
    'setengah-matang': 'Setengah Matang',
}

# === Data nutrisi per kelas folder ===
NUTRISI = {
    'matang': {
        'Energi (Kalori)':  '110 kcal / 100g',
        'Karbohidrat Total':'28.0 g / 100g',
        'Pati':             '~1.0 g / 100g',
        'Resistant Starch': '<1.0 g / 100g',
        'Total Gula':       '~15.0 g / 100g',
        'Serat Diet':       '4.5 g / 100g',
        'Protein':          '1.8 g / 100g',
        'Lemak':            '0.4 g / 100g',
        'Kadar Air':        '77.2%',
        'Abu (Ash)':        '0.80%',
        'Kalium / K':       '450 mg / 100g',
        'Magnesium / Mg':   '326.7 mg / 100g',
        'Zinc / Zn':        '0.27 mg / 100g',
        'Mangan / Mn':      '0.89 mg / 100g',
        'Vitamin C':        '10.3 mg / 100g',
        'Vitamin B6':       'Tinggi',
        'Indeks Glikemik':  '51',
    },
    'mentah': {
        'Energi (Kalori)':  '89 kcal / 100g',
        'Karbohidrat Total':'22.8 g / 100g',
        'Pati':             '21.0 g / 100g',
        'Resistant Starch': '~15.0 g / 100g',
        'Total Gula':       '<5.0 g / 100g',
        'Serat Diet':       '18.0 g / 100g',
        'Protein':          '1.3 g / 100g',
        'Lemak':            '0.3 g / 100g',
        'Kadar Air':        '73.5%',
        'Abu (Ash)':        '0.68%',
        'Kalium / K':       '<350 mg / 100g',
        'Magnesium / Mg':   '337.2 mg / 100g',
        'Zinc / Zn':        '0.15 mg / 100g',
        'Mangan / Mn':      '0.51 mg / 100g',
        'Vitamin C':        '~6.0 mg / 100g',
        'Vitamin B6':       'Rendah',
        'Indeks Glikemik':  '42',
    },
    'setengah-matang': {
        'Energi (Kalori)':  '99 kcal / 100g',
        'Karbohidrat Total':'25.2 g / 100g',
        'Pati':             '~10.0 g / 100g',
        'Resistant Starch': '~5.0 g / 100g',
        'Total Gula':       '~10.0 g / 100g',
        'Serat Diet':       '~9.0 g / 100g',
        'Protein':          '1.5 g / 100g',
        'Lemak':            '0.3 g / 100g',
        'Kadar Air':        '75.0%',
        'Abu (Ash)':        '0.74%',
        'Kalium / K':       '~400 mg / 100g',
        'Magnesium / Mg':   '331.0 mg / 100g',
        'Zinc / Zn':        '0.21 mg / 100g',
        'Mangan / Mn':      '0.70 mg / 100g',
        'Vitamin C':        '~8.0 mg / 100g',
        'Vitamin B6':       'Sedang',
        'Indeks Glikemik':  '46',
    },
}

TIPS = {
    'matang': [
        'Pisang sudah siap dikonsumsi langsung sebagai buah segar.',
        'Kandungan gula tinggi, cocok untuk sumber energi cepat.',
        'Tinggi Vitamin B6 yang baik untuk sistem saraf.',
        'Simpan di suhu ruangan, konsumsi dalam 1-2 hari.',
        'Bisa digunakan untuk smoothie, jus, atau campuran dessert.',
    ],
    'mentah': [
        'Pisang belum siap dikonsumsi langsung, rasanya masih sepat.',
        'Kandungan resistant starch tinggi, baik untuk kesehatan usus.',
        'Indeks glikemik rendah (42), aman untuk penderita diabetes.',
        'Cocok diolah menjadi keripik pisang atau pisang goreng.',
        'Simpan di suhu ruangan hingga kulit menguning.',
    ],
    'setengah-matang': [
        'Pisang setengah matang, bisa dikonsumsi tapi kurang manis.',
        'Kombinasi nutrisi antara pisang mentah dan matang.',
        'Cocok untuk dikukus atau dipanggang dengan sedikit gula.',
        'Simpan 1-2 hari lagi hingga mencapai kematangan optimal.',
        'Indeks glikemik sedang (46), cukup baik untuk diet seimbang.',
    ],
}

# Load model saat startup
model = None
class_indices = None  # dict: {folder_name: index}

def load_banana_model():
    global model, class_indices
    model_path = 'model/banana.keras'
    if not os.path.exists(model_path):
        print(f"⚠️  Model tidak ditemukan di {model_path}")
        return False
    try:
        model = load_model(model_path, compile=False)
        # Urutan kelas sesuai ImageDataGenerator (alphabetical)
        # matang=0, mentah=1, setengah-matang=2
        class_indices = {'matang': 0, 'mentah': 1, 'setengah-matang': 2}
        print("✅ Model berhasil dimuat!")
        return True
    except Exception as e:
        print(f"❌ Gagal memuat model: {e}")
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def predict_image(filepath):
    img = Image.open(filepath).convert('RGB').resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32)
    arr = preprocess_input(arr)
    arr = np.expand_dims(arr, axis=0)
    preds = model.predict(arr, verbose=0)[0]
    # index -> folder name
    idx_to_class = {v: k for k, v in class_indices.items()}
    predicted_idx = int(np.argmax(preds))
    predicted_class = idx_to_class[predicted_idx]
    confidence = float(preds[predicted_idx]) * 100
    # semua probabilitas
    all_probs = {idx_to_class[i]: float(preds[i]) * 100 for i in range(len(preds))}
    return predicted_class, confidence, all_probs

@app.route('/')
def index():
    model_loaded = model is not None
    return render_template('index.html', model_loaded=model_loaded)

@app.route('/predict', methods=['POST'])
def predict():
    if model is None:
        return jsonify({'error': 'Model belum dimuat. Pastikan file banana.h5 ada di folder model/'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'Tidak ada file yang diunggah'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Pilih file terlebih dahulu'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Format file tidak didukung. Gunakan JPG, PNG, atau WEBP'}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    try:
        predicted_class, confidence, all_probs = predict_image(save_path)
        label = LABEL_MAP.get(predicted_class, predicted_class)
        nutrisi = NUTRISI.get(predicted_class, {})
        tips = TIPS.get(predicted_class, [])

        return jsonify({
            'success': True,
            'predicted_class': predicted_class,
            'label': label,
            'confidence': round(confidence, 2),
            'all_probs': {LABEL_MAP.get(k, k): round(v, 2) for k, v in all_probs.items()},
            'nutrisi': nutrisi,
            'image_url': f'/static/uploads/{filename}',
        })
    except Exception as e:
        return jsonify({'error': f'Gagal memproses gambar: {str(e)}'}), 500

if __name__ == '__main__':
    import sys
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('model', exist_ok=True)
    load_banana_model()

    # Normal  : python app.py
    # HP HTTPS: python app.py --ssl
    ssl_mode = '--ssl' in sys.argv
    if ssl_mode:
        print("🔒 Mode HTTPS aktif — akses HP via https://<IP_LAPTOP>:5000")
        print("   Browser akan warning 'not safe', klik Advanced lalu Proceed")
        app.run(debug=False, host='0.0.0.0', port=5000, ssl_context='adhoc')
    else:
        print("🌐 Mode HTTP — akses via http://localhost:5000")
        print("   Untuk kamera HP jalankan: python app.py --ssl")
        app.run(debug=True, host='0.0.0.0', port=5000)
