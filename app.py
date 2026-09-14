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
# TAMPILAN — LIQUID GLASS UI
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      /* ============================================================
         LIQUID GLASS — kanvas, cahaya & gerak
         ============================================================ */
      @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&display=swap');

      .stApp {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont,
                     'Segoe UI', sans-serif !important;
        background:
          radial-gradient(900px 620px at 12% -10%, rgba(124,92,255,.26) 0%, transparent 60%),
          radial-gradient(820px 640px at 108% 4%, rgba(232,121,249,.17) 0%, transparent 56%),
          radial-gradient(1000px 900px at 50% 118%, rgba(34,211,238,.16) 0%, transparent 60%),
          linear-gradient(165deg, #070613 0%, #0D0B26 52%, #120C33 100%) !important;
        color: #EFEAFB;
        -webkit-font-smoothing: antialiased;
      }
      .stApp input, .stApp textarea, .stApp button { font-family: inherit !important; }

      [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] {
        background: transparent !important;
      }
      .block-container { padding-top: 2rem; max-width: 780px; }
      ::selection { background: rgba(139,92,246,.5); color: #fff; }
      ::-webkit-scrollbar { width: 8px; }
      ::-webkit-scrollbar-thumb { background: rgba(255,255,255,.18); border-radius: 999px; }
      ::-webkit-scrollbar-track { background: transparent; }

      /* ---------- Blob "liquid" melayang di belakang kaca ---------- */
      .liquid-bg { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
      .blob { position: absolute; border-radius: 50%;
              mix-blend-mode: screen; filter: blur(72px); opacity: .5;
              will-change: transform; }
      .blob-1 { width: 46vmax; height: 46vmax; left: -15vmax; top: -17vmax;
                background: radial-gradient(circle at 36% 36%, #7C5CFF, transparent 68%);
                animation: drift1 26s ease-in-out infinite alternate; }
      .blob-2 { width: 40vmax; height: 40vmax; right: -13vmax; top: 2vmax;
                background: radial-gradient(circle at 40% 40%, #E879F9, transparent 66%);
                animation: drift2 32s ease-in-out infinite alternate; }
      .blob-3 { width: 48vmax; height: 48vmax; left: 6vmax; bottom: -22vmax;
                background: radial-gradient(circle at 45% 40%, #22D3EE, transparent 66%);
                animation: drift3 38s ease-in-out infinite alternate; }
      .blob-4 { width: 26vmax; height: 26vmax; right: 14vmax; bottom: -8vmax;
                background: radial-gradient(circle at 50% 50%, #F5B85C, transparent 66%);
                opacity: .32; animation: drift1 24s ease-in-out infinite alternate-reverse; }
      @keyframes drift1 { from { transform: translate3d(0,0,0) scale(1); }
                          to   { transform: translate3d(9vmax,7vmax,0) scale(1.16); } }
      @keyframes drift2 { from { transform: translate3d(0,0,0) scale(1); }
                          to   { transform: translate3d(-8vmax,9vmax,0) scale(1.12); } }
      @keyframes drift3 { from { transform: translate3d(0,0,0) scale(1.1); }
                          to   { transform: translate3d(7vmax,-6vmax,0) scale(.96); } }

      .block-container { position: relative; z-index: 1; }
      [data-testid="stBottom"] { z-index: 3; }

      /* ============================================================
         Permukaan kaca (reusable look)
         ============================================================ */
      .stApp {
        --glass-bg: linear-gradient(135deg, rgba(255,255,255,.14), rgba(255,255,255,.05));
        --glass-brd: rgba(255,255,255,.20);
        --glass-sh: 0 12px 40px rgba(2,0,20,.45), inset 0 1px 0 rgba(255,255,255,.26);
      }

      /* ---------- Kepala room ---------- */
      .room-head { text-align: center; padding: 1.5rem 0 .4rem;
                   position: relative; z-index: 0; }
      .room-head::before { content: ""; position: absolute; z-index: -1;
        top: -46px; left: 18%; right: 18%; height: 170px;
        background: radial-gradient(ellipse at center, rgba(167,139,250,.34), transparent 70%);
        filter: blur(14px); }
      .room-head .judul { font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-weight: 800; font-size: 2.1rem; letter-spacing: .02em; margin: 0;
        background: linear-gradient(92deg, #FDE68A 0%, #F0ABFC 34%, #A5B4FC 66%, #67E8F9 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent;
        filter: drop-shadow(0 3px 20px rgba(167,139,250,.35)); }
      .room-head .sub { font-size: .7rem; font-weight: 600;
        letter-spacing: .42em; text-transform: uppercase;
        color: rgba(212,206,242,.62); margin-top: 9px; }
      .status-pill { display: inline-flex; align-items: center; gap: .45rem;
        margin-top: 1rem; padding: .34rem .95rem; border-radius: 999px;
        background: rgba(74,222,128,.09); border: 1px solid rgba(74,222,128,.32);
        color: #A7F3D0; font-size: .68rem; font-weight: 700; letter-spacing: .1em;
        backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.18); }
      .status-pill .dot { width: 8px; height: 8px; border-radius: 50%;
        background: #34D399; box-shadow: 0 0 10px #34D399;
        animation: pulse 2.2s ease-in-out infinite; }
      @keyframes pulse { 0%,100% { opacity: 1; transform: scale(1); }
                         50% { opacity: .55; transform: scale(.78); } }

      .lead { text-align: center; color: rgba(226,222,247,.82);
              font-size: .92rem; line-height: 1.7; margin: 1.1rem 0 1.5rem; }

      /* ---------- Kartu kaca (container berbingkai / form masuk) ---------- */
      [data-testid="stVerticalBlockBorderWrapper"] {
        background: linear-gradient(150deg, rgba(255,255,255,.13), rgba(255,255,255,.05)) !important;
        border: 1px solid rgba(255,255,255,.22) !important;
        border-radius: 24px !important;
        backdrop-filter: blur(24px) saturate(160%);
        -webkit-backdrop-filter: blur(24px) saturate(160%);
        box-shadow: 0 20px 54px rgba(2,0,24,.5), inset 0 1px 0 rgba(255,255,255,.3) !important;
        position: relative;
      }
      [data-testid="stVerticalBlockBorderWrapper"]::before {
        content: ""; position: absolute; top: 0; left: 10%; right: 10%; height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent);
      }

      /* ---------- Label & kolom isian ---------- */
      [data-testid="stTextInput"] label p, [data-testid="stTextInput"] label span,
      [data-testid="stTextInput"] label div {
        color: rgba(230,226,248,.88) !important; font-weight: 600; font-size: .82rem;
      }
      .stTextInput input, .stTextArea textarea {
        background: rgba(9,8,28,.5) !important;
        border: 1px solid rgba(255,255,255,.17) !important;
        border-radius: 14px !important;
        color: #F2EFFD !important;
        padding: .7rem 1rem !important;
        transition: border-color .22s, box-shadow .22s, background .22s;
      }
      .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: rgba(165,180,252,.75) !important;
        box-shadow: 0 0 0 3px rgba(139,124,246,.22), 0 0 26px rgba(139,124,246,.18) !important;
        background: rgba(15,13,38,.65) !important;
      }
      .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: rgba(198,192,232,.42) !important;
      }

      /* ---------- Tombol ---------- */
      .stButton > button {
        border-radius: 999px !important;
        background: linear-gradient(135deg, rgba(255,255,255,.16), rgba(255,255,255,.06)) !important;
        border: 1px solid rgba(255,255,255,.24) !important;
        color: #EFECFF !important; font-weight: 600 !important;
        letter-spacing: .02em;
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 6px 20px rgba(2,0,24,.35), inset 0 1px 0 rgba(255,255,255,.3) !important;
        transition: all .22s cubic-bezier(.2,.8,.3,1) !important;
      }
      .stButton > button:hover {
        transform: translateY(-2px);
        border-color: rgba(255,255,255,.46) !important;
        background: linear-gradient(135deg, rgba(255,255,255,.22), rgba(255,255,255,.10)) !important;
        box-shadow: 0 12px 30px rgba(96,90,255,.35), inset 0 1px 0 rgba(255,255,255,.36) !important;
      }
      .stButton > button:active { transform: translateY(0) scale(.98); }
      .stButton > button[kind="primary"],
      .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #F0ABFC -25%, #8B5CF6 30%, #6366F1 62%, #22D3EE 135%) !important;
        border: 1px solid rgba(255,255,255,.38) !important;
        box-shadow: 0 12px 32px rgba(124,92,255,.48), inset 0 1px 0 rgba(255,255,255,.5) !important;
      }
      .stButton > button[kind="primary"]:hover {
        filter: brightness(1.13);
        box-shadow: 0 16px 38px rgba(124,92,255,.55), 0 0 34px rgba(34,211,238,.28),
                    inset 0 1px 0 rgba(255,255,255,.55) !important;
      }
      .stButton > button p { color: inherit !important; }

      /* ---------- Gelembung chat kaca ---------- */
      [data-testid="stChatMessage"] {
        background: linear-gradient(140deg, rgba(253,230,138,.11), rgba(245,171,53,.05)) !important;
        border: 1px solid rgba(250,214,150,.28) !important;
        border-radius: 20px !important;
        padding: .75rem 1.05rem !important;
        backdrop-filter: blur(18px) saturate(150%);
        -webkit-backdrop-filter: blur(18px) saturate(150%);
        box-shadow: 0 10px 28px rgba(2,0,20,.35), inset 0 1px 0 rgba(255,255,255,.2) !important;
        animation: rise .38s cubic-bezier(.2,.8,.3,1) both;
      }
      [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        background: linear-gradient(140deg, rgba(129,140,248,.23), rgba(34,211,238,.08)) !important;
        border: 1px solid rgba(148,163,253,.38) !important;
        box-shadow: 0 10px 28px rgba(24,12,80,.4), inset 0 1px 0 rgba(255,255,255,.24) !important;
      }
      @keyframes rise { from { opacity: 0; transform: translateY(14px) scale(.985); }
                        to   { opacity: 1; transform: none; } }

      [data-testid^="chatAvatarIcon"] {
        background: linear-gradient(135deg, rgba(255,255,255,.22), rgba(255,255,255,.07)) !important;
        border: 1px solid rgba(255,255,255,.28) !important;
        color: #E9E4FF !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.38), 0 4px 14px rgba(0,0,0,.35);
      }

      .admin-badge { display: inline-block; font-size: .62rem; font-weight: 800;
        letter-spacing: .06em; color: #2B1A02;
        background: linear-gradient(135deg, #FDE68A, #F4B840);
        border: 1px solid rgba(255,235,180,.85);
        border-radius: 999px; padding: 2px 10px; margin-left: 8px;
        box-shadow: 0 0 16px rgba(244,184,64,.5); }
      .jam { display: inline-block; margin-top: 7px; font-size: .66rem;
        letter-spacing: .05em; color: rgba(214,208,240,.5); }

      /* ---------- Caption = chip kaca ---------- */
      [data-testid="stCaptionContainer"] {
        background: rgba(103,232,249,.08);
        border: 1px solid rgba(103,232,249,.24);
        border-radius: 999px;
        padding: .32rem .95rem !important;
        width: fit-content; margin: .3rem auto .9rem;
        backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
      }
      [data-testid="stCaptionContainer"] p { color: rgba(178,235,250,.92) !important; font-size: .76rem; }

      /* ---------- Expander kaca ---------- */
      [data-testid="stExpander"] details {
        background: linear-gradient(150deg, rgba(255,255,255,.09), rgba(255,255,255,.03)) !important;
        border: 1px solid rgba(255,255,255,.17) !important;
        border-radius: 18px !important;
        backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
        box-shadow: inset 0 1px 0 rgba(255,255,255,.18);
      }
      [data-testid="stExpander"] summary p { font-weight: 600; color: rgba(226,221,247,.9); }

      /* ---------- Kotak input chat kaca ---------- */
      [data-testid="stBottom"], [data-testid="stBottomBlockContainer"] {
        background: transparent !important; background-image: none !important;
      }
      [data-testid="stChatInput"] {
        background: rgba(13,11,34,.62) !important;
        border: 1px solid rgba(255,255,255,.21) !important;
        border-radius: 999px !important;
        backdrop-filter: blur(24px) saturate(170%);
        -webkit-backdrop-filter: blur(24px) saturate(170%);
        box-shadow: 0 16px 44px rgba(2,0,20,.55), inset 0 1px 0 rgba(255,255,255,.24) !important;
        transition: border-color .25s, box-shadow .25s;
      }
      [data-testid="stChatInput"]:focus-within {
        border-color: rgba(165,180,252,.72) !important;
        box-shadow: 0 16px 46px rgba(80,70,220,.35), 0 0 0 4px rgba(139,124,246,.18),
                    inset 0 1px 0 rgba(255,255,255,.26) !important;
      }
      [data-testid="stChatInput"] textarea { color: #F2EFFF !important; background: transparent !important; }
      [data-testid="stChatInput"] textarea::placeholder { color: rgba(199,193,233,.45) !important; }
      [data-testid="stChatInput"] button { color: #A5B4FC !important; }

      /* ---------- Alert / toast kaca ---------- */
      [data-testid="stAlert"] {
        background: linear-gradient(135deg, rgba(255,190,120,.10), rgba(255,190,120,.04)) !important;
        border: 1px solid rgba(255,196,130,.32) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      }
      [data-testid="stToast"] {
        background: rgba(20,17,48,.92) !important;
        border: 1px solid rgba(255,255,255,.22) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
        box-shadow: 0 14px 36px rgba(0,0,0,.5) !important;
      }

      hr { border-color: rgba(255,255,255,.12) !important; }

      @media (prefers-reduced-motion: reduce) {
        .blob, .status-pill .dot, [data-testid="stChatMessage"] { animation: none !important; }
      }
    </style>

    <div class="liquid-bg" aria-hidden="true">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
      <div class="blob blob-4"></div>
    </div>
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


def _kepala_room(pil: str) -> None:
    st.markdown(
        '<div class="room-head"><h1 class="judul">🔱 Ampera Official Group</h1>'
        '<div class="sub">Room Chat Resmi Ampera Official</div>'
        f'<div class="status-pill"><span class="dot"></span>{pil}</div></div>',
        unsafe_allow_html=True,
    )


def halaman_masuk() -> None:
    _kepala_room("ADMIN ONLINE · DIPANTAU SETIAP HARI")
    st.markdown(
        '<div class="lead">Mau tanya-tanya atau berlangganan produk '
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
        if st.button("Masuk Room  ✨", use_container_width=True, type="primary",
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
    _kepala_room("ADMIN ONLINE · SIAP MEMBALAS")
    c_kiri, c_kanan = st.columns([3, 1])
    with c_kiri:
        identitas = f"<b>{html.escape(st.session_state.nama)}</b>"
        if st.session_state.tag:
            identitas += (f' <span style="color:#8B86B5">'
                          f'#{st.session_state.tag}</span>')
        st.markdown(
            f'<div style="font-size:.85rem;color:#C6C1E8;">Masuk sebagai: '
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
