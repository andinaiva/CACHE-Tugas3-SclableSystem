from flask import Flask, render_template_string, request
import sqlite3
import redis
import time

app = Flask(__name__)
# Koneksi Redis (Tetap pake protocol=2 untuk Windows)
r = redis.Redis(host='localhost', port=6379, decode_responses=True, protocol=2)

def get_sample_ids():
    """Mengambil 3 ID contoh dari database untuk ditampilkan di home"""
    try:
        conn = sqlite3.connect('bank_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT trx_id FROM transaksi LIMIT 3")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except:
        return []

# --- TEMPLATE VERSI CERAH & BERSIH ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>SafeBank Core - Dashboard Cerah</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { 
            background-color: #f8fafc; 
            color: #1e293b; 
            font-family: 'Inter', sans-serif; 
            padding-top: 60px;
        }
        .container { max-width: 800px; }
        .main-card { 
            background: #ffffff; 
            border: none; 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        }
        .header-title { color: #0284c7; font-weight: 800; letter-spacing: -1px; }
        .search-input {
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 16px;
            transition: 0.3s;
        }
        .search-input:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.1);
        }
        .btn-check-data {
            background: #0284c7;
            border: none;
            border-radius: 12px;
            padding: 12px 25px;
            font-weight: 600;
            transition: 0.3s;
        }
        .btn-check-data:hover { background: #0369a1; transform: translateY(-2px); }
        .sample-badge {
            background: #f1f5f9;
            color: #475569;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            margin-right: 10px;
            border: 1px solid #e2e8f0;
            transition: 0.2s;
        }
        .sample-badge:hover { background: #e2e8f0; color: #0284c7; }
        
        /* Notifikasi Status */
        .status-box {
            border-radius: 15px;
            padding: 20px;
            margin-top: 30px;
        }
        .hit-box { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
        .miss-box { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; }
        
        .receipt-table td { padding: 10px 0; border-bottom: 1px solid #f1f5f9; }
        .latency-badge {
            font-family: monospace;
            background: #334155;
            color: #deff9a;
            padding: 3px 8px;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="main-card">
            <div class="text-center mb-5">
                <h2 class="header-title">🏦 SafeBank Core</h2>
                <p class="text-muted">Sistem Monitoring Skalabilitas Real-time</p>
            </div>
            
            <form action="/search" method="get" class="mb-4">
                <div class="input-group">
                    <input type="text" name="id" class="form-control search-input" placeholder="Masukkan ID Transaksi..." required>
                    <button class="btn btn-primary btn-check-data">Periksa</button>
                </div>
            </form>

            <div class="p-3 rounded-4" style="background: #f8fafc; border: 1px dashed #cbd5e1;">
                <p class="mb-2 small fw-bold text-secondary">ID Contoh (Pilih untuk Demo):</p>
                <div class="d-flex flex-wrap">
                    {% for sid in samples %}
                        <a href="/search?id={{ sid }}" class="sample-badge">{{ sid }}</a>
                    {% endfor %}
                </div>
            </div>

            {% if data %}
            <div class="status-box {% if status == 'HIT' %}hit-box{% else %}miss-box{% endif %} shadow-sm">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="m-0 fw-bold">
                        {% if status == 'HIT' %} ⭐ CACHE HIT {% else %} ❌ CACHE MISS {% endif %}
                    </h5>
                    <span class="latency-badge">{{ latency }} ms</span>
                </div>
                
                <table class="table table-borderless m-0 receipt-table" style="color: inherit;">
                    <tr><td width="40%">ID Transaksi</td><td class="fw-bold">{{ data.trx_id }}</td></tr>
                    <tr><td>Nomor Rekening</td><td>{{ data.no_rekening }}</td></tr>
                    <tr><td>Jenis Transaksi</td><td><span class="badge bg-primary opacity-75">{{ data.tipe_transaksi }}</span></td></tr>
                    <tr><td>Nominal</td><td class="h5 fw-bold">Rp {{ "{:,.2f}".format(data.nominal) }}</td></tr>
                    <tr><td>Sumber Data</td><td>{{ "Redis RAM (Sangat Cepat)" if status == 'HIT' else "Database SQLite (Lambat)" }}</td></tr>
                </table>
            </div>
            {% elif error %}
            <div class="alert alert-danger mt-4 border-0 rounded-4">{{ error }}</div>
            {% endif %}
            
            <div class="text-center mt-5">
                <small class="text-muted">Kelompok 4 RPL | Semester 6 Informatika</small>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    samples = get_sample_ids()
    return render_template_string(HTML_TEMPLATE, samples=samples, data=None)

@app.route('/search')
def search():
    trx_id = request.args.get('id')
    samples = get_sample_ids()
    start_time = time.time()
    
    # 1. Cek Redis
    cached_data = r.get(f"bank:trx:{trx_id}")
    
    if cached_data:
        latency = round((time.time() - start_time) * 1000, 4)
        return render_template_string(HTML_TEMPLATE, samples=samples, data=eval(cached_data), status="HIT", latency=latency)
    
    # 2. Cek DB
    conn = sqlite3.connect('bank_data.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transaksi WHERE trx_id = ?", (trx_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        res = dict(row)
        # Simpan ke Redis (TTL 60 detik)
        r.set(f"bank:trx:{trx_id}", str(res), ex=60)
        latency = round((time.time() - start_time) * 1000, 4)
        return render_template_string(HTML_TEMPLATE, samples=samples, data=res, status="MISS", latency=latency)
    
    return render_template_string(HTML_TEMPLATE, samples=samples, error="Data tidak ditemukan!", data=None)

if __name__ == '__main__':
    app.run(port=5000, debug=True)