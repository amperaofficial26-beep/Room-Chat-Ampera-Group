# Panduan Banner Iklan — Room Chat Ampera Official

Banner iklan tampil di **halaman masuk** dan **di dalam room chat**, berganti
otomatis dengan transisi halus (crossfade). Semuanya diatur dari satu tempat:
bagian `BANNER IKLAN` di dalam `app.py` (di dekat bagian atas file).

Tidak perlu menyentuh kode lain — cukup ubah daftar `IKLAN`.

---

## 1. Menyalakan / mematikan iklan

```python
IKLAN_AKTIF = True   # True = iklan tampil, False = semua iklan disembunyikan
IKLAN_DETIK = 6      # lama satu banner tampil sebelum berganti (detik)
```

---

## 2. Menambah / mengubah banner

Satu banner = satu blok di dalam daftar `IKLAN`:

```python
IKLAN = [
    {
        "gambar": "iklan-1.jpg",
        "label": "PROMO",
        "judul": "Diskon Spesial Bulan Ini",
        "teks": "Harga khusus untuk pembelian pertama.",
        "tombol": "Klaim Promo",
        "link": "https://wa.me/6281234567890",
        "tampil": "semua",
    },
    # ...tambah blok baru di sini
]
```

Arti tiap isian:

| Isian | Keterangan |
|---|---|
| `gambar` | Nama file di folder `assets/iklan/` (contoh `"iklan-1.jpg"`) **atau** link gambar langsung (`"https://..."`). Kosongkan `""` kalau mau banner teks saja. |
| `label` | Tulisan kecil di pojok atas, misal `"PROMO"`, `"BARU"`, `"TERBATAS"`. Boleh `""`. |
| `judul` | Judul besar banner. |
| `teks` | Keterangan singkat, 1–2 baris saja biar rapi. |
| `tombol` | Tulisan pada tombol, misal `"Lihat Produk"`. Isi `""` kalau tanpa tombol. |
| `link` | Alamat tujuan saat banner diklik (buka tab baru). Isi `""` kalau banner tidak bisa diklik. |
| `tampil` | `"semua"` = di dua halaman, `"masuk"` = hanya halaman login, `"room"` = hanya di dalam room. |

Mau **menghapus** satu banner? Hapus saja satu blok `{ ... },` itu.
Kalau tinggal satu banner, slider otomatis berhenti dan banner itu tampil diam.

---

## 3. Menyiapkan gambar banner

1. Simpan gambar ke folder **`assets/iklan/`**.
2. Ukuran yang pas: **960 × 540 px** (perbandingan 16:9), format `.jpg`.
3. Usahakan di bawah ~200 KB per gambar supaya app tetap ringan.
4. Sisi **kiri** gambar akan tertutup gradasi gelap tempat judul & teks —
   jadi taruh objek utama (produk, maskot) di sisi **kanan** gambar.

Boleh juga tidak mengupload apa-apa: cukup isi `"gambar"` dengan link
gambar dari internet, misalnya link "raw" GitHub atau CDN.

---

## 4. Contoh: iklan ke WhatsApp admin

```python
{
    "gambar": "",
    "label": "HUBUNGI KAMI",
    "judul": "Konsultasi Gratis via WhatsApp",
    "teks": "Bingung pilih paket? Chat admin, dibantu sampai cocok.",
    "tombol": "Chat Admin",
    "link": "https://wa.me/6281234567890",
    "tampil": "room",
},
```

---

## 5. Catatan teknis

- Slider memakai **CSS animation murni**, bukan timer Python. Jadi banner
  berganti mulus tanpa me-refresh halaman dan tidak mengganggu chat.
- Gambar lokal otomatis diubah jadi data URI dan di-cache, jadi selalu
  terbaca walau working directory Streamlit berbeda.
- Pengguna yang mengaktifkan "reduce motion" di HP/laptopnya akan melihat
  banner pertama saja tanpa animasi (otomatis, sesuai standar aksesibilitas).

---

# Maskot "Aogi"

Maskot tampil di **tiga tempat**, semuanya bisa dinyalakan/dimatikan dari
bagian `MASKOT` di `app.py`:

```python
MASKOT_NAMA = "Aogi"
MASKOT_AVATAR = True      # wajah maskot jadi avatar bubble chat admin
MASKOT_SAMBUTAN = True    # maskot menyapa di halaman masuk
MASKOT_PEEK = True        # maskot mengintip di pojok kanan bawah room
MASKOT_SAPAAN = "Halo! Aku Aogi, temanmu di room ini. Yuk masuk 👋"
```

## File maskot (folder `assets/maskot/`)

| File | Ukuran | Dipakai untuk |
|---|---|---|
| `maskot-avatar.png` | 128×128 | Avatar bubble chat admin — **pose potret senyum** |
| `maskot-sambutan.png` | 300 px | Halaman masuk — **pose melambai** |
| `maskot-peek.png` | 220 px | Pojok kanan bawah room — **pose mengintip** |
| `maskot.png` | 520 px | Master transparan, untuk bikin ukuran lain |

Gaya gambar: **2D flat vector cartoon** (outline tegas, warna flat), bukan 3D.
Tiap halaman memakai pose yang berbeda supaya maskot terasa hidup.

Semua sudah **berlatar transparan**. Kalau mau ganti maskot, timpa file-file
di atas dengan gambar PNG transparan berukuran serupa — kode tidak perlu diubah.

## Perilaku animasi

- **Sambutan**: maskot bergoyang pelan (seperti melambai), gelembung ucapan
  muncul menyusul setelah 0,35 detik.
- **Peek**: maskot naik dari balik tepi bawah layar, mengintip sambil
  memiringkan kepala, lalu turun lagi — berulang tiap 9 detik. Tidak bisa
  diklik dan berada di belakang kolom chat, jadi tidak mengganggu tombol.
- Pengguna dengan "reduce motion" aktif melihat maskot diam tanpa animasi.
