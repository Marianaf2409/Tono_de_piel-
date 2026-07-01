// SKINTONE ID - JS FINAL FUNCIONAL

const API = (location.hostname === 'localhost' || location.hostname === '127.0.0.1') ? 'http://localhost:8000' : '/api';
const HISTORY_KEY = 'skintone_history';

let current = null;
let history = [];
let stream = null;
let filterOn = false;
let capturedImageData = null;

document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    bindEvents();
    document.getElementById('year').textContent = new Date().getFullYear();
});

function bindEvents() {
    document.getElementById('startBtn').addEventListener('click', openScanner);
    document.getElementById('captureBtn').addEventListener('click', capture);
    document.getElementById('cancelBtn').addEventListener('click', closeScanner);
    document.getElementById('filterBtn').addEventListener('click', toggleFilter);
    document.getElementById('newScanBtn').addEventListener('click', openScanner);
    document.getElementById('saveBtn').addEventListener('click', saveToHistory);
    document.getElementById('backBtn').addEventListener('click', goBack);
    document.getElementById('themeBtn').addEventListener('click', toggleTheme);
    document.getElementById('errClose').addEventListener('click', hideError);
    
    const nameInput = document.getElementById('userName');
    if (nameInput) {
        nameInput.addEventListener('input', updateNameOverlay);
    }
    
    document.querySelectorAll('.acc-header').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.parentElement.classList.toggle('open');
        });
    });
}

function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    html.setAttribute('data-theme', isDark ? 'light' : 'dark');
    const btn = document.getElementById('themeBtn');
    btn.innerHTML = isDark ? '☀️ Claro' : '🌙 Oscuro';
}

function openScanner() {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('scanner').classList.add('active');
    startCamera();
}

function closeScanner() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }
    if (filterOn) toggleFilter();
    
    const nameOverlay = document.getElementById('userNameOverlay');
    if (nameOverlay) {
        nameOverlay.classList.remove('show');
    }
    
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('dashboard').classList.add('active');
}

function goBack() {
    closeScanner();
    renderHistory();
}

async function startCamera() {
    try {
        const video = document.getElementById('video');
        stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: 640, height: 640 }
        });
        video.srcObject = stream;
        
        updateNameOverlay();
    } catch (e) {
        showError('No se pudo acceder a la cámara. Permite el acceso.');
        closeScanner();
    }
}

function updateNameOverlay() {
    const nameInput = document.getElementById('userName');
    const nameOverlay = document.getElementById('userNameOverlay');
    if (nameInput && nameOverlay) {
        const name = nameInput.value.trim();
        nameOverlay.textContent = name;
        if (name) {
            nameOverlay.classList.add('show');
        } else {
            nameOverlay.classList.remove('show');
        }
    }
}

function toggleFilter() {
    filterOn = !filterOn;
    const overlay = document.getElementById('filterOverlay');
    const btn = document.getElementById('filterBtn');
    
    if (filterOn) {
        overlay.classList.add('on');
        btn.classList.replace('btn-secondary', 'btn-primary');
        btn.innerHTML = '✅ Filtro Activado';
    } else {
        overlay.classList.remove('on');
        btn.classList.replace('btn-primary', 'btn-secondary');
        btn.innerHTML = '💡 Filtro Luz Neutra';
    }
}

async function capture() {
    if (!stream) {
        showError('La cámara no está activa');
        return;
    }
    
    try {
        showLoading(true);
        
        const canvas = document.getElementById('canvas');
        const video = document.getElementById('video');
        const ctx = canvas.getContext('2d');
        
        canvas.width = video.videoWidth || 640;
        canvas.height = video.videoHeight || 640;
        ctx.drawImage(video, 0, 0);
        
        const imageBase64 = canvas.toDataURL('image/jpeg', 0.8);
        const imgData = imageBase64.split(',')[1];
        
        capturedImageData = imageBase64;
        
        closeScanner();
        
        const res = await fetch(`${API}/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_base64: imgData })
        });
        
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Error');
        }
        
        current = await res.json();
        showResults();
    } catch (e) {
        showError(e.message);
    } finally {
        showLoading(false);
    }
}

function showResults() {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const resultsEl = document.getElementById('results');
    if (resultsEl) resultsEl.classList.add('active');
    
    const a = current;
    
    const strip = document.getElementById('strip');
    const circle = document.getElementById('colorCircle');
    const capturedPhoto = document.getElementById('capturedPhoto');
    const userNameDisplay = document.getElementById('userNameDisplay');
    const tone = document.getElementById('toneName');
    const fitz = document.getElementById('fitzBadge');
    const undertoneEl = document.getElementById('undertone');
    const combo = document.getElementById('combo');
    const recsList = document.getElementById('recsList');
    
    const nameInput = document.getElementById('userName');
    if (userNameDisplay && nameInput) {
        const name = nameInput.value.trim();
        userNameDisplay.textContent = name || 'Usuario';
    }
    
    if (strip) strip.style.backgroundColor = a.hex_code;
    if (circle) circle.style.backgroundColor = a.hex_code;
    
    if (capturedPhoto && capturedImageData) {
        capturedPhoto.src = capturedImageData;
        capturedPhoto.classList.add('loaded');
    }
    
    if (strip) strip.style.backgroundColor = a.hex_code;
    if (circle) circle.style.backgroundColor = a.hex_code;
    
    if (capturedPhoto && capturedImageData) {
        capturedPhoto.src = capturedImageData;
        capturedPhoto.classList.add('loaded');
    }
    if (tone) tone.textContent = a.tone_name;
    if (fitz) fitz.textContent = `Fitzpatrick ${a.fitzpatrick_score} de 6`;
    if (undertoneEl) {
        undertoneEl.textContent = a.undertone;
        undertoneEl.className = 'badge';
        if (a.undertone === 'Cálido') {
            undertoneEl.classList.add('undertone-warm');
        } else if (a.undertone === 'Frío') {
            undertoneEl.classList.add('undertone-cool');
        } else {
            undertoneEl.classList.add('undertone-neutral-tono');
        }
    }
    if (combo) combo.textContent = `${a.tone_name} · ${a.undertone}`;
    
    if (recsList) {
        recsList.innerHTML = a.recommendations.map(r => `<li>${r}</li>`).join('');
    }
    
    const c1 = document.getElementById('c1');
    const c2 = document.getElementById('c2');
    const c3 = document.getElementById('c3');
    const c4 = document.getElementById('c4');
    if (c1) c1.style.backgroundColor = a.palette.primary;
    if (c2) c2.style.backgroundColor = a.palette.complementary;
    if (c3) c3.style.backgroundColor = a.palette.analogous;
    if (c4) c4.style.backgroundColor = a.palette.highlight;
    
    const a1 = document.getElementById('a1');
    const a2 = document.getElementById('a2');
    const a3 = document.getElementById('a3');
    const avoidNote = document.getElementById('avoidNote');
    if (a1) a1.style.backgroundColor = a.unflattering.unflattering_primary;
    if (a2) a2.style.backgroundColor = a.unflattering.unflattering_secondary;
    if (a3) a3.style.backgroundColor = a.unflattering.muddy_tone;
    if (avoidNote) avoidNote.textContent = a.unflattering.avoid_note;
    
    const hexVal = document.getElementById('hexVal');
    const rgbVal = document.getElementById('rgbVal');
    if (hexVal) hexVal.textContent = a.hex_code;
    if (rgbVal) rgbVal.textContent = `rgb(${a.rgb_values.r}, ${a.rgb_values.g}, ${a.rgb_values.b})`;
    
    const card = document.getElementById('resultsCard');
    if (card) {
        card.style.boxShadow = `0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 0 50px ${a.hex_code}30`;
    }
}

function showLoading(show) {
    const el = document.getElementById('loading');
    const laser = document.getElementById('laser');
    
    if (!el || !laser) return;
    
    if (show) {
        el.classList.remove('hidden');
        laser.classList.add('on');
    } else {
        el.classList.add('hidden');
        laser.classList.remove('on');
    }
}

function saveToHistory() {
    if (!current) {
        showError('No hay análisis para guardar');
        return;
    }
    
    const record = {
        id: crypto.randomUUID(),
        time: new Date().toLocaleString('es-ES'),
        hex: current.hex_code,
        fitz: current.fitzpatrick_score,
        undertone: current.undertone
    };
    
    history.unshift(record);
    if (history.length > 5) history = history.slice(0, 5);
    
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    showError('Guardado correctamente', 'success');
    renderHistory();
}

function deleteFromHistory(id, e) {
    if (e) e.stopPropagation();
    history = history.filter(r => r.id !== id);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
    renderHistory();
}

function loadHistory() {
    try {
        const data = localStorage.getItem(HISTORY_KEY);
        history = data ? JSON.parse(data) : [];
    } catch (e) {
        history = [];
    }
}

function renderHistory() {
    const container = document.getElementById('historyList');
    if (!container) return;
    
    if (history.length === 0) {
        container.innerHTML = '<p class="empty">Sin análisis previos</p>';
        return;
    }
    
    container.innerHTML = history.map(r => `
        <div class="history-item" onclick='loadFromHistory(${JSON.stringify(r)})'>
            <div class="history-dot" style="background:${r.hex}"></div>
            <div class="history-info">
                <p class="history-time">${r.time}</p>
                <p class="history-code">${r.hex}</p>
            </div>
            <button class="history-del" onclick="deleteFromHistory('${r.id}', event)">✕</button>
        </div>
    `).join('');
}

function loadFromHistory(record) {
    current = {
        hex_code: record.hex,
        rgb_values: hexToRgb(record.hex),
        fitzpatrick_score: record.fitz,
        tone_name: fitzToName(record.fitz),
        undertone: record.undertone,
        recommendations: mockRecs(record.fitz, record.undertone),
        palette: mockPalette(record.hex),
        unflattering: mockUnflattering(record.hex, record.undertone)
    };
    showResults();
}

function showError(msg, type = 'error') {
    const box = document.getElementById('errorBox');
    const text = document.getElementById('errorText');
    text.textContent = msg;
    box.classList.remove('hidden');
    
    if (type === 'success') {
        box.classList.add('success');
    } else {
        box.classList.remove('success');
    }
    
    setTimeout(hideError, 4000);
}

function hideError() {
    document.getElementById('errorBox').classList.add('hidden');
}

function hexToRgb(hex) {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return m ? { r: parseInt(m[1],16), g: parseInt(m[2],16), b: parseInt(m[3],16) } : {r:0,g:0,b:0};
}

function fitzToName(f) {
    const names = {1:'Blanco', 2:'Claro', 3:'Trigueño Claro', 4:'Trigueño', 5:'Moreno', 6:'Negro'};
    return names[f] || 'Indefinido';
}

function mockRecs(fitz, undertone) {
    const recs = [];
    if (fitz <= 2) {
        recs.push('Protector solar SPF 50+ diario');
        recs.push('Evita exposición solar prolongada');
    } else if (fitz <= 4) {
        recs.push('Protector solar SPF 30+');
        recs.push('Tolera sol moderado');
    } else {
        recs.push('SPF 15-30 preventivo');
        recs.push('Enfócate en antienvejecimiento');
    }
    if (undertone === 'Cálido') recs.push('Los tonos dorados te favorecen');
    else if (undertone === 'Frío') recs.push('Los plateados son tu mejor aliado');
    else recs.push('Versátil con dorados y plateados');
    return recs;
}

function mockPalette(hex) {
    return {
        primary: hex,
        complementary: '#000000',
        analogous: '#808080',
        highlight: '#FFFFFF'
    };
}

function mockUnflattering(hex, undertone) {
    const r = parseInt(hex.slice(1,3), 16);
    const g = parseInt(hex.slice(3,5), 16);
    const b = parseInt(hex.slice(5,7), 16);
    
    if (undertone === 'Cálido') {
        return {
            unflattering_primary: `rgb(${Math.max(0,r-60)},${Math.max(0,g-40)},${Math.min(255,b+80)})`,
            unflattering_secondary: `rgb(${Math.min(255,r+30)},${Math.min(255,g+30)},${Math.max(0,b-50)})`,
            muddy_tone: `rgb(${Math.max(0,r-30)},${Math.max(0,g-30)},${Math.max(0,b-30)})`,
            avoid_note: 'Evita plateados y tonos azulados fríos'
        };
    } else if (undertone === 'Frío') {
        return {
            unflattering_primary: `rgb(${Math.min(255,r+70)},${Math.min(255,g+40)},${Math.max(0,b-30)})`,
            unflattering_secondary: `rgb(${Math.min(255,r+40)},${Math.min(255,g+60)},${Math.min(255,b+40)})`,
            muddy_tone: `rgb(${Math.max(0,r-30)},${Math.max(0,g-30)},${Math.max(0,b-30)})`,
            avoid_note: 'Evita tonos dorados y naranjas cálidos'
        };
    } else {
        return {
            unflattering_primary: `rgb(${Math.min(255,r+50)},${Math.min(255,g+50)},${Math.min(255,b+50)})`,
            unflattering_secondary: `rgb(${Math.max(0,r-40)},${Math.max(0,g-40)},${Math.max(0,b-40)})`,
            muddy_tone: `rgb(${Math.max(0,r-30)},${Math.max(0,g-30)},${Math.max(0,b-30)})`,
            avoid_note: 'Evita extremos muy cálidos o muy fríos'
        };
    }
}

console.log('SkinTone ID listo');
