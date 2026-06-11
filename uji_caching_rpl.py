import redis
import time

# FIX: Ditambahkan protocol=2 agar kompatibel dengan Redis v5 di Windows
r = redis.Redis(host='localhost', port=6379, decode_responses=True, protocol=2)

def ambil_data_dari_database_utama(id_produk):
    """Simulasi query database asli yang lambat"""
    print(f"--> [DATABASE] Mencari produk {id_produk} ke database utama... (Proses Lambat 2 Detik)")
    time.sleep(2) 
    return f"Detail Informasi Produk Kuliah Scalable System {id_produk}"

def dapatkan_produk(id_produk):
    print(f"\n[REQUEST] User meminta data untuk produk: {id_produk}")
    waktu_mulai = time.time()
    
    # STRATEGI CACHE ASIDE [cite: 58]: Cek ke Redis Cache [cite: 51, 62]
    try:
        data_di_cache = r.get(f"produk:{id_produk}")
    except Exception as e:
        print(f"    ❌ Gagal terhubung ke Redis Server: {e}")
        return None
    
    if data_di_cache:
        # KONDISI: CACHE HIT [cite: 21, 22]
        waktu_selesai = time.time() - waktu_mulai
        print(f"    ⭐ [CACHE HIT] Data ditemukan di Redis!")
        print(f"    Hasil: {data_di_cache}")
        print(f"    Waktu Respons: {waktu_selesai:.4f} detik (SUPER CEPAT/INSTAN!)")
        return data_di_cache
    else:
        # KONDISI: CACHE MISS [cite: 23, 24]
        print(f"    ❌ [CACHE MISS] Di Redis kosong.")
        
        # Ambil dari database utama yang lambat [cite: 23, 51, 63]
        data_asli = ambil_data_dari_database_utama(id_produk)
        
        # Salin data tersebut ke Redis dengan TTL 30 detik [cite: 23, 51, 63]
        r.set(f"produk:{id_produk}", data_asli, ex=30)
        
        waktu_selesai = time.time() - waktu_mulai
        print(f"    ✅ [SUCCESS] Data diambil dari DB dan sekarang berhasil disalin ke Redis.")
        print(f"    Total Waktu Tunggu: {waktu_selesai:.4f} detik")
        return data_asli

# --- SIMULASI UJI COBA ---
print("==================================================")
print("     DEMO CACHING SYSTEM - MAHASISWA RPL SEMESTER 6")
print("==================================================")

# Percobaan 1: Mengambil Produk P001 untuk pertama kali (Pasti LAMA)
dapatkan_produk("P001")

print("\n--- Kita coba minta data yang sama lagi dalam hitungan detik ---")

# Percobaan 2: Mengambil data yang sama (P001) untuk kedua kali (Pasti INSTAN)
dapatkan_produk("P001")