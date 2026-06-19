import os
import io
import numpy as np
import streamlit as st
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input

# ── Page config ────────────────────────────────────────────────
st.set_page_config(
    page_title="BananaLens — Klasifikasi Kematangan Pisang",
    page_icon="🍌",
    layout="centered",
)

# ── Constants ──────────────────────────────────────────────────
IMG_SIZE = (224, 224)

LABEL_MAP = {
    'matang':          'Matang',
    'mentah':          'Mentah',
    'setengah-matang': 'Setengah Matang',
}

EMOJI = {
    'matang':          '🍌',
    'mentah':          '🟢',
    'setengah-matang': '🌿',
}

BADGE_COLOR = {
    'matang':          '#8B5800',
    'mentah':          '#27500A',
    'setengah-matang': '#3B6D11',
}

BADGE_BG = {
    'matang':          '#FFF8E7',
    'mentah':          '#EAF3DE',
    'setengah-matang': '#F9FBE7',
}

BAR_COLOR = {
    'Matang':          '#F5A623',
    'Mentah':          '#5CB85C',
    'Setengah Matang': '#A8C34F',
}

NUTRISI = {
    'matang': {
        'Energi (Kalori)':   '110 kcal / 100g',
        'Karbohidrat Total': '28.0 g / 100g',
        'Pati':              '~1.0 g / 100g',
        'Resistant Starch':  '<1.0 g / 100g',
        'Total Gula':        '~15.0 g / 100g',
        'Serat Diet':        '4.5 g / 100g',
        'Protein':           '1.8 g / 100g',
        'Lemak':             '0.4 g / 100g',
        'Kadar Air':         '77.2%',
        'Abu (Ash)':         '0.80%',
        'Kalium / K':        '450 mg / 100g',
        'Magnesium / Mg':    '326.7 mg / 100g',
        'Zinc / Zn':         '0.27 mg / 100g',
        'Mangan / Mn':       '0.89 mg / 100g',
        'Vitamin C':         '10.3 mg / 100g',
        'Vitamin B6':        'Tinggi',
        'Indeks Glikemik':   '51',
    },
    'mentah': {
        'Energi (Kalori)':   '89 kcal / 100g',
        'Karbohidrat Total': '22.8 g / 100g',
        'Pati':              '21.0 g / 100g',
        'Resistant Starch':  '~15.0 g / 100g',
        'Total Gula':        '<5.0 g / 100g',
        'Serat Diet':        '18.0 g / 100g',
        'Protein':           '1.3 g / 100g',
        'Lemak':             '0.3 g / 100g',
        'Kadar Air':         '73.5%',
        'Abu (Ash)':         '0.68%',
        'Kalium / K':        '<350 mg / 100g',
        'Magnesium / Mg':    '337.2 mg / 100g',
        'Zinc / Zn':         '0.15 mg / 100g',
        'Mangan / Mn':       '0.51 mg / 100g',
        'Vitamin C':         '~6.0 mg / 100g',
        'Vitamin B6':        'Rendah',
        'Indeks Glikemik':   '42',
    },
    'setengah-matang': {
        'Energi (Kalori)':   '99 kcal / 100g',
        'Karbohidrat Total': '25.2 g / 100g',
        'Pati':              '~10.0 g / 100g',
        'Resistant Starch':  '~5.0 g / 100g',
        'Total Gula':        '~10.0 g / 100g',
        'Serat Diet':        '~9.0 g / 100g',
        'Protein':           '1.5 g / 100g',
        'Lemak':             '0.3 g / 100g',
        'Kadar Air':         '75.0%',
        'Abu (Ash)':         '0.74%',
        'Kalium / K':        '~400 mg / 100g',
        'Magnesium / Mg':    '331.0 mg / 100g',
        'Zinc / Zn':         '0.21 mg / 100g',
        'Mangan / Mn':       '0.70 mg / 100g',
        'Vitamin C':         '~8.0 mg / 100g',
        'Vitamin B6':        'Sedang',
        'Indeks Glikemik':   '46',
    },
}

TIPS = {
    'matang': [
        '✅ Pisang sudah siap dikonsumsi langsung sebagai buah segar.',
        '⚡ Kandungan gula tinggi, cocok untuk sumber energi cepat.',
        '🧠 Tinggi Vitamin B6 yang baik untuk sistem saraf.',
        '🏠 Simpan di suhu ruangan, konsumsi dalam 1–2 hari.',
        '🥤 Bisa digunakan untuk smoothie, jus, atau campuran dessert.',
    ],
    'mentah': [
        '⏳ Pisang belum siap dikonsumsi langsung, rasanya masih sepat.',
        '🦠 Kandungan resistant starch tinggi, baik untuk kesehatan usus.',
        '💉 Indeks glikemik rendah (42), aman untuk penderita diabetes.',
        '🍟 Cocok diolah menjadi keripik pisang atau pisang goreng.',
        '🌡️ Simpan di suhu ruangan hingga kulit menguning.',
    ],
    'setengah-matang': [
        '🟡 Pisang setengah matang, bisa dikonsumsi tapi kurang manis.',
        '⚖️ Kombinasi nutrisi antara pisang mentah dan matang.',
        '🍳 Cocok untuk dikukus atau dipanggang dengan sedikit gula.',
        '📅 Simpan 1–2 hari lagi hingga mencapai kematangan optimal.',
        '🥗 Indeks glikemik sedang (46), cukup baik untuk diet seimbang.',
    ],
}

# ── Custom CSS ─────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.bananalen-header {
    text-align: center;
    padding: 8px 0 20px;
}
.logo-row {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 4px;
}
.logo-icon {
    width: 42px; height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg,#FFD600,#F5A623);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.logo-name {
    font-family: 'Sora', sans-serif;
    font-size: 24px; font-weight: 700;
    letter-spacing: -0.5px;
}
.logo-name span { color: #C47C00; }
.header-desc { font-size: 13px; color: #6B7280; }

.warn-box {
    background: #FFF8E7;
    border: 1px solid #FFD77A;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 12px;
    color: #7A5800;
    margin: 10px auto;
    max-width: 420px;
    text-align: center;
}

.result-card {
    background: #fff;
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 16px;
    padding: 20px;
    margin-top: 16px;
}
.kelas-label {
    font-family: 'Sora', sans-serif;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 4px;
}
.badge-pill {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-bottom: 10px;
}
.conf-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 4px;
}
.section-title {
    font-family: 'Sora', sans-serif;
    font-size: 13px;
    font-weight: 600;
    margin: 16px 0 10px;
    display: flex;
    align-items: center;
    gap: 6px;
    color: #1A1208;
}
.nutrisi-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 8px;
}
.nutrisi-item {
    background: #FAFAF8;
    border: 1px solid rgba(0,0,0,0.07);
    border-radius: 8px;
    padding: 8px 10px;
}
.nkey {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #6B7280;
    margin-bottom: 2px;
}
.nval {
    font-size: 12px;
    font-weight: 500;
    color: #1A1208;
}
.tip-item {
    font-size: 13px;
    color: #374151;
    padding: 6px 0;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}
.tip-item:last-child { border-bottom: none; }
.divider { border: none; border-top: 1px solid rgba(0,0,0,0.07); margin: 14px 0; }
</style>
""", unsafe_allow_html=True)

# ── Model loader (cached) ──────────────────────────────────────
@st.cache_resource(show_spinner="Memuat model CNN…")
def load_banana_model():
    model_path = 'model/banana.keras'
    if not os.path.exists(model_path):
        return None
    try:
        model = load_model(model_path, compile=False)
        return model
    except Exception as e:
        st.error(f"Gagal memuat model: {e}")
        return None

# ── Prediction ─────────────────────────────────────────────────
def predict_image(model, pil_img):
    class_indices = {'matang': 0, 'mentah': 1, 'setengah-matang': 2}
    idx_to_class  = {v: k for k, v in class_indices.items()}

    img  = pil_img.convert('RGB').resize(IMG_SIZE)
    arr  = np.array(img, dtype=np.float32)
    arr  = preprocess_input(arr)
    arr  = np.expand_dims(arr, axis=0)
    preds = model.predict(arr, verbose=0)[0]

    predicted_idx   = int(np.argmax(preds))
    predicted_class = idx_to_class[predicted_idx]
    confidence      = float(preds[predicted_idx]) * 100
    all_probs = {
        LABEL_MAP[idx_to_class[i]]: float(preds[i]) * 100
        for i in range(len(preds))
    }
    return predicted_class, confidence, all_probs

# ── Render result ──────────────────────────────────────────────
def render_result(pil_img, predicted_class, confidence, all_probs):
    label = LABEL_MAP[predicted_class]
    emoji = EMOJI[predicted_class]
    bg    = BADGE_BG[predicted_class]
    fg    = BADGE_COLOR[predicted_class]

    col_img, col_info = st.columns([1, 2])

    with col_img:
        st.image(pil_img, use_container_width=True)

    with col_info:
        st.markdown(f'<div class="kelas-label">{label}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<span class="badge-pill" style="background:{bg};color:{fg};border:1px solid {fg}40">'
            f'{emoji} {label}</span>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="conf-label">Kepercayaan Model</div>', unsafe_allow_html=True)
        st.progress(confidence / 100, text=f"{confidence:.1f}%")

    # Probability distribution
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 Distribusi Probabilitas</div>', unsafe_allow_html=True)
    for name, pct in all_probs.items():
        color = BAR_COLOR.get(name, '#F5A623')
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:7px">
                <span style="min-width:120px;font-size:12px;color:#6B7280">{name}</span>
                <div style="flex:1;height:5px;background:#EDE2C8;border-radius:100px;overflow:hidden">
                    <div style="width:{pct:.1f}%;height:100%;background:{color};border-radius:100px"></div>
                </div>
                <span style="min-width:42px;text-align:right;font-size:12px;font-weight:500">{pct:.1f}%</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Nutrition
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-title">🌿 Kandungan Nutrisi — Pisang {label}</div>',
        unsafe_allow_html=True,
    )
    nutrisi = NUTRISI.get(predicted_class, {})
    items   = list(nutrisi.items())
    pairs   = [items[i:i+2] for i in range(0, len(items), 2)]
    for pair in pairs:
        cols = st.columns(2)
        for col, (k, v) in zip(cols, pair):
            with col:
                st.markdown(
                    f'<div class="nutrisi-item"><div class="nkey">{k}</div><div class="nval">{v}</div></div>',
                    unsafe_allow_html=True,
                )

    # Tips
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">💡 Tips Konsumsi</div>', unsafe_allow_html=True)
    for tip in TIPS.get(predicted_class, []):
        st.markdown(f'<div class="tip-item">{tip}</div>', unsafe_allow_html=True)

# ── Main app ───────────────────────────────────────────────────
def main():
    # Header
    st.markdown("""
    <div class="bananalen-header">
        <div class="logo-row">
            <div class="logo-icon">🍌</div>
            <div class="logo-name">Banana<span>Lens</span></div>
        </div>
        <div class="header-desc">Klasifikasi Kematangan Pisang — MobileNetV2 CNN</div>
    </div>
    """, unsafe_allow_html=True)

    # Load model
    model = load_banana_model()
    if model is None:
        st.markdown(
            '<div class="warn-box">⚠️ Model belum ditemukan — letakkan <strong>banana.keras</strong> di folder <code>model/</code></div>',
            unsafe_allow_html=True,
        )

    # Input tabs
    tab_upload, tab_kamera = st.tabs(["📁 Upload Gambar", "📷 Kamera"])

    pil_img = None
    source  = None

    # ── Tab Upload ─────────────────────────────────────────────
    with tab_upload:
        uploaded = st.file_uploader(
            "Pilih gambar pisang",
            type=["jpg", "jpeg", "png", "webp"],
            label_visibility="collapsed",
        )
        if uploaded:
            pil_img = Image.open(uploaded)
            source  = "upload"
            st.image(pil_img, caption=uploaded.name, use_container_width=True)

    # ── Tab Kamera ─────────────────────────────────────────────
    with tab_kamera:
        st.caption("Gunakan kamera perangkat untuk mengambil foto pisang langsung.")
        cam_img = st.camera_input("Ambil Foto Pisang", label_visibility="collapsed")
        if cam_img:
            pil_img = Image.open(cam_img)
            source  = "kamera"

    # ── Analyze button ─────────────────────────────────────────
    if pil_img is not None:
        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            analyze = st.button("✨ Analisis Kematangan", use_container_width=True, type="primary")

        if analyze:
            if model is None:
                st.error("Model belum dimuat. Pastikan file **banana.keras** ada di folder **model/**.")
            else:
                with st.spinner("Menganalisis gambar pisang…"):
                    try:
                        predicted_class, confidence, all_probs = predict_image(model, pil_img)
                        st.success(f"Hasil: **{LABEL_MAP[predicted_class]}** ({confidence:.1f}%)")
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        render_result(pil_img, predicted_class, confidence, all_probs)
                        st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Gagal memproses gambar: {e}")

if __name__ == '__main__':
    main()