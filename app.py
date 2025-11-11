# Ini adalah file: app.py
# VERSI FINAL (Menggunakan SVG Lokal & Data Sesuai Excel)

import streamlit as st
import sqlite3
import sys
from datetime import datetime, time
import base64  # <-- Import untuk SVG
import os      # <-- Import untuk SVG

DB_FILE = "jadwal.db"

# --- FUNGSI BARU UNTUK MEMBACA SVG ---
@st.cache_data # Cache agar tidak dibaca ulang terus
def get_svg_as_data_uri(file_path):
    """Membaca file SVG dan meng-enkode-nya sebagai Base64 data URI."""
    if not os.path.exists(file_path):
        # Beri peringatan di terminal jika file tidak ada
        print(f"Peringatan: File icon tidak ditemukan di {file_path}")
        return "" # Kembalikan string kosong jika file tidak ada
    try:
        with open(file_path, "rb") as f:
            svg_bytes = f.read()
        b64_svg = base64.b64encode(svg_bytes).decode("utf-8")
        # Kembalikan sebagai data URI yang bisa dibaca CSS
        return f"data:image/svg+xml;base64,{b64_svg}"
    except Exception as e:
        print(f"Error membaca SVG {file_path}: {e}")
        return ""
# --- BATAS FUNGSI BARU ---

def get_db_connection():
    """Membuka koneksi ke database SQLite."""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Error koneksi database: {e}")
        return None

@st.cache_data(ttl=3600)
def get_unique_options():
    """Mengambil data unik dari DB (Sesuai Excel)"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Mengurutkan berdasarkan data asli (Kapital)
            cursor.execute("SELECT DISTINCT hari FROM jadwal ORDER BY CASE hari WHEN 'Senin' THEN 1 WHEN 'Selasa' THEN 2 WHEN 'Rabu' THEN 3 WHEN 'Kamis' THEN 4 WHEN 'Jumat' THEN 5 WHEN 'Sabtu' THEN 6 ELSE 7 END")
            list_hari = [row['hari'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT ruang FROM jadwal ORDER BY ruang")
            list_ruang = [row['ruang'] for row in cursor.fetchall()]
            
            return list_hari, list_ruang
        
        except sqlite3.Error as e:
            st.error(f"Gagal mengambil data options: {e}")
            return [], []
        finally:
            conn.close()
    return [], []

def cek_ketersediaan_db(input_hari, input_ruang, input_jam_str):
    """Mencari data di DB (Sesuai Excel)"""
    conn = get_db_connection()
    if not conn: return "ERROR", None
    try:
        cursor = conn.cursor()
        
        # Mencari data apa adanya (tanpa .lower())
        query_hari = input_hari
        query_ruang = input_ruang
        
        query = """
            SELECT nama_matakuliah, jam_mulai_hhmm, jam_selesai_hhmm
            FROM jadwal WHERE hari = ? AND ruang = ? AND ? >= jam_mulai_hhmm AND ? < jam_selesai_hhmm
        """
        cursor.execute(query, (query_hari, query_ruang, input_jam_str, input_jam_str))
        bentrok = cursor.fetchone()
        
        return ("DIGUNAKAN", bentrok) if bentrok else ("TERSEDIA", None)
                
    except sqlite3.Error as e:
        print(f"[Error] Gagal query: {e}", file=sys.stderr)
        return "ERROR", None
    finally:
        conn.close()

# --- Tampilan Streamlit ---

st.set_page_config(
    page_title="Cek Lab USN",
    page_icon="logo-universitas.png", # Icon tab browser (file lokal)
    layout="centered"
)

st.title("Sistem Pengecekan Ketersediaan Lab USN")
st.caption("Penerapan Finite State Automata (DFA)")

# --- CSS UNTUK IKON SVG DI TAB ---

# 1. Baca file SVG kamu
# PASTIKAN NAMA FILE SAMA
icon_search_uri = get_svg_as_data_uri("icon-search.svg")
icon_info_uri = get_svg_as_data_uri("icon-info.svg")

# 2. Injeksi CSS yang menggunakan SVG
st.markdown(f"""
    <style>
    /* Target div di dalam tab pertama */
    [data-testid="stTab"]:nth-of-type(1) > div::before {{
        content: "";
        display: inline-block;
        width: 1em; /* Ukuran icon */
        height: 1em;
        margin-right: 0.4em; /* Jarak icon ke teks */
        vertical-align: -0.15em; /* Sejajarkan icon dengan teks */
        
        /* Teknik 'mask-image' */
        background-color: currentColor; /* Ambil warna teks (biru/abu-abu) */
        mask-image: url("{icon_search_uri}");
        mask-size: 100% 100%;
        mask-repeat: no-repeat;
    }}

    /* Target div di dalam tab kedua */
    [data-testid="stTab"]:nth-of-type(2) > div::before {{
        content: "";
        display: inline-block;
        width: 1em;
        height: 1em;
        margin-right: 0.4em;
        vertical-align: -0.15em;

        background-color: currentColor;
        mask-image: url("{icon_info_uri}");
        mask-size: 100% 100%;
        mask-repeat: no-repeat;
    }}
    </style>
    """, unsafe_allow_html=True)
# --- BATAS CSS ---


list_hari, list_ruang = get_unique_options()

if not list_hari or not list_ruang:
    st.error("Gagal memuat data jadwal dari database.")
else:
    # Buat Tab (Tanpa emoji)
    tab_cek, tab_info = st.tabs(["Cek Ketersediaan", "Info Aplikasi"])
    
    with tab_cek:
        st.subheader("Cek Ketersediaan Ruang")
        with st.form(key="cek_form_tab"):
            # Dropdown akan menampilkan data asli: "Senin", "Software I"
            input_hari = st.selectbox("1. Pilih Hari", list_hari)
            input_ruang = st.selectbox("2. Pilih Ruang Lab", list_ruang)
            default_time = time(8, 0)
            input_jam_obj = st.time_input("3. Pilih Jam", value=default_time)
            submit_button = st.form_submit_button(
                label="Cek Sekarang", type="primary", use_container_width=True
            )
            input_jam_str = input_jam_obj.strftime("%H:%M")

        st.divider() 
        
        if submit_button:
            st.markdown(f"### Hasil Pengecekan (State q3)")
            st.write(f"Mencari ketersediaan untuk **{input_ruang}** pada hari **{input_hari}** jam **{input_jam_str}**...")
            status, detail_bentrok = cek_ketersediaan_db(input_hari, input_ruang, input_jam_str)
            
            if status == "TERSEDIA":
                st.success(f"**Status: TERSEDIA (State q4)**\n\nRuang **{input_ruang}** dapat digunakan.")
            elif status == "DIGUNAKAN":
                st.error(f"**Status: DIGUNAKAN (State q5)**\n\nRuang **{input_ruang}** sedang dipakai untuk:")
                with st.container(border=True):
                    st.write(f"**Matakuliah:** {detail_bentrok['nama_matakuliah']}")
                    st.write(f"**Waktu:** {detail_bentrok['jam_mulai_hhmm']} - {detail_bentrok['jam_selesai_hhmm']}")
            else:
                st.error("Terjadi kesalahan saat memproses permintaan.")
        else:
            st.info("Silakan pilih Hari, Ruang, dan Jam, lalu tekan 'Cek Sekarang'.")

    with tab_info:
        st.subheader("Tentang Aplikasi Ini")
        st.write(
            """
            Aplikasi ini adalah implementasi dari **Finite State Automata (DFA)** untuk sistem pengecekan ketersediaan ruang laboratorium.
            
            **Alur FSA (DFA):**
            - **$q_0$ (State Awal):** Menunggu input.
            - **$q_1$ (Hari Dipilih):** Input 'Hari' diterima.
            - **$q_2$ (Ruang Dipilih):** Input 'Ruang' diterima.
            - **$q_3$ (Jam Dipilih):** Input 'Jam' diterima, sistem melakukan pengecekan ke database.
            - **$q_4$ (State Akhir - Tersedia):** Hasil pengecekan tidak menemukan jadwal (Tersedia).
            - **$q_5$ (State Akhir - Digunakan):** Hasil pengecekan menemukan jadwal (Digunakan).
            
            **Teknologi yang Digunakan:**
            - Python
            - Streamlit (untuk tampilan User Interface)
            - Pandas (untuk pemrosesan data awal)
            - SQLite (sebagai database jadwal)
            """
        )
        st.write("---")
        st.write("Dibuat oleh: **Rizqiyah**")