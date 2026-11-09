# Warehouse AI Assistant

Prototype aplikasi monitoring persediaan gudang menggunakan FastAPI, Streamlit,
PostgreSQL, Docker Compose, dan Ollama (Qwen3 4B).

## 1. Arsitektur

Pada konfigurasi prototype ini:

- **Streamlit**: dashboard dan antarmuka pengguna, berjalan di Windows melalui Miniconda.
- **FastAPI**: REST API dan logika inventory, berjalan di Windows melalui Miniconda.
- **PostgreSQL**: penyimpanan data inventory, berjalan di Docker.
- **Ollama**: runtime Local LLM, berjalan di Docker.
- **Qwen3 4B**: model bahasa yang dijalankan oleh Ollama.
- **SQLAlchemy**: komunikasi Python dengan PostgreSQL.

### Alur koneksi

Karena FastAPI dan Streamlit berjalan langsung di Windows, sedangkan PostgreSQL
dan Ollama berjalan di Docker, gunakan alamat host berikut:

| Komponen tujuan | Alamat dari aplikasi Windows |
|---|---|
| FastAPI | `http://127.0.0.1:8000` |
| Streamlit | `http://localhost:8501` |
| PostgreSQL | `localhost:5432` |
| Ollama API | `http://127.0.0.1:11434` |

> Catatan: Jika nantinya Streamlit atau FastAPI juga dipindahkan ke Docker,
> koneksi antarkontainer harus menggunakan nama service Docker, misalnya
> `http://ollama:11434` dan `postgres:5432`, bukan `localhost`.

## 2. Prasyarat

- Windows 10/11 64-bit.
- Miniconda dan Python 3.11.
- Docker Desktop dengan Docker Engine berjalan.
- VS Code.
- Koneksi internet saat mengunduh image Docker dan model LLM.

Ollama tidak perlu di-install sebagai aplikasi Windows karena pada project ini
Ollama dijalankan melalui container Docker.

## 3. Struktur project

```text
Warehouse-AI-Assistant/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── inventory.py
├── frontend/
│   └── app.py
├── data/
│   └── inventory.csv
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 4. Menjalankan PostgreSQL dan Ollama dengan Docker

Pastikan Docker Desktop sudah dibuka dan status Docker Engine menunjukkan berjalan.

Buka terminal VS Code pada folder utama project, yaitu folder yang berisi
`docker-compose.yml`. Jalankan:

```powershell
docker compose up -d
```

Perintah tersebut akan mengunduh image PostgreSQL dan Ollama jika belum tersedia,
kemudian menjalankan kedua container.

Periksa container:

```powershell
docker ps
```

Pastikan container berikut berstatus `Up`:

- `warehouse-db`
- `warehouse-ollama`

Untuk melihat log:

```powershell
docker compose logs -f
```

Tekan `Ctrl+C` untuk keluar dari tampilan log. Perintah tersebut tidak
menghentikan container.

## 5. Mengunduh model Qwen3 4B ke Ollama Docker

Model perlu diunduh ke dalam container Ollama. Jalankan:

```powershell
docker exec -it warehouse-ollama ollama pull qwen3:4b
```

Periksa model yang sudah tersedia:

```powershell
docker exec -it warehouse-ollama ollama list
```

Uji model:

```powershell
docker exec -it warehouse-ollama ollama run qwen3:4b
```

Coba pertanyaan:

```text
Jelaskan fungsi safety stock dan reorder point dalam pengelolaan gudang.
Jawab dalam bahasa Indonesia.
```

Keluar dari sesi model dengan:

```text
/bye
```

Pastikan container Ollama tetap berjalan. Model disimpan pada Docker volume
`ollama_data`, sehingga tidak perlu diunduh ulang setiap container dibuat ulang
selama volume tersebut tidak dihapus.

Uji endpoint Ollama dari PowerShell Windows:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
```

Jika berhasil, endpoint akan mengembalikan daftar model yang tersedia.

## 6. Menyiapkan Python environment

Aktifkan environment Miniconda:

```powershell
conda activate warehouse-ai
```

Jika environment belum dibuat:

```powershell
conda create -n warehouse-ai python=3.11 -y
conda activate warehouse-ai
```

Install seluruh library:

```powershell
pip install -r requirements.txt
```

Jalankan perintah dari folder utama project.

## 7. Konfigurasi koneksi

### PostgreSQL

File `backend/database.py` menggunakan default connection string:

```text
postgresql+psycopg://warehouse_user:warehouse_pass@localhost:5432/warehouse_db
```

Nilai tersebut harus sesuai dengan environment PostgreSQL pada `docker-compose.yml`.
Untuk mengganti kredensial, ubah konfigurasi Compose dan connection string secara
bersamaan. Untuk deployment, gunakan environment variable atau secret, bukan
password yang ditulis langsung di kode.

### Ollama

File `frontend/app.py` menggunakan konfigurasi default:

```text
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen3:4b
```

Konfigurasi dapat diubah melalui environment variable PowerShell sebelum
menjalankan Streamlit:

```powershell
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
$env:OLLAMA_MODEL="qwen3:4b"
```

Karena Streamlit berjalan di Windows, alamat `127.0.0.1:11434` mengarah ke port
Ollama yang dipublikasikan oleh Docker.

## 8. Menjalankan backend FastAPI

Buka terminal VS Code pertama. Pastikan terminal berada di folder utama project
dan environment `warehouse-ai` aktif.

Jalankan:

```powershell
uvicorn backend.main:app --reload
```

API tersedia di:

- Root API: http://127.0.0.1:8000
- Dokumentasi interaktif: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

Saat pertama kali berjalan, tabel database dibuat otomatis dan data contoh dari
`data/inventory.csv` dimasukkan jika tabel `items` masih kosong.

## 9. Menjalankan frontend Streamlit

Buka terminal VS Code kedua. Aktifkan environment:

```powershell
conda activate warehouse-ai
```

Jalankan:

```powershell
streamlit run frontend/app.py
```

Streamlit biasanya tersedia di:

http://localhost:8501

Pastikan backend FastAPI, container PostgreSQL, dan container Ollama sedang
berjalan. Untuk fitur AI Chat, pastikan model `qwen3:4b` sudah diunduh.

## 10. Fitur prototype

1. Dashboard jumlah produk, total unit stok, low stock, out of stock, dan nilai stok.
2. Daftar barang dan status persediaan.
3. Grafik stok per barang.
4. Tambah barang baru.
5. Pencatatan transaksi barang masuk (IN) dan keluar (OUT).
6. Stock alert berdasarkan minimum stock.
7. AI chat yang menerima ringkasan data persediaan dari aplikasi dan mengirimkannya
   ke model Qwen3 melalui Ollama API.

## 11. Aturan status stok

- `OUT_OF_STOCK`: quantity = 0.
- `LOW_STOCK`: quantity lebih dari 0 dan kurang dari atau sama dengan min_stock.
- `NORMAL`: quantity lebih besar dari min_stock.

## 12. API utama

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/health` | Cek API |
| GET | `/dashboard` | Ringkasan dashboard |
| GET | `/items` | Daftar barang |
| POST | `/items` | Tambah barang |
| POST | `/transactions` | Catat barang masuk/keluar |
| GET | `/transactions` | Riwayat transaksi |

## 13. Menghentikan dan menjalankan kembali Docker

Menghentikan container tanpa menghapus data:

```powershell
docker compose down
```

Menjalankan kembali:

```powershell
docker compose up -d
```

**Jangan gunakan `docker compose down -v` jika ingin mempertahankan data.**
Opsi `-v` menghapus volume yang menyimpan database PostgreSQL dan model Ollama.

## 14. Troubleshooting

### Ollama tidak bisa diakses

Pastikan container berjalan:

```powershell
docker ps
```

Periksa log Ollama:

```powershell
docker logs warehouse-ollama
```

Tes API:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:11434/api/tags
```

### Model belum ditemukan

Unduh model di container:

```powershell
docker exec -it warehouse-ollama ollama pull qwen3:4b
```

### PostgreSQL tidak bisa diakses

Periksa container dan log:

```powershell
docker ps
docker logs warehouse-db
```

Pastikan port `5432` tidak sedang digunakan oleh layanan PostgreSQL lain.

### Port sudah digunakan

Jika port `5432` atau `11434` sudah digunakan aplikasi lain, ubah sisi kiri port
pada bagian `ports` di `docker-compose.yml`, lalu sesuaikan alamat koneksi aplikasi.

## 15. Catatan pengembangan

- CSV hanya diimpor otomatis ketika tabel `items` masih kosong.
- AI memberikan penjelasan berdasarkan snapshot data stok yang dikirim aplikasi.
- Validasi transaksi stok dilakukan oleh backend, bukan oleh LLM.
- Docker volume `warehouse_data` menyimpan database PostgreSQL.
- Docker volume `ollama_data` menyimpan model Ollama.
- Untuk penggunaan nyata, tambahkan autentikasi, pengelolaan rahasia, backup,
  audit log, migrasi database (Alembic), dan pengujian.
- Konfigurasi ini adalah prototype lokal, belum ditujukan untuk deployment publik.
