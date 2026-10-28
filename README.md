# Message Spreader

Simulasi penyebaran pesan pada jaringan pernikahan keluarga Florence
abad ke-15 menggunakan BFS (Breadth-First Search).

## Dataset
Padgett Florentine Families (Netzschleuder), dikumpulkan oleh Padgett
dan Ansell. Dipakai: layer 1 (pernikahan), 16 keluarga, 20 hubungan.
Layer 2 (bisnis) tidak dipakai karena pasangan yang sama muncul di
kedua layer sehingga bisa terhitung dobel. Nama keluarga ditulis
disingkat sesuai data sumber.

## Model
- Titik: keluarga
- Sisi: hubungan pernikahan, tak berarah
- Pertanyaan: berapa putaran dan siapa saja yang menerima kabar
  dari satu pengirim awal

## Algoritma
BFS per lapisan. Putaran k berisi keluarga yang berjarak k dari
pengirim. Keluarga yang sudah menerima tidak dihitung lagi.

## Validasi
1. Tidak ada keluarga dihitung dua kali
2. Tiap penerima terhubung dari putaran sebelumnya
3. Nomor putaran sama dengan jarak terpendek (NetworkX)

## Cara menjalankan
pip install -r requirements.txt
py -3.13 -m streamlit run app.py

## Fitur
(1) Pilih pengirim dan tabel putaran
(2) Graf dengan posisi tetap, tombol Langkah berikutnya, Reset,
    warna per putaran, legenda
(3) Skenario 2: hapus satu hubungan dan bandingkan sebelum/sesudah

## Temuan
- Pucci tidak punya hubungan, jadi tidak pernah terjangkau.
- Dari Medici: 3 putaran. Dari Pazzi: 5 putaran, karena Pazzi hanya
  terhubung ke Salviati.
- Hubungan Medici-Salviati adalah jembatan: bila dihapus, Salviati
  dan Pazzi terputus. Hubungan Medici-Barbadori punya jalur cadangan.

## Keterbatasan
Model memakai satu jenis hubungan dan menganggap pesan selalu
diteruskan ke semua tetangga tanpa kegagalan.

## Struktur folder
app.py, nodes.csv, edges.csv, gprops.csv, catatan.txt,
requirements.txt, README.md, .streamlit/config.toml (tema gelap),
bukti/ (10 tangkapan layar)
Bukti tangkapan layar ada di folder bukti/ (01 sampai 10).