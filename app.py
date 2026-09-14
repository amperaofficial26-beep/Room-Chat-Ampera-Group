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

ASET GAMBAR: taruh 4 file ini di folder yang sama dengan app.py (root
repo) — logo.png, maskot-masuk.png, maskot-kirim.png, maskot-keluar.png.
Kalau belum ada, app tetap jalan normal (otomatis pakai ikon pengganti).
"""

from __future__ import annotations

import html
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st

WIB = ZoneInfo("Asia/Jakarta")

# ---------------------------------------------------------------------------
# PENGATURAN
# ---------------------------------------------------------------------------
EMAIL_ADMIN = "saputraampera26@gmail.com"    # inbox utama tujuan pesan
EMAIL_CC = "amperaofficialgroup@gmail.com"   # dapat kopian tiap pesan
URL_ROOM = "https://room-chat-ampera-group.streamlit.app"  # alamat room ini
BATAS_PESAN = 2000                           # panjang maksimum 1 pesan
_TIMEOUT = 15

# Aset gambar (taruh di root repo, sejajar dengan app.py)
LOGO_URL = "logo.png"
MASCOT_MASUK = "maskot-masuk.png"     # tampil di halaman login
MASCOT_KIRIM = "maskot-kirim.png"     # tampil sesaat setelah pesan terkirim
MASCOT_KELUAR = "maskot-keluar.png"   # tampil sesaat setelah tekan Keluar

_LOGO_ADA = os.path.exists(LOGO_URL)

st.set_page_config(
    page_title="Room Chat Ampera Official",
    page_icon=(LOGO_URL if _LOGO_ADA else None),
    layout="centered",
    initial_sidebar_state="collapsed",
)


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
        "_subject": f"Pesan baru dari {nama} #{tag}: {pesan[:40]}",
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
        "anim_kirim": False,
        "anim_keluar": False,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ---------------------------------------------------------------------------
# TAMPILAN — CSS: charcoal & silver, kaca, tanpa emoji, glow, maskot
# ---------------------------------------------------------------------------
st.markdown(
    '<link rel="stylesheet" '
    'href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:'
    'opsz,wght,FILL,GRAD@20,500,1,0&display=swap">',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <style>
      .material-symbols-outlined {
        font-family:'Material Symbols Outlined'; font-weight:normal;
        font-style:normal; line-height:1; letter-spacing:normal;
        text-transform:none; white-space:nowrap; word-wrap:normal;
        direction:ltr; vertical-align:middle; font-size:1.05em;
        -webkit-font-smoothing:antialiased;
      }

      /* ---------- Latar: charcoal & silver, mengalir pelan ---------- */
      .appview-container, .stApp {
        background: linear-gradient(120deg,
          #131315 0%, #232326 22%, #3D3D42 42%,
          #7A7A82 52%, #3D3D42 62%, #232326 82%, #131315 100%) !important;
        background-size: 320% 320% !important;
        animation: aliranCharcoal 24s ease-in-out infinite !important;
        background-attachment: fixed !important;
      }
      @keyframes aliranCharcoal {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
      .stApp, .stApp p, .stApp span, .stApp label, .stMarkdown { color:#ECECEF; }
      .stApp [data-testid="stCaptionContainer"] { color:#A6A6AE !important; }

      /* ---------- Logo + glow berjalan ---------- */
      .logo-wrap { position:relative; width:84px; height:84px; margin:.1rem auto .25rem;
        display:flex; align-items:center; justify-content:center; }
      .logo-wrap::before {
        content:""; position:absolute; inset:-6px; border-radius:50%;
        background: conic-gradient(from 0deg,
          transparent 0deg, #FFFFFF 35deg, #C9A227 70deg, transparent 110deg,
          transparent 250deg, #C9A227 300deg, #FFFFFF 330deg, transparent 360deg);
        filter: blur(6px);
        animation: putarGlow 5s linear infinite;
      }
      .logo-wrap::after {
        content:""; position:absolute; inset:-1px; border-radius:50%;
        background: rgba(255,255,255,0.06);
        backdrop-filter: blur(6px);
        border: 1px solid rgba(255,255,255,0.22);
      }
      .logo-wrap img { position:relative; z-index:2; width:68px; height:68px;
        border-radius:50%; object-fit:cover;
        box-shadow: 0 4px 16px rgba(0,0,0,0.45); background:#111; }
      @keyframes putarGlow { to { transform: rotate(360deg); } }

      /* ---------- Maskot ---------- */
      .mascot-idle { display:block; width:92px; margin:0 auto .2rem;
        animation: mascotFloat 3.2s ease-in-out infinite;
        filter: drop-shadow(0 10px 14px rgba(0,0,0,0.45)); }
      @keyframes mascotFloat {
        0%,100% { transform: translateY(0); }
        50%     { transform: translateY(-8px); }
      }
      .mascot-toast, .mascot-exit {
        position: fixed; left:50%; z-index:1000; text-align:center;
        pointer-events:none;
        animation: mascotPopFade 2.3s ease forwards;
      }
      .mascot-toast { bottom: 104px; }
      .mascot-exit  { top: 16%; }
      .mascot-toast img, .mascot-exit img { width:78px;
        filter: drop-shadow(0 8px 14px rgba(0,0,0,0.5)); }
      .mascot-toast span, .mascot-exit span { display:inline-block; margin-top:2px;
        font-size:.72rem; color:#ECECEF; background:rgba(20,20,22,0.65);
        padding:2px 11px; border-radius:999px; backdrop-filter:blur(8px);
        border:1px solid rgba(255,255,255,0.14); }
      @keyframes mascotPopFade {
        0%   { opacity:0; transform: translate(-50%,12px) scale(.85); }
        14%  { opacity:1; transform: translate(-50%,0) scale(1); }
        78%  { opacity:1; transform: translate(-50%,0) scale(1); }
        100% { opacity:0; transform: translate(-50%,-8px) scale(.94); }
      }

      /* ---------- Header / teks resmi — elegan + kilau putih berjalan ---------- */
      .room-head { text-align:center; padding:.25rem 0 .45rem; }
      .room-head .judul { font-family:Georgia,"Times New Roman",serif;
        font-weight:600; font-size:1.42rem; letter-spacing:.14em; margin:0;
        text-transform:uppercase;
        background: linear-gradient(100deg, #B9B9C2 30%, #FFFFFF 50%, #B9B9C2 70%);
        background-size: 240% auto;
        -webkit-background-clip:text; background-clip:text; color:transparent;
        animation: kilauJudul 3.6s linear infinite;
      }
      @keyframes kilauJudul { to { background-position: -240% center; } }
      .room-head .sub { font-size:.64rem; letter-spacing:.3em; color:#9C9CA6;
        margin-top:5px; font-weight:600; }
      .room-head .garis { width:34px; height:1px; margin:.5rem auto 0;
        background:linear-gradient(90deg,transparent,#8E8E96,transparent); }

      /* ---------- Kartu kaca dasar ---------- */
      [data-testid="stVerticalBlockBorderWrapper"],
      [data-testid="stExpander"] details,
      [data-testid="stChatInput"] {
        background: rgba(255,255,255,0.055) !important;
        backdrop-filter: blur(20px) saturate(140%) !important;
        -webkit-backdrop-filter: blur(20px) saturate(140%) !important;
        border: 1px solid rgba(255,255,255,0.14) !important;
        border-radius: 18px !important;
        box-shadow: 0 8px 24px rgba(0,0,0,0.35),
                    inset 0 1px 0 rgba(255,255,255,0.06) !important;
      }

      /* ---------- Gelembung chat rapi ala WhatsApp: kubus, kiri/kanan ---------- */
      [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.055) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 12px !important;
        padding:.55rem .85rem !important;
        max-width:78% !important;
        margin-bottom:.4rem !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3) !important;
      }
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
        margin-left: auto !important;
        flex-direction: row-reverse !important;
        background: rgba(201,162,39,0.14) !important;
        border-color: rgba(201,162,39,0.3) !important;
      }
      [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
        margin-right: auto !important;
      }
      [data-testid="stChatMessageContent"] p { margin-bottom:.15rem !important; }

      /* ---------- Input teks: pil kaca ---------- */
      .stTextInput input {
        background: rgba(255,255,255,0.07) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 999px !important;
        color:#ECECEF !important;
      }
      .stTextInput label p { color:#B6B6BE !important; }

      /* ---------- Kotak chat: input lonjong + tombol kirim terpisah ---------- */
      [data-testid="stChatInput"] {
        background: transparent !important;
        border: none !important;
        box-shadow:none !important;
        display:flex !important; align-items:center !important; gap:10px !important;
        padding:0 !important;
      }
      [data-testid="stChatInput"] textarea {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.22) !important;
        border-radius: 999px !important;
        padding:.65rem 1.1rem !important;
        color:#ECECEF !important;
        outline:none !important;
        box-shadow:none !important;
      }
      [data-testid="stChatInput"] textarea:focus { border-color: rgba(201,162,39,0.55) !important; }
      [data-testid="stChatInput"] button {
        border-radius: 50% !important;
        width:44px !important; height:44px !important; min-width:44px !important;
        background: linear-gradient(135deg,#D9BE68,#8C712F) !important;
        border:none !important; box-shadow: 0 4px 14px rgba(0,0,0,0.45) !important;
        flex:none !important;
      }

      /* Hilangkan latar putih bawaan di area kotak chat input */
      [data-testid="stBottomBlockContainer"],
      [data-testid="stBottom"] > div,
      .stChatFloatingInputContainer,
      [data-testid="stChatInputContainer"] {
        background: transparent !important;
        box-shadow: none !important;
        border-top: none !important;
      }

      /* ---------- Tombol: pil kaca ---------- */
      .stButton button {
        border-radius: 999px !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        backdrop-filter: blur(14px) saturate(140%) !important;
        -webkit-backdrop-filter: blur(14px) saturate(140%) !important;
        font-weight:600 !important;
        transition: transform .15s ease, box-shadow .15s ease;
      }
      .stButton button:hover { transform: translateY(-1px); }
      .stButton button[kind="primary"] {
        background: linear-gradient(93deg,#D9BE68 0%,#B99A46 55%,#D9BE68 100%) !important;
        color:#1C1A10 !important; border:none !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.4) !important;
      }
      .stButton button[kind="secondary"] {
        background: rgba(255,255,255,0.08) !important; color:#ECECEF !important;
      }

      /* ---------- Panel kontak kecil (kiri) ---------- */
      .panel-kontak [data-testid="stExpander"] details { border-radius:16px !important; }
      .panel-kontak summary p { font-size:.76rem !important; }

      /* ---------- Tombol Keluar mengambang di pojok kanan bawah (bukan menimpa input) ---------- */
      div[data-testid="stElementContainer"]:has(.anchor-keluar) {
        height:0 !important; overflow:visible !important; margin:0 !important;
      }
      div[data-testid="stElementContainer"]:has(.anchor-keluar) + div[data-testid="stElementContainer"] {
        position: fixed !important; right:18px !important; bottom:118px !important;
        z-index: 999 !important; width:auto !important; left:auto !important;
      }
      div[data-testid="stElementContainer"]:has(.anchor-keluar) + div[data-testid="stElementContainer"] div[data-testid="stButton"] {
        width:auto !important;
      }
      div[data-testid="stElementContainer"]:has(.anchor-keluar) + div[data-testid="stElementContainer"] button {
        width:auto !important; white-space:nowrap !important;
        border-radius: 999px !important; padding:.4rem 1rem !important;
        background: rgba(255,255,255,0.08) !important; color:#ECECEF !important;
        border:1px solid rgba(255,255,255,0.2) !important;
        box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
      }

      /* ---------- Elemen kecil ---------- */
      .admin-badge { display:inline-block; font-size:.62rem; font-weight:700;
        color:#F0D998; background:rgba(201,162,39,0.16);
        border:1px solid rgba(201,162,39,0.35);
        border-radius:999px; padding:1px 9px; margin-left:6px;
        backdrop-filter: blur(6px); }
      .admin-badge .material-symbols-outlined { font-size:.85rem; vertical-align:-2px; }
      .jam { font-size:.62rem; color:#8B8B93; }

      [data-testid="stExpander"] { border:none !important; background:transparent !important; }
      [data-testid="stExpander"] summary { color:#ECECEF !important; }
      [data-testid="stAlertContainer"] { border-radius:14px !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _logo_html(size: int = 84) -> str:
    if not _LOGO_ADA:
        return (
            '<div class="logo-wrap" style="font-size:1.9rem;">'
            '<span class="material-symbols-outlined" style="position:relative;z-index:2;">shield_person</span>'
            '</div>'
        )
    return f'<div class="logo-wrap"><img src="{LOGO_URL}" /></div>'


def _mascot_html(src: str, css_class: str, keterangan: str = "") -> str:
    onerror = "this.parentElement.style.display='none';"
    ket = f'<span>{html.escape(keterangan)}</span>' if keterangan else ""
    return (
        f'<div class="{css_class}"><img src="{src}" onerror="{onerror}" />{ket}</div>'
    )


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
    label = f"**{html.escape(str(m.get('pengirim', 'Seseorang')))}**" + (
        '<span class="admin-badge">'
        '<span class="material-symbols-outlined">verified</span> RESMI</span>'
        if resmi else "")
    avatar = (LOGO_URL if (resmi and _LOGO_ADA) else
              (":material/shield_person:" if resmi else None))
    with st.chat_message("assistant" if resmi else "user", avatar=avatar):
        st.markdown(
            f"{label}  \n{html.escape(str(m.get('teks', '')))}  \n"
            f'<span class="jam">{html.escape(str(m.get("jam", "")))}</span>',
            unsafe_allow_html=True,
        )


def halaman_masuk() -> None:
    if st.session_state.pop("anim_keluar", False):
        st.markdown(
            _mascot_html(MASCOT_KELUAR, "mascot-exit", "Sampai jumpa lagi"),
            unsafe_allow_html=True,
        )

    st.markdown(
        _mascot_html(MASCOT_MASUK, "mascot-idle"),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="room-head"><h1 class="judul">Ampera Official Group</h1>'
        '<div class="sub">ROOM CHAT RESMI</div>'
        '<div class="garis"></div></div>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(
            '<div style="text-align:center;font-size:.7rem;'
            'letter-spacing:.16em;color:#9C9CA6;font-weight:600;'
            'margin-bottom:.5rem;">MASUK KE ROOM</div>',
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
        if st.button(":material/login: Masuk Room", use_container_width=True,
                     type="primary", key="btn_masuk"):
            nama_bersih = " ".join((nama or "").split())
            if not nama_bersih:
                st.warning("Isi dulu nama panggilanmu ya.",
                           icon=":material/error:")
            elif ("ampera" in nama_bersih.lower()
                  and "official" in nama_bersih.lower()):
                st.error("Nama itu khusus admin resmi. Pilih nama lain ya.",
                          icon=":material/block:")
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
    if st.session_state.pop("anim_kirim", False):
        st.markdown(
            _mascot_html(MASCOT_KIRIM, "mascot-toast", "Pesan terkirim"),
            unsafe_allow_html=True,
        )

    st.markdown(_logo_html(), unsafe_allow_html=True)
    st.markdown(
        '<div class="room-head"><h1 class="judul">Ampera Official Group</h1>'
        '<div class="sub">ROOM CHAT RESMI</div>'
        '<div class="garis"></div></div>',
        unsafe_allow_html=True,
    )

    identitas = f"<b>{html.escape(st.session_state.nama)}</b>"
    if st.session_state.tag:
        identitas += (f' <span style="color:#8B8B93">'
                      f'#{st.session_state.tag}</span>')
    st.markdown(
        f'<div style="text-align:center;font-size:.78rem;color:#B6B6BE;'
        f'margin-bottom:.35rem;">Masuk sebagai: {identitas}</div>',
        unsafe_allow_html=True,
    )
    st.caption(":material/bolt: Setiap pesanmu langsung terkirim ke admin "
               "Ampera Official.")

    # Panel kontak kecil di sisi kiri — bisa diisi / diganti kapan saja,
    # ikut terkirim di pesan berikutnya, jadi admin tahu harus membalas
    # ke mana.
    col_kontak, _ = st.columns([1, 2])
    with col_kontak:
        st.markdown('<div class="panel-kontak">', unsafe_allow_html=True)
        with st.expander(":material/mail: Kontak", expanded=False):
            st.caption(
                f"Saat ini: {st.session_state.kontak or 'belum diisi'}"
            )
            baru = st.text_input(
                "Email / No. HP kamu",
                value=st.session_state.kontak,
                max_chars=60,
                key="in_kontak_edit",
            )
            if st.button(":material/check: Simpan", key="btn_simpan_kontak"):
                st.session_state.kontak = " ".join((baru or "").split())
                st.session_state.pop("in_kontak_edit", None)
                st.toast("Kontak kamu tersimpan.",
                         icon=":material/check_circle:")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    for m in st.session_state.pesan:
        _bubble(m)

    # Tombol Keluar — mengambang di pojok kanan bawah, TIDAK menimpa kotak
    # chat (lihat CSS ".anchor-keluar" di atas untuk cara kerjanya: anchor
    # ditinggikan 0, lalu elemen sesudahnya di-fixed dengan lebar otomatis).
    st.markdown('<span class="anchor-keluar"></span>', unsafe_allow_html=True)
    if st.button(":material/logout: Keluar", key="btn_keluar"):
        st.session_state["anim_keluar"] = True
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
        st.session_state["anim_kirim"] = True
        if kirim_ke_admin(
            st.session_state.nama,
            st.session_state.tag,
            st.session_state.kontak,
            bersih,
        ):
            st.toast("Pesan terkirim ke admin Ampera Official.",
                     icon=":material/check_circle:")
        else:
            st.toast("Pesan tampil di sini, tapi gagal terkirim ke admin — "
                     "coba kirim ulang ya.", icon=":material/warning:")
        st.rerun()


# ---------------------------------------------------------------------------
# JALAN UTAMA
# ---------------------------------------------------------------------------
init_state()

if st.session_state.masuk:
    halaman_room()
else:
    halaman_masuk()
