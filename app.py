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
        "_subject": f"Pesan Room Chat — {nama} #{tag}: {pesan[:40]}",
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
      .logo-wrap { position:relative; width:150px; height:150px; margin:.15rem auto .35rem;
        transform:translateX(-10px);
        display:flex; align-items:center; justify-content:center; overflow:hidden;
        border-radius:24px; background:rgba(255,255,255,.20);
        border:1px solid rgba(255,255,255,.58);
        box-shadow:0 10px 30px rgba(25,27,32,.16), inset 0 1px 0 rgba(255,255,255,.65);
        backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px); }
      .logo-wrap::before {
        content:""; position:absolute; top:-18%; bottom:-18%; left:-48%; width:42%; z-index:3; pointer-events:none;
        background:linear-gradient(90deg, transparent 0%, rgba(255,255,255,.12) 22%, rgba(255,255,255,.78) 50%, rgba(255,255,255,.12) 78%, transparent 100%);
        filter:blur(8px); opacity:.42; transform:skewX(-14deg) translateX(0);
        mix-blend-mode:screen; will-change:transform,opacity;
        animation:glowBerjalan 5.8s cubic-bezier(.45,0,.55,1) infinite;
      }
      .logo-wrap img { position:relative; z-index:2; width:100%; height:100%;
        object-fit:cover; display:block; border-radius:22px;
        box-shadow:0 5px 18px rgba(20,22,26,.18); }
      .logo-fallback { font-family:Georgia,serif; font-size:2.2rem; font-weight:700; color:#2B2B31; }
      @keyframes glowBerjalan {
        0%, 18% { transform:skewX(-14deg) translateX(0); opacity:0; }
        30% { opacity:.20; }
        50% { opacity:.46; }
        70% { opacity:.20; }
        82%, 100% { transform:skewX(-14deg) translateX(390%); opacity:0; }
      }

      /* ---------- Header / teks judul — elegan, monokrom (bukan pelangi) ---------- */
      .room-head { text-align:center; padding:.3rem 0 .5rem; transform:translateX(55px); }
      .room-head .judul { font-family:Georgia,"Times New Roman",serif;
        font-weight:600; font-size:1.55rem; letter-spacing:.16em; margin:0;
        text-transform:uppercase; color:#2B2B31; }
      .room-head .sub { font-size:.68rem; letter-spacing:.32em; color:#8A8A93;
        margin-top:7px; font-weight:600; }
      .room-head .garis { width:38px; height:1px; margin:.55rem auto 0;
        background:linear-gradient(90deg,transparent,#B9B9C2,transparent); }

      /* ---------- Kartu kaca dasar ---------- */
      [data-testid="stVerticalBlockBorderWrapper"],
      [data-testid="stExpander"] details {
         background: rgba(255,255,255,0.34) !important;
         backdrop-filter: blur(22px) saturate(150%) !important;
         -webkit-backdrop-filter: blur(22px) saturate(150%) !important;
         border: 1px solid rgba(255,255,255,0.48) !important;
         border-radius: 22px !important;
         box-shadow: 0 8px 26px rgba(25,27,32,0.12), inset 0 1px 0 rgba(255,255,255,0.55) !important;
      }

        /* =========================================================
           CHAT BUBBLE — FIX POSISI KIRI / KANAN
           ========================================================= */
        
        /* CONTAINER INDUK CHAT HARUS FULL WIDTH */
        div:has(> [data-testid="stChatMessage"]) {
            width: 100% !important;
            display: flex !important;
            flex-direction: column !important;
        }
        
        
        /* ---------- BUBBLE DASAR ---------- */
        
        [data-testid="stChatMessage"] {
            position: relative !important;
        
            width: fit-content !important;
            max-width: 86% !important;
            min-width: 120px !important;
        
            margin-top: .24rem !important;
            margin-bottom: .24rem !important;
        
            border: none !important;
            border-radius: 14px !important;
        
            box-shadow: 0 3px 10px rgba(20,22,26,.14) !important;
        
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
        
            animation: bubbleIn .34s cubic-bezier(.22,.8,.24,1) both;
        }
        
        
        /* =========================================================
           ADMIN → KIRI
           ========================================================= */
        
        div:has(> [data-testid="stChatMessage"])
        [data-testid="stChatMessage"]:has(
            [data-testid="stChatMessageAvatarAssistant"]
        ) {
            align-self: flex-start !important;
        
            margin-left: 0 !important;
            margin-right: auto !important;
        
            background: linear-gradient(
                135deg,
                #AEB3B9,
                #92979E
            ) !important;
        
            color: #FFFFFF !important;
        
            border-top-left-radius: 5px !important;
        
            transform-origin: left bottom;
        }
        
        
        /* =========================================================
           USER → KANAN
           ========================================================= */
        
        div:has(> [data-testid="stChatMessage"])
        [data-testid="stChatMessage"]:has(
            [data-testid="stChatMessageAvatarUser"]
        ) {
            align-self: flex-end !important;
        
            margin-left: auto !important;
            margin-right: 0 !important;
        
            background: linear-gradient(
                135deg,
                #E5E7EA,
                #D2D5D9
            ) !important;
        
            color: #202124 !important;
        
            border-top-right-radius: 5px !important;
        
            transform-origin: right bottom;
        }
        
        
        /* ---------- USER AVATAR ---------- */
        
        [data-testid="stChatMessage"]:has(
            [data-testid="stChatMessageAvatarUser"]
        )
        [data-testid="stChatMessageAvatarUser"] {
            margin-left: 8px !important;
            margin-right: 0 !important;
        }
        
        
        /* ---------- ISI BUBBLE ---------- */
        
        [data-testid="stChatMessageContent"] {
            text-align: left !important;
        }
        
        
        /* ---------- PARAGRAF ---------- */
        
        [data-testid="stChatMessageContent"] p {
            margin-bottom: .12rem !important;
            line-height: 1.45 !important;
        }
      
       @keyframes userGlow {
         0%, 18% { background-position: 130% 50%; opacity: 0; }
         38% { opacity: .22; }
         55% { background-position: 0% 50%; opacity: .42; }
         72% { opacity: .18; }
         88%, 100% { background-position: -30% 50%; opacity: 0; }
      }

      @keyframes bubbleIn {
         0% { opacity:0; transform:translateY(9px) scale(.94); filter:blur(2px); }
         65% { opacity:1; transform:translateY(-1px) scale(1.01); filter:blur(0); }
         100% { opacity:1; transform:translateY(0) scale(1); filter:blur(0); }
      }

      @media (prefers-reduced-motion: reduce) {
         [data-testid="stChatMessage"] { animation:none !important; }
         [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])::after { animation:none !important; }
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
      @media (max-width: 699px) {
        .logo-wrap { transform:translateX(-10px) scale(.90); }
        .room-head { transform:translateX(0); }
        .room-head .judul { font-size:1.18rem; letter-spacing:.10em; }
      }
      /* ---------- Elemen kecil ---------- */
      .admin-badge { display:inline-block; font-size:.64rem; font-weight:700;
        color:#3A3A40; background:rgba(200,200,210,0.35);
        border:1px solid rgba(180,180,192,0.5);
        border-radius:999px; padding:1px 9px; margin-left:6px;
        backdrop-filter: blur(6px); }
      .jam { font-size:.64rem; color:#96969E; }

      [data-testid="stExpander"] { border:none !important; background:transparent !important; }

      /* ==================================================================
         OVERRIDE CHAT USER — paksa bubble USER ke kanan
         ================================================================== */
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
         display: flex !important;
         flex-direction: row !important;
         align-self: flex-end !important;
         float: none !important;
         clear: none !important;

         /* Lebih lebar + dorong penuh ke sisi kanan */
         width: 88% !important;
         max-width: 88% !important;
         min-width: 0 !important;
         margin-left: auto !important;
         margin-right: 0 !important;

         position: relative !important;
         left: auto !important;
         right: auto !important;
         box-sizing: border-box !important;
         overflow: hidden !important;

         border-radius: 16px !important;
         border-top-right-radius: 5px !important;
         background: linear-gradient(135deg, #F0F1F3 0%, #D8DBE0 52%, #C9CDD2 100%) !important;
         color: #202124 !important;
         box-shadow: 0 5px 18px rgba(20,22,26,.15),
                     inset 0 1px 0 rgba(255,255,255,.72) !important;
         transform-origin: right bottom !important;
         animation: bubbleInRight .42s cubic-bezier(.22,.78,.22,1) both !important;
      }

      /* Cahaya/glow halus yang bergerak di bubble user */
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])::after {
         content: "" !important;
         position: absolute !important;
         top: -35% !important;
         bottom: -35% !important;
         left: -42% !important;
         width: 28% !important;
         pointer-events: none !important;
         z-index: 0 !important;
         background: linear-gradient(90deg, transparent, rgba(255,255,255,.52), transparent) !important;
         filter: blur(9px) !important;
         opacity: 0 !important;
         transform: skewX(-14deg) translateX(0) !important;
         animation: userBubbleGlow 6.5s cubic-bezier(.45,0,.55,1) infinite !important;
      }

      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
      [data-testid="stChatMessageContent"] {
         position: relative !important;
         z-index: 1 !important;
      }

      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
      [data-testid="stChatMessageAvatarUser"] {
         order: 2 !important;
         flex: 0 0 auto !important;
         margin-left: 10px !important;
         margin-right: 0 !important;
      }

      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
      [data-testid="stChatMessageContent"] {
         order: 1 !important;
         min-width: 0 !important;
         text-align: left !important;
      }

      @keyframes bubbleInRight {
         0% { opacity: 0; transform: translate3d(18px, 10px, 0) scale(.94); filter: blur(2px); }
         65% { opacity: 1; transform: translate3d(-2px, -1px, 0) scale(1.005); filter: blur(0); }
         100% { opacity: 1; transform: translate3d(0, 0, 0) scale(1); filter: blur(0); }
      }

      @keyframes userBubbleGlow {
         0%, 18% { transform: skewX(-14deg) translateX(0); opacity: 0; }
         30% { opacity: .10; }
         48% { opacity: .30; }
         66% { opacity: .10; }
         82%, 100% { transform: skewX(-14deg) translateX(520%); opacity: 0; }
      }

      @media (prefers-reduced-motion: reduce) {
         [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
            animation: none !important;
         }
         [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])::after {
            animation: none !important;
         }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def _logo_path() -> str:
    return str((Path(__file__).resolve().parent / LOGO_URL).resolve())


def _logo_html() -> str:
    # Embed logo sebagai data URI agar gambar lokal repository tetap tampil.
    try:
        with open(_logo_path(), "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode("utf-8")
        logo_src = f"data:image/png;base64,{logo_b64}"
        return f'<div class="logo-wrap"><img src="{logo_src}" alt="Ampera Official Group" /></div>'
    except Exception:
        return '<div class="logo-wrap logo-fallback">AOG</div>'


def _sapaan_pembuka(nama: str) -> str:
    return (
        f"Hai {nama}! :material/waving_hand: Selamat datang di Room Chat Ampera Official. "
        "Tulis pesanmu di kotak paling bawah — mau tanya-tanya produk, "
        "harga, atau langganan, semuanya langsung terkirim ke admin "
        "Ampera Official. Pesanmu di room ini cuma dilihat oleh kamu dan "
        "admin :material/sentiment_satisfied:."
    )


def _bubble(m: dict) -> None:
    resmi = bool(m.get("resmi"))
    label = f"**{html.escape(str(m.get('pengirim', 'Seseorang')))}**" + (
        " :material/verified: **RESMI**" if resmi else "")

    # Admin memakai logo AOG sebagai avatar; user memakai Material Icon person.
    avatar = _logo_path() if resmi else ":material/person:"
    with st.chat_message("assistant" if resmi else "user", avatar=avatar):
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
                st.warning("Isi dulu nama panggilanmu.")
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
    st.caption(":material/bolt: Setiap pesanmu langsung terkirim ke admin Ampera Official.")

    # Panel kontak kecil di sisi kiri — bisa diisi / diganti kapan saja,
    # ikut terkirim di pesan berikutnya, jadi admin tahu harus membalas
    # ke mana.
    col_kontak, _ = st.columns([1, 2])
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
            if st.button("Simpan", key="btn_simpan_kontak"):
                st.session_state.kontak = " ".join((baru or "").split())
                st.session_state.pop("in_kontak_edit", None)
                st.toast(":material/check_circle: Kontak kamu tersimpan")
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
            st.toast(":material/check_circle: Pesan terkirim ke admin Ampera Official")
        else:
            st.toast(":material/warning: Pesan tampil di sini, tapi gagal terkirim ke admin — "
                     "coba kirim ulang ya")
        st.rerun()


# ---------------------------------------------------------------------------
# JALAN UTAMA
# ---------------------------------------------------------------------------
init_state()

if st.session_state.masuk:
    halaman_room()
else:
    halaman_masuk()
