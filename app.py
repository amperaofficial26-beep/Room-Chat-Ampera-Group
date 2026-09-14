# -*- coding: utf-8 -*-
"""
Ampera Official Group — room chat resmi Ampera Official.

App Streamlit terpisah (repo sendiri).
TANPA database, TANPA Supabase, TANPA secrets: setiap pesan yang dikirim
user langsung diteruskan ke inbox email admin lewat FormSubmit
(formsubmit.co) — layanan form-to-email gratis tanpa API key.

PENTING (sekali saja, waktu pertama dipakai): kirim satu pesan tes dari
room ini, lalu buka Gmail admin dan klik link AKTIVASI dari FormSubmit.
Setelah diklik, semua pesan (termasuk yang tertahan sebelumnya) masuk
terus ke inbox.
"""

from __future__ import annotations

import html
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st

WIB = ZoneInfo("Asia/Jakarta")

st.set_page_config(
    page_title="Room Chat Ampera Official",
    page_icon="🔱",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# PENGATURAN
# ---------------------------------------------------------------------------
EMAIL_ADMIN = "saputraampera26@gmail.com"    # inbox utama tujuan pesan
EMAIL_CC = "amperaofficialgroup@gmail.com"   # dapat kopian tiap pesan
URL_ROOM = "https://room-chat-ampera-group.streamlit.app"  # alamat room ini
BATAS_PESAN = 2000                           # panjang maksimum 1 pesan
_TIMEOUT = 15


def jam_wib() -> str:
    return datetime.now(WIB).strftime("%d %b %H:%M")


def _mirip_email(teks: str) -> bool:
    """True kalau teksnya berbentuk alamat email (ada @ lalu titik)."""
    t = (teks or "").strip()
    if " " in t or "@" not in t:
        return False
    setelah = t.split("@", 1)[1]
    return "." in setelah and len(setelah) > 2


# ---------------------------------------------------------------------------
# KIRIM PESAN KE EMAIL ADMIN (FormSubmit — gratis, tanpa API key)
# ---------------------------------------------------------------------------
def kirim_ke_admin(nama: str, tag: str, kontak: str, pesan: str) -> bool:
    """Teruskan pesan user ke inbox admin. True kalau berhasil."""
    data = {
        "name": f"{nama} #{tag}",
        "Pesan": pesan,
        "Kontak": kontak or "(tidak diisi)",
        "Waktu (WIB)": jam_wib(),
        "_subject": f"💬 {nama} #{tag}: {pesan[:40]}",
        "_template": "table",
        "_captcha": "false",
        "_cc": EMAIL_CC,
    }
    # Kalau user mengisi email, jadikan Reply-To: di Gmail tinggal tekan
    # tombol "Balas" dan jawabannya langsung menuju email user tersebut.
    if _mirip_email(kontak):
        data["email"] = kontak
    try:
        r = requests.post(
            f"https://formsubmit.co/ajax/{EMAIL_ADMIN}",
            json=data,
            headers={
                "Accept": "application/json",
                # FormSubmit menolak kiriman tanpa identitas halaman web
                # (error "open this page through a web server"). Server
                # Streamlit tidak otomatis mengirim Origin/Referer, jadi
                # dikirim manual — seolah pesan dikirim dari halaman room
                # ini sendiri.
                "Origin": URL_ROOM,
                "Referer": URL_ROOM + "/",
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/126.0.0.0 Safari/537.36"),
            },
            timeout=_TIMEOUT,
        )
        ok = r.status_code == 200
        try:
            isi = r.json()
            if str(isi.get("success", "")).lower() != "true":
                ok = False
        except Exception:
            ok = False
        return ok
    except Exception:
        return False


# ---------------------------------------------------------------------------
# STATE SEDERHANA
# ---------------------------------------------------------------------------
def init_state() -> None:
    for k, v in {
        "masuk": False,
        "nama": "",
        "tag": "",
        "kontak": "",
        "pesan": [],
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# TAMPILAN
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      /* ---------- Latar: gradient warna-warni ala iOS di belakang kaca ---------- */
      .appview-container, .stApp {
        background:
          radial-gradient(900px 600px at 12% 8%,  #7C9CFF66 0%, transparent 60%),
          radial-gradient(900px 650px at 88% 15%, #FF9BD266 0%, transparent 60%),
          radial-gradient(950px 700px at 25% 92%, #7CF0D066 0%, transparent 60%),
          radial-gradient(900px 650px at 90% 88%, #FFD27C66 0%, transparent 60%),
          linear-gradient(160deg, #EDEFFB 0%, #F4EEFB 45%, #EAF6F3 100%) !important;
        background-attachment: fixed !important;
      }

      /* ---------- Header ---------- */
      .room-head { text-align:center; padding:1.2rem 0 .5rem; }
      .room-head .judul { font-family:-apple-system,"SF Pro Display",Segoe UI,sans-serif;
        font-weight:700; font-size:1.85rem; letter-spacing:.01em; margin:0;
        background:linear-gradient(93deg,#4A5AE8 10%,#B355D8 50%,#E8608F 92%);
        -webkit-background-clip:text; background-clip:text; color:transparent; }
      .room-head .sub { font-size:.72rem; letter-spacing:.28em; color:#6E7280;
        margin-top:6px; font-weight:600; }

      /* ---------- Kartu kaca dasar: dipakai container, chat bubble, expander ---------- */
      [data-testid="stVerticalBlockBorderWrapper"],
      [data-testid="stChatMessage"],
      [data-testid="stExpander"] details,
      [data-testid="stChatInput"] {
        background: rgba(255,255,255,0.38) !important;
        backdrop-filter: blur(22px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(22px) saturate(180%) !important;
        border: 1px solid rgba(255,255,255,0.55) !important;
        border-radius: 22px !important;
        box-shadow: 0 8px 28px rgba(80,60,140,0.12),
                    inset 0 1px 0 rgba(255,255,255,0.6) !important;
      }
      [data-testid="stChatMessage"] { padding:.7rem 1rem !important; }

      /* ---------- Input teks: pil kaca ---------- */
      .stTextInput input, [data-testid="stChatInput"] textarea {
        background: rgba(255,255,255,0.55) !important;
        backdrop-filter: blur(14px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(160%) !important;
        border: 1px solid rgba(255,255,255,0.7) !important;
        border-radius: 999px !important;
        color:#2E2A3D !important;
      }
      [data-testid="stChatInput"] { border-radius: 26px !important; padding:.2rem .4rem !important; }
      [data-testid="stChatInput"] textarea { border-radius: 20px !important; }

      /* ---------- Tombol: pil kaca dengan aksen gradient ---------- */
      .stButton button {
        border-radius: 999px !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        backdrop-filter: blur(14px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(160%) !important;
        font-weight:600 !important;
        transition: transform .15s ease, box-shadow .15s ease;
      }
      .stButton button:hover { transform: translateY(-1px); }
      .stButton button[kind="primary"] {
        background: linear-gradient(93deg,#5B6EF5 0%,#B355D8 55%,#E8608F 100%) !important;
        color:#fff !important; border:none !important;
        box-shadow: 0 6px 18px rgba(120,80,220,0.35) !important;
      }
      .stButton button[kind="secondary"] {
        background: rgba(255,255,255,0.45) !important; color:#3A3550 !important;
      }

      /* ---------- Elemen kecil ---------- */
      .admin-badge { display:inline-block; font-size:.66rem; font-weight:700;
        color:#5B3FA0; background:rgba(179,85,216,0.16);
        border:1px solid rgba(179,85,216,0.35);
        border-radius:999px; padding:1px 9px; margin-left:6px;
        backdrop-filter: blur(6px); }
      .jam { font-size:.66rem; color:#8A8496; }

      /* ---------- Sembunyikan chrome default agar kaca lebih menonjol ---------- */
      [data-testid="stExpander"] { border:none !important; background:transparent !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _sapaan_pembuka(nama: str) -> str:
    return (
        f"Hai {nama}! 👋 Selamat datang di Room Chat Ampera Official. "
        "Tulis pesanmu di kotak paling bawah — mau tanya-tanya produk, "
        "harga, atau langganan, semuanya langsung terkirim ke admin "
        "Ampera Official. Pesanmu di room ini cuma dilihat oleh kamu dan "
        "admin 😉"
    )


def _bubble(m: dict) -> None:
    resmi = bool(m.get("resmi"))
    label = f"**{html.escape(str(m.get('pengirim', 'Seseorang')))}**" + (
        '<span class="admin-badge">👑 RESMI</span>' if resmi else "")
    with st.chat_message("assistant" if resmi else "user",
                         avatar="🔱" if resmi else None):
        st.markdown(
            f"{label}  \n{html.escape(str(m.get('teks', '')))}  \n"
            f'<span class="jam">{html.escape(str(m.get("jam", "")))}</span>',
            unsafe_allow_html=True,
        )


def halaman_masuk() -> None:
    st.markdown(
        '<div class="room-head"><h1 class="judul">🔱 Ampera Official Group</h1>'
        '<div class="sub">ROOM CHAT RESMI AMPERA OFFICIAL</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center;color:#6F6154;font-size:.9rem;'
        'margin:1rem 0 1.4rem;">Mau tanya-tanya atau berlangganan produk '
        "Ampera Official? Masuk dengan nama panggilanmu — tanpa daftar, "
        "tanpa akun. Setiap pesanmu langsung sampai ke admin.</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        nama = st.text_input(
            "Nama panggilan kamu",
            max_chars=20,
            placeholder="misal: Budi",
            key="in_nama",
        )
        kontak = st.text_input(
            "Email / No. HP kamu (opsional)",
            max_chars=60,
            placeholder="biar admin bisa membalas kamu",
            key="in_kontak",
        )
        if st.button("Masuk Room", use_container_width=True, type="primary",
                     key="btn_masuk"):
            nama_bersih = " ".join((nama or "").split())
            if not nama_bersih:
                st.warning("Isi dulu nama panggilanmu ya.")
            elif ("ampera" in nama_bersih.lower()
                  and "official" in nama_bersih.lower()):
                st.error("Nama itu khusus admin resmi. Pilih nama lain ya.")
            else:
                st.session_state.masuk = True
                st.session_state.nama = nama_bersih
                st.session_state.tag = str(random.randint(100, 999))
                st.session_state.kontak = " ".join((kontak or "").split())
                st.session_state.pesan = [{
                    "pengirim": "Ampera Official",
                    "resmi": True,
                    "teks": _sapaan_pembuka(nama_bersih),
                    "jam": jam_wib(),
                }]
                st.rerun()


def halaman_room() -> None:
    st.markdown(
        '<div class="room-head"><h1 class="judul">🔱 Ampera Official Group</h1>'
        '<div class="sub">ROOM CHAT RESMI AMPERA OFFICIAL</div></div>',
        unsafe_allow_html=True,
    )
    c_kiri, c_kanan = st.columns([3, 1])
    with c_kiri:
        identitas = f"<b>{html.escape(st.session_state.nama)}</b>"
        if st.session_state.tag:
            identitas += (f' <span style="color:#B3A28C">'
                          f'#{st.session_state.tag}</span>')
        st.markdown(
            f'<div style="font-size:.85rem;color:#6F6154;">Masuk sebagai: '
            f"{identitas}</div>",
            unsafe_allow_html=True,
        )
    with c_kanan:
        if st.button("Keluar", use_container_width=True, key="btn_keluar"):
            for k in ("masuk", "nama", "tag", "kontak", "pesan",
                      "in_kontak_edit"):
                st.session_state.pop(k, None)
            st.rerun()

    st.caption("⚡ Setiap pesanmu langsung terkirim ke admin Ampera Official.")

    for m in st.session_state.pesan:
        _bubble(m)

    # Kontak bisa diisi / diganti kapan saja — ikut terkirim di pesan
    # berikutnya, jadi admin tahu harus membalas ke mana.
    with st.expander(
        f"✏️ Kontak balas: {st.session_state.kontak or 'belum diisi'}"
    ):
        baru = st.text_input(
            "Email / No. HP kamu",
            value=st.session_state.kontak,
            max_chars=60,
            key="in_kontak_edit",
        )
        if st.button("Simpan kontak", key="btn_simpan_kontak"):
            st.session_state.kontak = " ".join((baru or "").split())
            st.session_state.pop("in_kontak_edit", None)
            st.toast("Kontak kamu tersimpan ✅")
            st.rerun()

    teks = st.chat_input("Tulis pesan…")
    if teks and teks.strip():
        bersih = teks.strip()[:BATAS_PESAN]
        st.session_state.pesan.append({
            "pengirim": st.session_state.nama,
            "resmi": False,
            "teks": bersih,
            "jam": jam_wib(),
        })
        if kirim_ke_admin(
            st.session_state.nama,
            st.session_state.tag,
            st.session_state.kontak,
            bersih,
        ):
            st.toast("Pesan terkirim ke admin Ampera Official ✅")
        else:
            st.toast("Pesan tampil di sini, tapi gagal terkirim ke admin — "
                     "coba kirim ulang ya ⚠️")
        st.rerun()


# ---------------------------------------------------------------------------
# JALAN UTAMA
# ---------------------------------------------------------------------------
init_state()

if st.session_state.masuk:
    halaman_room()
else:
    halaman_masuk()
