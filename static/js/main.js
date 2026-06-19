// ============================================================
// SHARED RESULT ELEMENTS
// ============================================================
const resultWrap  = document.getElementById('resultWrap');
const loadingCard = document.getElementById('loadingCard');
const resultMain  = document.getElementById('resultMain');
const resultImg   = document.getElementById('resultImg');
const resultKelas = document.getElementById('resultKelas');
const resultBadge = document.getElementById('resultBadge');
const confBar     = document.getElementById('confBar');
const confPct     = document.getElementById('confPct');
const probGrid    = document.getElementById('probGrid');
const nutrisiGrid = document.getElementById('nutrisiGrid');
const nutrisiSub  = document.getElementById('nutrisiSubtitle');
const errorCard   = document.getElementById('errorCard');
const errorMsg    = document.getElementById('errorMsg');

// ============================================================
// TAB SWITCHER
// ============================================================
const tabs   = { upload: document.getElementById('tabUpload'),   photo: document.getElementById('tabPhoto'),   rt: document.getElementById('tabRealtime') };
const panels = { upload: document.getElementById('panelUpload'), photo: document.getElementById('panelPhoto'), rt: document.getElementById('panelRealtime') };

function switchTab(name) {
  Object.keys(tabs).forEach(k => {
    tabs[k].classList.toggle('active', k === name);
    panels[k].style.display = k === name ? 'block' : 'none';
  });
  hideResult();
  if (name !== 'photo') stopCamera('photo');
  if (name !== 'rt')    stopRealtime();
}

document.getElementById('tabUpload').addEventListener('click',   () => switchTab('upload'));
document.getElementById('tabPhoto').addEventListener('click',    () => switchTab('photo'));
document.getElementById('tabRealtime').addEventListener('click', () => switchTab('rt'));

// ============================================================
// UTILITIES
// ============================================================
function hideResult() {
  resultWrap.style.display  = 'none';
  resultMain.style.display  = 'none';
  errorCard.style.display   = 'none';
  loadingCard.style.display = 'none';
  confBar.style.width = '0%';
}

const FILL = { 'Matang':'fill-matang', 'Mentah':'fill-mentah', 'Setengah Matang':'fill-setengah' };
const EMOJI = { matang:'🍌', mentah:'🟢', 'setengah-matang':'🌿' };
const BADGE_CLASS = { matang:'badge-matang', mentah:'badge-mentah', 'setengah-matang':'badge-setengah' };

function buildProbBars(container, all_probs, animated=true) {
  container.innerHTML = '';
  Object.entries(all_probs).forEach(([name, pct]) => {
    const row = document.createElement('div');
    row.className = 'prob-item-row';
    row.innerHTML = `<span class="prob-name">${name}</span>
      <div class="prob-bar-outer"><div class="prob-bar-fill ${FILL[name]||'fill-matang'}" data-w="${pct.toFixed(1)}"></div></div>
      <span class="prob-val">${pct.toFixed(1)}%</span>`;
    container.appendChild(row);
  });
  if (animated) setTimeout(() => container.querySelectorAll('.prob-bar-fill').forEach(b => b.style.width = b.dataset.w+'%'), 80);
  else          container.querySelectorAll('.prob-bar-fill').forEach(b => b.style.width = b.dataset.w+'%');
}

function buildNutrisi(container, nutrisi) {
  container.innerHTML = '';
  Object.entries(nutrisi).forEach(([k,v], i) => {
    const el = document.createElement('div');
    el.className = 'nutrisi-item fade-in';
    el.style.animationDelay = `${i*30}ms`;
    el.innerHTML = `<div class="nkey">${k}</div><div class="nval">${v}</div>`;
    container.appendChild(el);
  });
}

async function sendToPredict(file) {
  const fd = new FormData();
  fd.append('file', file);
  const res  = await fetch('/predict', { method:'POST', body:fd });
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || 'Terjadi kesalahan');
  return data;
}

// ============================================================
// TAB 1 — UPLOAD
// ============================================================
const dropZone    = document.getElementById('dropZone');
const fileInput   = document.getElementById('fileInput');
const previewCard = document.getElementById('previewCard');
const previewImg  = document.getElementById('previewImg');
const previewName = document.getElementById('previewName');
const previewSize = document.getElementById('previewSize');

let uploadFile = null;

dropZone.addEventListener('dragover',  e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => { e.preventDefault(); dropZone.classList.remove('dragover'); if(e.dataTransfer.files[0]) handleUpload(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', () => { if(fileInput.files[0]) handleUpload(fileInput.files[0]); });

function handleUpload(f) {
  const ok = ['image/jpeg','image/png','image/webp'];
  if (!ok.includes(f.type)) { alert('Format tidak didukung.'); return; }
  if (f.size > 16*1024*1024) { alert('File terlalu besar (maks 16MB).'); return; }
  uploadFile = f;
  const r = new FileReader();
  r.onload = e => {
    previewImg.src = e.target.result;
    previewName.textContent = f.name.length > 34 ? f.name.slice(0,32)+'…' : f.name;
    previewSize.textContent = (f.size/1024).toFixed(1)+' KB';
    previewCard.style.display = 'block';
    hideResult();
  };
  r.readAsDataURL(f);
}

document.getElementById('btnCancel').addEventListener('click', () => {
  uploadFile = null; previewCard.style.display = 'none';
  fileInput.value = ''; hideResult();
});

document.getElementById('btnAnalyze').addEventListener('click', async () => {
  if (!uploadFile) return;
  resultImg.src = previewImg.src;
  showLoading();
  try {
    const data = await sendToPredict(uploadFile);
    renderResult(data);
  } catch(e) { showError(e.message); }
});

function showLoading() {
  resultWrap.style.display  = 'block';
  loadingCard.style.display = 'block';
  resultMain.style.display  = 'none';
  errorCard.style.display   = 'none';
}
function renderResult(data) {
  const { predicted_class, label, confidence, all_probs, nutrisi } = data;
  resultKelas.textContent = label;
  confPct.textContent = confidence.toFixed(1)+'%';
  setTimeout(() => { confBar.style.width = confidence+'%'; }, 80);
  resultBadge.className = 'badge '+(BADGE_CLASS[predicted_class]||'badge-matang');
  resultBadge.textContent = (EMOJI[predicted_class]||'') + ' ' + label;
  buildProbBars(probGrid, all_probs);
  nutrisiSub.textContent = `— Pisang ${label}`;
  buildNutrisi(nutrisiGrid, nutrisi);
  loadingCard.style.display = 'none';
  resultMain.style.display  = 'block';
  resultMain.classList.add('fade-in');
}
function showError(msg) { errorMsg.textContent = msg; loadingCard.style.display='none'; errorCard.style.display='block'; }

[document.getElementById('btnReset'), document.getElementById('btnResetErr')].forEach(btn => {
  if(btn) btn.addEventListener('click', () => {
    hideResult(); uploadFile=null; previewCard.style.display='none'; fileInput.value='';
    photoPreviewCard.style.display='none'; photoBlob=null;
  });
});

// ============================================================
// TAB 2 — KAMERA FOTO
// ============================================================
const photoVideo       = document.getElementById('photoVideo');
const photoCanvas      = document.getElementById('photoCanvas');
const photoPlaceholder = document.getElementById('photoPlaceholder');
const photoControls    = document.getElementById('photoControls');
const photoPreviewCard = document.getElementById('photoPreviewCard');
const photoPreviewImg  = document.getElementById('photoPreviewImg');
const photoPreviewTime = document.getElementById('photoPreviewTime');

let photoStream = null;
let photoBlob   = null;

document.getElementById('btnCapture').addEventListener('click', () => {
  if (!photoStream) return;
  const w = photoVideo.videoWidth||640, h = photoVideo.videoHeight||480;
  photoCanvas.width=w; photoCanvas.height=h;
  photoCanvas.getContext('2d').drawImage(photoVideo,0,0,w,h);
  const dataURL = photoCanvas.toDataURL('image/jpeg',0.92);
  photoPreviewImg.src = dataURL;
  photoPreviewTime.textContent = new Date().toLocaleTimeString('id-ID');
  photoCanvas.toBlob(b => { photoBlob = b; }, 'image/jpeg', 0.92);
  photoPreviewCard.style.display = 'block';
  hideResult();
});

document.getElementById('btnPhotoRetake').addEventListener('click', () => {
  photoPreviewCard.style.display='none'; photoBlob=null; hideResult();
});

document.getElementById('btnPhotoAnalyze').addEventListener('click', async () => {
  if (!photoBlob) return;
  resultImg.src = photoPreviewImg.src;
  showLoading();
  try {
    const data = await sendToPredict(new File([photoBlob],'foto.jpg',{type:'image/jpeg'}));
    renderResult(data);
  } catch(e) { showError(e.message); }
});

document.getElementById('btnStopPhoto').addEventListener('click', () => stopCamera('photo'));

// ============================================================
// TAB 3 — REAL-TIME
// ============================================================
const rtVideo       = document.getElementById('rtVideo');
const rtCanvas      = document.getElementById('rtCanvas');
const rtPlaceholder = document.getElementById('rtPlaceholder');
const rtVideoWrap   = document.getElementById('rtVideoWrap');
const rtControls    = document.getElementById('rtControls');
const rtStatusBadge = document.getElementById('rtStatusBadge');
const rtPulseDot    = () => rtStatusBadge.querySelector('.pulse-dot');
const btnRtPause    = document.getElementById('btnRtPause');
const btnRtResume   = document.getElementById('btnRtResume');
const rtResultEmpty = document.getElementById('rtResultEmpty');
const rtResultCard  = document.getElementById('rtResultCard');
const rtThumb       = document.getElementById('rtThumb');
const rtKelas       = document.getElementById('rtKelas');
const rtBadge       = document.getElementById('rtBadge');
const rtConfBar     = document.getElementById('rtConfBar');
const rtConfPct     = document.getElementById('rtConfPct');
const rtProbGrid    = document.getElementById('rtProbGrid');
const rtNutrisiGrid = document.getElementById('rtNutrisiGrid');
const rtNutrisiTitle= document.getElementById('rtNutrisiTitle');
const rtTimestamp   = document.getElementById('rtTimestamp');

let rtStream    = null;
let rtInterval  = null;
let rtPaused    = false;
let rtMs        = 2000;
let rtBusy      = false;

// Interval buttons
document.querySelectorAll('.interval-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.interval-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    rtMs = parseInt(btn.dataset.ms);
    if (rtInterval) restartRtLoop();
  });
});

btnRtPause.addEventListener('click', () => {
  rtPaused = true;
  btnRtPause.style.display  = 'none';
  btnRtResume.style.display = 'inline-flex';
  const dot = rtPulseDot();
  if(dot){ dot.classList.remove('scanning'); dot.classList.add('paused'); }
  rtStatusBadge.querySelector('span:last-child') && (rtStatusBadge.lastChild.textContent=' Dijeda');
  setRtStatus('paused','⏸ Dijeda');
});

btnRtResume.addEventListener('click', () => {
  rtPaused = false;
  btnRtPause.style.display  = 'inline-flex';
  btnRtResume.style.display = 'none';
  setRtStatus('scanning','🔍 Scanning…');
});

document.getElementById('btnStopRt').addEventListener('click', () => stopRealtime());

function setRtStatus(state, text) {
  const dot = rtPulseDot();
  if(!dot) return;
  dot.className = 'pulse-dot';
  if(state==='scanning') dot.classList.add('scanning');
  if(state==='paused')   dot.classList.add('paused');
  // update text node
  rtStatusBadge.innerHTML = `<span class="pulse-dot ${state==='scanning'?'scanning':state==='paused'?'paused':''}"></span> ${text}`;
}

async function startCameraStream(videoEl, facing) {
  let constraints;
  if (facing === 'desktop') {
    constraints = { video:{ width:{ideal:1280}, height:{ideal:720} }, audio:false };
  } else {
    constraints = { video:{ facingMode:facing, width:{ideal:1280}, height:{ideal:720} }, audio:false };
  }
  const stream = await navigator.mediaDevices.getUserMedia(constraints);
  videoEl.srcObject = stream;
  return stream;
}

function stopCamera(panel) {
  if (panel === 'photo') {
    if (photoStream) { photoStream.getTracks().forEach(t=>t.stop()); photoStream=null; }
    photoVideo.srcObject = null;
    photoVideo.style.display = 'none';
    photoControls.style.display = 'none';
    photoPlaceholder.style.display = 'flex';
    photoPlaceholder.innerHTML = `<i class="ti ti-camera-off" style="font-size:38px;color:var(--muted);margin-bottom:8px"></i><p>Pilih sumber kamera di atas</p>`;
    document.querySelectorAll('.cam-src-btn[data-panel="photo"]').forEach(b=>b.classList.remove('active'));
  }
}

function stopRealtime() {
  clearInterval(rtInterval); rtInterval=null;
  if (rtStream) { rtStream.getTracks().forEach(t=>t.stop()); rtStream=null; }
  rtVideo.srcObject = null;
  rtVideoWrap.style.display   = 'none';
  rtPlaceholder.style.display = 'flex';
  rtPlaceholder.innerHTML = `<i class="ti ti-scan" style="font-size:38px;color:var(--muted);margin-bottom:8px"></i><p>Pilih sumber kamera di atas</p>`;
  rtControls.style.display = 'none';
  rtPaused = false;
  btnRtPause.style.display  = 'none';
  btnRtResume.style.display = 'none';
  document.querySelectorAll('.cam-src-btn[data-panel="rt"]').forEach(b=>b.classList.remove('active'));
}

function restartRtLoop() {
  clearInterval(rtInterval);
  rtInterval = setInterval(runRtScan, rtMs);
}

async function runRtScan() {
  if (rtPaused || rtBusy || !rtStream) return;
  rtBusy = true;
  setRtStatus('scanning','🔍 Menganalisis…');

  const w = rtVideo.videoWidth||640, h = rtVideo.videoHeight||480;
  rtCanvas.width=w; rtCanvas.height=h;
  rtCanvas.getContext('2d').drawImage(rtVideo,0,0,w,h);
  const dataURL = rtCanvas.toDataURL('image/jpeg',0.85);

  rtCanvas.toBlob(async blob => {
    try {
      const data = await sendToPredict(new File([blob],'rt.jpg',{type:'image/jpeg'}));
      renderRtResult(data, dataURL);
      setRtStatus('scanning','✅ Selesai — scan berikutnya…');
    } catch(e) {
      setRtStatus('paused','⚠️ Error: '+e.message.slice(0,30));
    } finally {
      rtBusy = false;
    }
  }, 'image/jpeg', 0.85);
}

function renderRtResult(data, thumbSrc) {
  const { predicted_class, label, confidence, all_probs, nutrisi } = data;
  rtThumb.src = thumbSrc;
  rtKelas.textContent = label;
  rtBadge.className = 'badge '+(BADGE_CLASS[predicted_class]||'badge-matang');
  rtBadge.textContent = (EMOJI[predicted_class]||'') + ' ' + label;
  rtConfPct.textContent = confidence.toFixed(1)+'%';
  rtConfBar.style.width = confidence+'%';
  buildProbBars(rtProbGrid, all_probs, false);
  rtNutrisiTitle.textContent = `Nutrisi Pisang ${label}`;
  buildNutrisi(rtNutrisiGrid, nutrisi);
  rtTimestamp.textContent = new Date().toLocaleTimeString('id-ID');
  rtResultEmpty.style.display = 'none';
  rtResultCard.style.display  = 'block';
}

// ============================================================
// CAMERA SOURCE BUTTONS (semua panel)
// ============================================================
document.querySelectorAll('.cam-src-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const panel  = btn.dataset.panel;
    const facing = btn.dataset.facing;

    // Update active state untuk panel ini
    document.querySelectorAll(`.cam-src-btn[data-panel="${panel}"]`).forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');

    if (panel === 'photo') {
      stopCamera('photo');
      photoPlaceholder.style.display = 'none';
      try {
        photoStream = await startCameraStream(photoVideo, facing);
        photoVideo.style.display    = 'block';
        photoControls.style.display = 'flex';
      } catch(e) {
        photoPlaceholder.style.display = 'flex';
        photoPlaceholder.innerHTML = `<i class="ti ti-camera-off" style="font-size:36px;color:#e57373;margin-bottom:8px"></i>
          <p style="color:#c62828;font-size:12px">Gagal: ${e.message}</p>
          <p style="color:var(--muted);font-size:11px;margin-top:4px">Pastikan izin kamera diberikan di browser</p>`;
      }
    }

    if (panel === 'rt') {
      stopRealtime();
      rtPlaceholder.style.display = 'none';
      try {
        rtStream = await startCameraStream(rtVideo, facing);
        rtVideoWrap.style.display = 'block';
        rtControls.style.display  = 'flex';
        btnRtPause.style.display  = 'inline-flex';
        btnRtResume.style.display = 'none';
        rtPaused = false;
        setRtStatus('scanning','🔍 Scanning otomatis…');
        await new Promise(r => setTimeout(r, 800)); // tunggu video stabil
        restartRtLoop();
      } catch(e) {
        rtPlaceholder.style.display = 'flex';
        rtPlaceholder.innerHTML = `<i class="ti ti-camera-off" style="font-size:36px;color:#e57373;margin-bottom:8px"></i>
          <p style="color:#c62828;font-size:12px">Gagal: ${e.message}</p>
          <p style="color:var(--muted);font-size:11px;margin-top:4px">Pastikan izin kamera diberikan di browser</p>`;
      }
    }
  });
});
