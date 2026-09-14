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
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import base64
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

# Ganti dengan link logo AOG kamu (upload logo.png ke repo ini, lalu isi
# link "raw" GitHub-nya di sini — atau link gambar dari mana saja).
LOGO_URL = "logo.png"


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
      /* ---------- Latar: silver + charcoal terang, bergerak ---------- */
      .stApp, .appview-container, [data-testid="stAppViewContainer"] {
         background:
           radial-gradient(circle at 12% 18%, rgba(255,255,255,.34), transparent 30%),
           radial-gradient(circle at 86% 78%, rgba(255,255,255,.16), transparent 32%),
           linear-gradient(125deg, #D9DADF 0%, #AEB1B9 18%, #E7E8EB 36%, #767981 55%, #B9BBC1 72%, #4E5057 100%) !important;
         background-size: 140% 140%, 150% 150%, 400% 400% !important;
         background-position: 0% 50%, 100% 50%, 0% 50% !important;
         animation: aliranSilverCharcoal 18s ease-in-out infinite !important;
         background-attachment: fixed !important;
      }
      .stApp::before {
         content: ""; position: fixed; inset: -25%; pointer-events: none; z-index: 0;
         background: radial-gradient(circle at 25% 35%, rgba(255,255,255,.18), transparent 22%), radial-gradient(circle at 72% 60%, rgba(255,255,255,.10), transparent 24%);
         filter: blur(35px); animation: kabutCharcoal 24s ease-in-out infinite alternate;
      }
      @keyframes aliranSilverCharcoal {
         0% { background-position: 0% 45%, 100% 55%, 0% 50%; }
         50% { background-position: 100% 55%, 0% 45%, 100% 50%; }
         100% { background-position: 0% 45%, 100% 55%, 0% 50%; }
      }
      @keyframes kabutCharcoal {
         0% { transform: translate3d(-3%, -2%, 0) scale(1); }
         50% { transform: translate3d(3%, 2%, 0) scale(1.06); }
         100% { transform: translate3d(-1%, 4%, 0) scale(1.02); }
      }
      /* ---------- Logo Ampera Official ---------- */
      .logo-wrap { position:relative; width:142px; height:142px; margin:.15rem auto .8rem;
        display:flex; align-items:center; justify-content:center; overflow:hidden;
        border-radius:25px; background:rgba(255,255,255,.18);
        border:1px solid rgba(255,255,255,.68);
        box-shadow:0 12px 34px rgba(25,27,32,.18), inset 0 1px 0 rgba(255,255,255,.75);
        backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); }
      .logo-wrap img { position:relative; z-index:2; width:100%; height:100%;
        object-fit:cover; display:block; border-radius:23px;
        box-shadow:0 5px 18px rgba(20,22,26,.18); }
      /* Kilatan putih bergerak dari kiri ke kanan melewati logo */
      .logo-wrap::after { content:""; position:absolute; z-index:3; top:-20%; bottom:-20%; left:-65%; width:42%;
        transform:skewX(-20deg); pointer-events:none;
        background:linear-gradient(90deg, transparent 0%, rgba(255,255,255,0) 18%, rgba(255,255,255,.96) 50%, rgba(255,255,255,.18) 78%, transparent 100%);
        filter:blur(7px); mix-blend-mode:screen;
        animation:logoShine 3.8s cubic-bezier(.45,0,.25,1) infinite; }
      .logo-wrap::before { content:""; position:absolute; z-index:1; inset:-2px; border-radius:27px;
        box-shadow:0 0 0 1px rgba(255,255,255,.35), 0 0 22px rgba(255,255,255,.18);
        pointer-events:none; }
      @keyframes logoShine {
        0%, 18% { left:-65%; opacity:0; }
        28% { opacity:1; }
        62% { left:125%; opacity:1; }
        70%, 100% { left:125%; opacity:0; }
      }

      /* ---------- Header / teks judul — elegan, monokrom (bukan pelangi) ---------- */
      .room-head { text-align: center;padding: .3rem 0 .5rem; transform: translateX(40px); }
      .room-head .judul { font-family:Georgia,"Times New Roman",serif;
        font-weight:600; font-size:1.42rem; letter-spacing:.13em; margin:0;
        text-transform:uppercase; color:#292A30; line-height:1.2; }
      .room-head .sub { font-size:.62rem; letter-spacing:.38em; color:#85868F;
        margin-top:8px; font-weight:700; }
      .room-head .garis { width:46px; height:2px; margin:.62rem auto 0;
        border-radius:999px; background:linear-gradient(90deg,transparent,#A8AAB2,transparent); }

      /* ---------- Kartu kaca dasar ---------- */
      [data-testid="stVerticalBlockBorderWrapper"],
      [data-testid="stExpander"] details {
         background: rgba(255,255,255,0.30) !important;
         backdrop-filter: blur(22px) saturate(150%) !important;
         -webkit-backdrop-filter: blur(22px) saturate(150%) !important;
         border: 1px solid rgba(255,255,255,0.48) !important;
         border-radius: 22px !important;
         box-shadow: 0 8px 26px rgba(25,27,32,0.12), inset 0 1px 0 rgba(255,255,255,0.55) !important;
      }

      /* ---------- Chat bubble gaya WhatsApp ---------- */
      [data-testid="stChatMessage"] {
         position: relative !important; padding: .55rem .82rem !important;
         max-width: 76% !important; width: fit-content !important; min-width: 92px !important;
         margin-top: .22rem !important; margin-bottom: .22rem !important;
         border: none !important; border-radius: 14px !important;
         box-shadow: 0 3px 10px rgba(20,22,26,.14) !important;
         backdrop-filter: blur(10px) !important; -webkit-backdrop-filter: blur(10px) !important;
         transform-origin: left bottom;
         animation: bubbleIn .34s cubic-bezier(.22,.8,.24,1) both;
      }
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
         margin-right: auto !important; margin-left: 0 !important;
         background: linear-gradient(135deg, #AEB3B9, #92979E) !important; color: #FFFFFF !important;
         border-top-left-radius: 5px !important; transform-origin: left bottom;
      }
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
         margin-left: auto !important; margin-right: 0 !important; flex-direction: row-reverse !important;
         background: linear-gradient(135deg, #E5E7EA, #D2D5D9) !important; color: #202124 !important;
         border-top-right-radius: 5px !important; transform-origin: right bottom;
      }
      @keyframes bubbleIn {
         0% { opacity:0; transform:translateY(9px) scale(.94); filter:blur(2px); }
         70% { opacity:1; transform:translateY(-1px) scale(1.01); filter:blur(0); }
         100% { opacity:1; transform:translateY(0) scale(1); filter:blur(0); }
      }
      [data-testid="stChatMessage"] p { margin:.08rem 0 !important; line-height:1.48 !important; }
      [data-testid="stChatMessage"] .admin-badge { vertical-align:middle; }
      @media (prefers-reduced-motion: reduce) {
         [data-testid="stChatMessage"] { animation:none !important; }
      }
      [data-testid="stChatMessageContent"] p { margin-bottom: .12rem !important; line-height: 1.45 !important; }

      /* ---------- Input seperti composer WhatsApp ---------- */
      [data-testid="stChatInput"] {
         background: rgba(245,246,247,.88) !important;
         backdrop-filter: blur(18px) saturate(150%) !important;
         -webkit-backdrop-filter: blur(18px) saturate(150%) !important;
         border: 1px solid rgba(255,255,255,.68) !important;
         border-radius: 999px !important;
         box-shadow: 0 7px 24px rgba(25,27,32,.18) !important;
      }
      /* ---------- Kolom chat panjang berbentuk pil ---------- */
      /* ---------- Chat input: tanpa background/container tambahan ---------- */
      [data-testid="stChatInput"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
      }

      [data-testid="stChatInput"] > div {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
      }

      [data-testid="stChatInput"] textarea {
        min-height: 48px !important;
        height: 48px !important;
        flex: 1 1 auto !important;
        background: rgba(255,255,255,0.98) !important;
        backdrop-filter: blur(18px) saturate(160%) !important;
        -webkit-backdrop-filter: blur(18px) saturate(160%) !important;
        border: 1px solid rgba(255,255,255,1) !important;
        border-radius: 999px !important;
        color:#2B2B31 !important;
        padding: 12px 18px !important;
        box-shadow: 0 5px 18px rgba(25,25,35,0.14) !important;
      }

      /* Tombol kirim berada DI SAMPING kolom, bukan di dalam/bawahnya */
      [data-testid="stChatInput"] button {
        flex: 0 0 48px !important;
        width: 48px !important;
        min-width: 48px !important;
        height: 48px !important;
        margin: 0 !important;
        padding: 0 !important;
        border-radius: 50% !important;
        background: rgba(255,255,255,0.98) !important;
        border: 1px solid rgba(255,255,255,1) !important;
        box-shadow: 0 5px 18px rgba(25,25,35,0.16) !important;
      }

      [data-testid="stChatInput"] button:hover {
        transform: translateY(-1px) scale(1.03) !important;
      }

      /* Hilangkan latar putih bawaan di area kotak chat input */
      [data-testid="stBottomBlockContainer"],
      [data-testid="stBottom"] > div,
      .stChatFloatingInputContainer,
      [data-testid="stChatInputContainer"] {
        background: transparent !important;
        box-shadow: none !important;
        border: none !important;
        border-top: none !important;
      }
      [data-testid="stBottomBlockContainer"]::before,
      [data-testid="stBottom"]::before {
        background: transparent !important;
      }

      /* ---------- Tombol: pil kaca dengan aksen silver ---------- */
      .stButton button {
        border-radius: 999px !important;
        border: 1px solid rgba(255,255,255,0.7) !important;
        backdrop-filter: blur(14px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(150%) !important;
        font-weight:600 !important;
        transition: transform .15s ease, box-shadow .15s ease;
      }
      .stButton button:hover { transform: translateY(-1px); }
      .stButton button[kind="primary"] {
        background: linear-gradient(93deg,#3A3A3F 0%,#6E6E76 50%,#3A3A3F 100%) !important;
        color:#fff !important; border:none !important;
        box-shadow: 0 6px 18px rgba(30,30,40,0.28) !important;
      }
      .stButton button[kind="secondary"] {
        background: rgba(255,255,255,0.5) !important; color:#3A3A40 !important;
      }

      /* ---------- Panel kontak kecil (kiri) ---------- */
      .panel-kontak [data-testid="stExpander"] details { border-radius:18px !important; }
      .panel-kontak summary { font-size:.78rem !important; }

      /* ---------- Tombol Keluar: pojok kanan atas ---------- */
      div[data-testid="stElementContainer"]:has(.anchor-keluar)
        + div[data-testid="stElementContainer"] div[data-testid="stButton"] {
         position: fixed !important; top: 18px !important; right: 20px !important; z-index: 9999 !important;
      }
      div[data-testid="stElementContainer"]:has(.anchor-keluar)
        + div[data-testid="stElementContainer"] div[data-testid="stButton"] button {
         border-radius: 999px !important; padding: .38rem .95rem !important; min-height: 34px !important;
         background: rgba(255,255,255,.68) !important; color: #5A3030 !important;
         border: 1px solid rgba(255,255,255,.82) !important;
         box-shadow: 0 5px 18px rgba(25,27,32,.20) !important;
         backdrop-filter: blur(14px) !important; -webkit-backdrop-filter: blur(14px) !important;
      }
      div[data-testid="stElementContainer"]:has(.anchor-keluar)
        + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover {
         transform: translateY(-1px) scale(1.02); background: rgba(255,255,255,.84) !important;
      }
      @media (min-width: 700px) { .room-head { padding-right: 115px; } }
      @media (max-width: 600px) {
        .logo-wrap { width:122px; height:122px; border-radius:22px; }
        .logo-wrap img { border-radius:20px; }
        .room-head .judul { font-size:1.12rem; letter-spacing:.10em; }
        .room-head .sub { font-size:.56rem; letter-spacing:.28em; }
        [data-testid="stChatMessage"] { max-width:84% !important; }
      }
      /* ---------- Elemen kecil ---------- */
      .admin-badge { display:inline-block; font-size:.60rem; font-weight:700;
        color:#35363B; background:rgba(235,235,240,0.55);
        border:1px solid rgba(180,180,192,0.5);
        border-radius:999px; padding:1px 9px; margin-left:6px;
        backdrop-filter: blur(6px); }
      .jam { font-size:.64rem; color:#96969E; }

      [data-testid="stExpander"] { border:none !important; background:transparent !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _logo_html() -> str:
    # Embed logo sebagai data URI agar gambar lokal repo selalu terbaca,
    # termasuk saat working directory Streamlit berbeda.
    try:
        logo_path = Path(__file__).resolve().parent / LOGO_URL
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")
        logo_src = f"data:image/png;base64,{logo_b64}"
        return f'<div class="logo-wrap"><img src="{logo_src}" alt="Ampera Official Group" /></div>'
    except Exception:
        return '<div class="logo-wrap logo-fallback">AOG</div>'


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
    st.markdown(_logo_html(), unsafe_allow_html=True)
    st.markdown(
        '<div class="room-head"><h1 class="judul">Ampera Official Group</h1>'
        '<div class="sub">ROOM CHAT RESMI</div>'
        '<div class="garis"></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center;color:#6E6E76;font-size:.86rem;'
        'margin:.9rem 0 1.3rem;line-height:1.5;">Mau tanya-tanya atau '
        "berlangganan produk Ampera Official? Masuk dengan nama "
        "panggilanmu — tanpa daftar, tanpa akun. Setiap pesanmu langsung "
        "sampai ke admin.</div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '<div style="text-align:center;font-size:.72rem;'
            'letter-spacing:.18em;color:#9A9AA2;font-weight:600;'
            'margin-bottom:.6rem;">MASUK KE ROOM</div>',
            unsafe_allow_html=True,
        )
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
    st.markdown(_logo_html(), unsafe_allow_html=True)
    st.markdown(
        '<div class="room-head"><h1 class="judul">Ampera Official Group</h1>'
        '<div class="sub">ROOM CHAT RESMI</div>'
        '<div class="garis"></div></div>',
        unsafe_allow_html=True,
    )

    identitas = f"<b>{html.escape(st.session_state.nama)}</b>"
    if st.session_state.tag:
        identitas += (f' <span style="color:#A6A6AF">'
                      f'#{st.session_state.tag}</span>')
    st.markdown(
        f'<div style="text-align:center;font-size:.8rem;color:#7A7A82;'
        f'margin-bottom:.4rem;">Masuk sebagai: {identitas}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div style="text-align:center;color:#686A72;font-size:.78rem;'
        'margin:.05rem 0 .7rem;line-height:1.45;">⚡ Setiap pesanmu langsung '
        'terkirim ke admin Ampera Official.</div>',
        unsafe_allow_html=True,
    )

    # Panel kontak kecil di sisi kiri — bisa diisi / diganti kapan saja,
    # ikut terkirim di pesan berikutnya, jadi admin tahu harus membalas
    # ke mana.
    col_kontak, _ = st.columns([1.15, 1.85])
    with col_kontak:
        st.markdown('<div class="panel-kontak">', unsafe_allow_html=True)
        with st.expander("✏️ Kontak", expanded=False):
            st.caption(
                f"Saat ini: {st.session_state.kontak or 'belum diisi'}"
            )
            baru = st.text_input(
                "Email / No. HP kamu",
                value=st.session_state.kontak,
                max_chars=60,
                key="in_kontak_edit",
            )
            if st.button("Simpan", key="btn_simpan_kontak"):
                st.session_state.kontak = " ".join((baru or "").split())
                st.session_state.pop("in_kontak_edit", None)
                st.toast("Kontak kamu tersimpan ✅")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    for m in st.session_state.pesan:
        _bubble(m)

    # Tombol Keluar — mengambang di pojok kanan atas.
    st.markdown('<span class="anchor-keluar"></span>', unsafe_allow_html=True)
    if st.button("🚪 Keluar", key="btn_keluar"):
        for k in ("masuk", "nama", "tag", "kontak", "pesan",
                  "in_kontak_edit"):
            st.session_state.pop(k, None)
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
