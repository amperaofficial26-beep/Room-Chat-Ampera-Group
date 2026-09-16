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
from functools import lru_cache
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import base64
import streamlit as st

WIB = ZoneInfo("Asia/Jakarta")

st.set_page_config(
    page_title="Room Chat Ampera Official",
    page_icon=":material/forum:",
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

# ---------------------------------------------------------------------------
# BANNER IKLAN  (lihat panduan lengkap di IKLAN.md)
# ---------------------------------------------------------------------------
# Banner berganti otomatis dengan transisi halus (crossfade). Cukup ubah
# daftar IKLAN di bawah ini — tidak perlu menyentuh kode lain.
#
# Satu banner = satu dict:
#   "gambar"  : nama file di folder assets/iklan/  ATAU link gambar https://
#   "label"   : tulisan kecil di pojok (mis. "PROMO", "BARU")
#   "judul"   : judul besar
#   "teks"    : keterangan singkat 1–2 baris
#   "tombol"  : tulisan pada tombol (kosongkan "" kalau tanpa tombol)
#   "link"    : alamat tujuan saat banner/tombol diklik ("" = tidak diklik)
#   "tampil"  : "semua" (default) | "masuk" (halaman login) | "room"
IKLAN_AKTIF = True        # False = semua banner disembunyikan
IKLAN_DETIK = 6           # lama satu banner tampil (detik)

IKLAN = [
    {
        "gambar": "iklan-1.jpg",
        "label": "AMPERA OFFICIAL",
        "judul": "Produk Resmi Ampera Official",
        "teks": "Semua produk dijamin original, bergaransi, dan didampingi "
                "admin resmi sampai beres.",
        "tombol": "Lihat Produk",
        "link": "https://room-chat-ampera-group.streamlit.app",
        "tampil": "semua",
    },
    {
        "gambar": "iklan-2.jpg",
        "label": "PROMO",
        "judul": "Diskon Spesial Bulan Ini",
        "teks": "Harga khusus untuk pembelian pertama. Tanya admin di room "
                "ini untuk dapat kode promonya.",
        "tombol": "Klaim Promo",
        "link": "https://room-chat-ampera-group.streamlit.app",
        "tampil": "semua",
    },
    {
        "gambar": "iklan-3.jpg",
        "label": "LANGGANAN",
        "judul": "Paket Langganan Digital",
        "teks": "Aktivasi cepat, pembayaran mudah, dan bantuan admin setiap "
                "hari kalau ada kendala.",
        "tombol": "Cek Paket",
        "link": "https://room-chat-ampera-group.streamlit.app",
        "tampil": "semua",
    },
]

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
        "_subject": f"Chat {nama} #{tag}: {pesan[:40]}",
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
      @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,300..700,0..1,-50..200');

      .material-symbols-rounded {
        font-family: 'Material Symbols Rounded';
        font-weight: normal;
        font-style: normal;
        font-size: 1.05em;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
        font-variation-settings: 'FILL' 1, 'wght' 550, 'GRAD' 0, 'opsz' 24;
        vertical-align: -0.2em;
      }
      .inline-icon { margin-right: .38rem; }

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
        backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); transform: translateX(-10px); }
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
      .room-head { text-align:center; padding:.05rem 0 .75rem; transform: translateX(55px); }
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

      /* ---------- Chat bubble lebih besar + animasi masuk ---------- */
      [data-testid="stChatMessage"] {
         position: relative !important;
         padding: .82rem 1.05rem !important;
         max-width: 86% !important;
         width: fit-content !important;
         min-width: 138px !important;
         margin-top: .34rem !important;
         margin-bottom: .34rem !important;
         border: none !important;
         border-radius: 19px !important;
         box-shadow: 0 10px 28px rgba(20,22,26,.17) !important;
         backdrop-filter: blur(13px) !important;
         -webkit-backdrop-filter: blur(13px) !important;
         font-size: .98rem !important;
         line-height: 1.55 !important;
         transform-origin: left bottom;
         animation: bubblePopLeft .48s cubic-bezier(.16,1,.3,1) both;
         will-change: transform, opacity, filter;
      }
      [data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]),
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
         margin-right: auto !important;
         margin-left: 0 !important;
         background: linear-gradient(135deg, #AEB3B9, #8D9299) !important;
         color: #FFFFFF !important;
         border-top-left-radius: 6px !important;
         transform-origin: left bottom;
         animation-name: bubblePopLeft;
      }
      [data-testid="stChatMessage"]:has([aria-label="Chat message from user"]),
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
         margin-left: auto !important;
         margin-right: 0 !important;
         flex-direction: row-reverse !important;
         background: linear-gradient(135deg, #F3F4F6, #D8DBE0) !important;
         color: #202124 !important;
         border-top-right-radius: 6px !important;
         transform-origin: right bottom;
         animation-name: bubblePopRight;
      }
      @keyframes bubblePopLeft {
         0% { opacity:0; transform:translate3d(-18px, 16px, 0) scale(.90); filter:blur(4px); }
         58% { opacity:1; transform:translate3d(2px, -2px, 0) scale(1.025); filter:blur(0); }
         100% { opacity:1; transform:translate3d(0, 0, 0) scale(1); filter:blur(0); }
      }
      @keyframes bubblePopRight {
         0% { opacity:0; transform:translate3d(18px, 16px, 0) scale(.90); filter:blur(4px); }
         58% { opacity:1; transform:translate3d(-2px, -2px, 0) scale(1.025); filter:blur(0); }
         100% { opacity:1; transform:translate3d(0, 0, 0) scale(1); filter:blur(0); }
      }
      [data-testid="stChatMessage"] p { margin:.08rem 0 !important; line-height:1.55 !important; }
      [data-testid="stChatMessage"] .admin-badge { vertical-align:middle; }
      [data-testid="stChatMessageContent"] { width: 100% !important; }
      [data-testid="stChatMessageContent"] p { margin-bottom: .12rem !important; line-height: 1.55 !important; }
      [data-testid="stChatMessageAvatarAssistant"],
      [data-testid="stChatMessageAvatarUser"],
      [data-testid="stChatMessageAvatarCustom"] { transform: scale(1.08); }
      @media (prefers-reduced-motion: reduce) {
         [data-testid="stChatMessage"] { animation:none !important; }
      }

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
        [data-testid="stChatMessage"] {
          max-width:92% !important;
          min-width:120px !important;
          padding:.76rem .92rem !important;
          margin-top:.30rem !important;
          margin-bottom:.30rem !important;
        }
      }
      /* ---------- Elemen kecil ---------- */
      .sender-name {
        display:inline-block;
        font-weight:700;
        letter-spacing:.01em;
        margin-bottom:.18rem;
      }
      .bubble-text {
        margin:.10rem 0 .22rem;
        line-height:1.56;
        word-break:break-word;
      }
      .admin-badge {
        display:inline-flex;
        align-items:center;
        gap:4px;
        font-size:.62rem;
        font-weight:800;
        color:#35363B;
        background:rgba(235,235,240,0.64);
        border:1px solid rgba(180,180,192,0.54);
        border-radius:999px;
        padding:3px 10px;
        margin-left:7px;
        backdrop-filter: blur(6px);
      }
      .admin-badge .material-symbols-rounded { font-size:.85rem; }
      .jam {
        display:inline-flex;
        align-items:center;
        gap:4px;
        font-size:.68rem;
        color:#8C8D96;
      }
      .jam .material-symbols-rounded { font-size:.84rem; font-variation-settings:'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 20; }

      [data-testid="stExpander"] { border:none !important; background:transparent !important; }

      /* ---------- Banner iklan (slider crossfade) ---------- */
      .iklan-box {
        position:relative; width:100%; margin:.35rem 0 1.05rem;
        aspect-ratio: 16 / 6.2; min-height:150px;
        border-radius:22px; overflow:hidden; isolation:isolate;
        border:1px solid rgba(255,255,255,.55);
        box-shadow:0 12px 32px rgba(25,27,32,.20), inset 0 1px 0 rgba(255,255,255,.45);
        background:rgba(255,255,255,.28);
        backdrop-filter:blur(16px); -webkit-backdrop-filter:blur(16px);
      }
      .iklan-slide {
        position:absolute; inset:0; opacity:0;
        display:flex; align-items:flex-end;
        text-decoration:none !important; color:#fff !important;
        animation-timing-function: cubic-bezier(.4,0,.2,1);
        animation-iteration-count: infinite;
        animation-fill-mode: backwards;
        will-change: opacity, transform;
      }
      .iklan-slide.tunggal { opacity:1; animation:none !important; }
      .iklan-slide img {
        position:absolute; inset:0; width:100%; height:100%;
        object-fit:cover; z-index:0; transform:scale(1.03);
        animation: iklanZoom 14s ease-in-out infinite alternate;
      }
      .iklan-slide::after {
        content:""; position:absolute; inset:0; z-index:1;
        background:linear-gradient(100deg, rgba(18,19,23,.90) 0%, rgba(18,19,23,.72) 42%, rgba(18,19,23,.20) 78%, rgba(18,19,23,.05) 100%);
      }
      .iklan-isi { position:relative; z-index:2; padding:.95rem 1.15rem; max-width:82%; }
      .iklan-label {
        display:inline-block; font-size:.56rem; font-weight:800; letter-spacing:.22em;
        text-transform:uppercase; color:#EDEEF2;
        background:rgba(255,255,255,.17); border:1px solid rgba(255,255,255,.34);
        border-radius:999px; padding:3px 10px; margin-bottom:.42rem;
        backdrop-filter:blur(6px);
      }
      .iklan-judul {
        font-family:Georgia,"Times New Roman",serif; font-weight:600;
        font-size:1.06rem; line-height:1.25; margin:0 0 .22rem; color:#FFFFFF;
        text-shadow:0 2px 10px rgba(0,0,0,.35);
      }
      .iklan-teks {
        font-size:.76rem; line-height:1.45; color:rgba(255,255,255,.86);
        margin:0 0 .58rem;
      }
      .iklan-tombol {
        display:inline-flex; align-items:center; gap:5px;
        font-size:.72rem; font-weight:700; letter-spacing:.02em; color:#26272C;
        background:linear-gradient(135deg,#FFFFFF,#DDDFE4);
        border-radius:999px; padding:6px 15px;
        box-shadow:0 6px 18px rgba(0,0,0,.28);
        transition:transform .15s ease, box-shadow .15s ease;
      }
      .iklan-slide:hover .iklan-tombol { transform:translateY(-1px); box-shadow:0 8px 22px rgba(0,0,0,.34); }
      .iklan-tombol .material-symbols-rounded { font-size:.9rem; }
      .iklan-dots {
        position:absolute; z-index:3; right:12px; bottom:11px;
        display:flex; gap:6px;
      }
      .iklan-dot {
        width:6px; height:6px; border-radius:999px;
        background:rgba(255,255,255,.34);
        animation-timing-function: linear; animation-iteration-count: infinite;
        animation-fill-mode: backwards;
      }
      .iklan-dot.tunggal { background:rgba(255,255,255,.85); animation:none !important; }
      @keyframes iklanZoom { from { transform:scale(1.03); } to { transform:scale(1.11); } }
      @media (max-width:600px) {
        .iklan-box { aspect-ratio: 16 / 8.4; min-height:158px; border-radius:18px; }
        .iklan-isi { padding:.8rem .9rem; max-width:94%; }
        .iklan-judul { font-size:.95rem; }
        .iklan-teks { font-size:.72rem; }
      }
      @media (prefers-reduced-motion: reduce) {
        .iklan-slide, .iklan-slide img, .iklan-dot { animation:none !important; }
        .iklan-slide:first-of-type { opacity:1 !important; }
      }
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


# ---------------------------------------------------------------------------
# BANNER IKLAN — slider crossfade murni CSS (tidak perlu rerun/refresh)
# ---------------------------------------------------------------------------
_FADE = 0.9  # lama transisi crossfade antar banner (detik)


@lru_cache(maxsize=32)
def _sumber_gambar(nama_file: str) -> str:
    """Kembalikan src gambar: link https dipakai apa adanya, file lokal
    di folder assets/iklan/ diubah jadi data URI supaya selalu terbaca."""
    n = (nama_file or "").strip()
    if not n:
        return ""
    if n.startswith(("http://", "https://", "data:")):
        return n
    for kandidat in (
        Path(__file__).resolve().parent / "assets" / "iklan" / n,
        Path(__file__).resolve().parent / n,
    ):
        try:
            data = kandidat.read_bytes()
        except Exception:
            continue
        jenis = "jpeg" if kandidat.suffix.lower() in (".jpg", ".jpeg") else \
                kandidat.suffix.lower().lstrip(".") or "png"
        return f"data:image/{jenis};base64," + base64.b64encode(data).decode()
    return ""


def _keyframes_iklan(n: int, durasi: float) -> str:
    """Bikin @keyframes untuk tiap slide + titik indikatornya."""
    total = n * durasi
    f = min(_FADE, durasi / 2)
    p_in = f / total * 100          # selesai fade-in
    p_hold = durasi / total * 100   # mulai fade-out
    p_out = (durasi + f) / total * 100
    p_balik = (total - f) / total * 100
    css = [
        "@keyframes iklanFade {"
        f" 0%,{p_hold:.3f}% {{ opacity:1; }}"
        f" {p_out:.3f}%,{p_balik:.3f}% {{ opacity:0; }}"
        " 100% { opacity:1; } }",
        "@keyframes iklanDot {"
        f" 0%,{p_hold:.3f}% {{ background:rgba(255,255,255,.90); }}"
        f" {p_out:.3f}%,{p_balik:.3f}% {{ background:rgba(255,255,255,.30); }}"
        " 100% { background:rgba(255,255,255,.90); } }",
    ]
    _ = p_in
    return "".join(css)


@lru_cache(maxsize=4)
def _iklan_html(area: str) -> str:
    """HTML banner iklan untuk area tertentu: 'masuk' atau 'room'."""
    if not IKLAN_AKTIF:
        return ""
    daftar = [
        b for b in IKLAN
        if str(b.get("tampil", "semua")).lower() in ("semua", area)
    ]
    slide, dots = [], []
    n = len(daftar)
    if n == 0:
        return ""
    durasi = max(2.0, float(IKLAN_DETIK))
    total = n * durasi

    for i, b in enumerate(daftar):
        src = _sumber_gambar(str(b.get("gambar", "")))
        judul = html.escape(str(b.get("judul", "")))
        teks = html.escape(str(b.get("teks", "")))
        label = html.escape(str(b.get("label", "")))
        tombol = html.escape(str(b.get("tombol", "")))
        link = str(b.get("link", "")).strip()

        # Waktu mulai tiap slide diatur lewat animation-delay negatif,
        # supaya slide pertama sudah tampil penuh sejak detik ke-0 dan
        # tidak ada dua banner yang tumpuk saat halaman baru dibuka.
        delay = i * durasi - total - min(_FADE, durasi / 2)
        gaya_slide = ("" if n == 1 else
                      f"animation-name:iklanFade;animation-duration:{total:g}s;"
                      f"animation-delay:{delay:g}s;")
        gaya_dot = ("" if n == 1 else
                    f"animation-name:iklanDot;animation-duration:{total:g}s;"
                    f"animation-delay:{delay:g}s;")

        isi = []
        if label:
            isi.append(f'<span class="iklan-label">{label}</span>')
        if judul:
            isi.append(f'<div class="iklan-judul">{judul}</div>')
        if teks:
            isi.append(f'<div class="iklan-teks">{teks}</div>')
        if tombol:
            isi.append(
                '<span class="iklan-tombol">' + tombol +
                '<span class="material-symbols-rounded" aria-hidden="true">'
                'arrow_forward</span></span>'
            )
        gambar = (f'<img src="{src}" alt="{judul or "Iklan"}" loading="lazy" />'
                  if src else "")
        badan = (f'{gambar}<div class="iklan-isi">{"".join(isi)}</div>')
        kelas = "iklan-slide" + (" tunggal" if n == 1 else "")

        if link.startswith(("http://", "https://")):
            slide.append(
                f'<a class="{kelas}" style="{gaya_slide}" href="{html.escape(link)}" '
                f'target="_blank" rel="noopener noreferrer">{badan}</a>'
            )
        else:
            slide.append(f'<div class="{kelas}" style="{gaya_slide}">{badan}</div>')
        dots.append(
            f'<span class="iklan-dot{" tunggal" if n == 1 else ""}" '
            f'style="{gaya_dot}"></span>'
        )

    gaya = f"<style>{_keyframes_iklan(n, durasi)}</style>" if n > 1 else ""
    return (
        gaya
        + '<div class="iklan-box" role="complementary" aria-label="Iklan">'
        + "".join(slide)
        + f'<div class="iklan-dots">{"".join(dots)}</div>'
        + "</div>"
    )


def tampilkan_iklan(area: str) -> None:
    kode = _iklan_html(area)
    if kode:
        st.markdown(kode, unsafe_allow_html=True)


def _sapaan_pembuka(nama: str) -> str:
    return (
        f"Hai {nama}! Selamat datang di Room Chat Ampera Official. "
        "Tulis pesanmu di kotak paling bawah — mau tanya-tanya produk, "
        "harga, atau langganan, semuanya langsung terkirim ke admin "
        "Ampera Official. Pesanmu di room ini cuma dilihat oleh kamu dan "
        "admin."
    )


def _bubble(m: dict) -> None:
    resmi = bool(m.get("resmi"))
    pengirim = html.escape(str(m.get("pengirim", "Seseorang")))
    teks = html.escape(str(m.get("teks", ""))).replace("\n", "<br>")
    jam = html.escape(str(m.get("jam", "")))
    label = f'<span class="sender-name">{pengirim}</span>'
    if resmi:
        label += (
            '<span class="admin-badge">'
            '<span class="material-symbols-rounded" aria-hidden="true">verified</span>'
            'RESMI</span>'
        )
    avatar = ":material/verified_user:" if resmi else ":material/person:"
    with st.chat_message("assistant" if resmi else "user", avatar=avatar):
        st.markdown(
            f"{label}"
            f'<div class="bubble-text">{teks}</div>'
            '<span class="jam">'
            '<span class="material-symbols-rounded" aria-hidden="true">schedule</span>'
            f"{jam}</span>",
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

    tampilkan_iklan("masuk")

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
        if st.button(":material/login: Masuk Room", use_container_width=True, type="primary",
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
        'margin:.05rem 0 .7rem;line-height:1.45;">'
        '<span class="material-symbols-rounded inline-icon" aria-hidden="true">bolt</span>'
        'Setiap pesanmu langsung terkirim ke admin Ampera Official.</div>',
        unsafe_allow_html=True,
    )

    tampilkan_iklan("room")

    # Panel kontak kecil di sisi kiri — bisa diisi / diganti kapan saja,
    # ikut terkirim di pesan berikutnya, jadi admin tahu harus membalas
    # ke mana.
    col_kontak, _ = st.columns([1.15, 1.85])
    with col_kontak:
        st.markdown('<div class="panel-kontak">', unsafe_allow_html=True)
        with st.expander(":material/edit: Kontak", expanded=False):
            st.caption(
                f"Saat ini: {st.session_state.kontak or 'belum diisi'}"
            )
            baru = st.text_input(
                "Email / No. HP kamu",
                value=st.session_state.kontak,
                max_chars=60,
                key="in_kontak_edit",
            )
            if st.button(":material/save: Simpan", key="btn_simpan_kontak"):
                st.session_state.kontak = " ".join((baru or "").split())
                st.session_state.pop("in_kontak_edit", None)
                st.toast("Kontak kamu tersimpan", icon=":material/check_circle:")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    for m in st.session_state.pesan:
        _bubble(m)

    # Tombol Keluar — mengambang di pojok kanan atas.
    st.markdown('<span class="anchor-keluar"></span>', unsafe_allow_html=True)
    if st.button(":material/logout: Keluar", key="btn_keluar"):
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
            st.toast("Pesan terkirim ke admin Ampera Official", icon=":material/check_circle:")
        else:
            st.toast(
                "Pesan tampil di sini, tapi gagal terkirim ke admin — "
                "coba kirim ulang ya",
                icon=":material/error:",
            )
        st.rerun()


# ---------------------------------------------------------------------------
# JALAN UTAMA
# ---------------------------------------------------------------------------
init_state()

if st.session_state.masuk:
    halaman_room()
else:
    halaman_masuk()
