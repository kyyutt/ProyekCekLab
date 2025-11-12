# VERSI FINAL (NFA Wizard, Sesuai Desain 5-State)

import streamlit as st
import sqlite3
import sys
from datetime import datetime, time
import base64
import os

DB_FILE = "jadwal.db"

# --- FUNGSI BACA SVG (Tetap Sama) ---
@st.cache_data
def get_svg_as_data_uri(file_path):
    if not os.path.exists(file_path):
        print(f"Peringatan: File icon tidak ditemukan di {file_path}")
        return ""
    try:
        with open(file_path, "rb") as f:
            svg_bytes = f.read()
        b64_svg = base64.b64encode(svg_bytes).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64_svg}"
    except Exception as e:
        print(f"Error membaca SVG {file_path}: {e}")
        return ""

# --- FUNGSI DATABASE (Tetap Sama) ---
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Error koneksi database: {e}")
        return None

@st.cache_data(ttl=3600)
def get_unique_options():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT hari FROM jadwal ORDER BY CASE hari WHEN 'Senin' THEN 1 WHEN 'Selasa' THEN 2 WHEN 'Rabu' THEN 3 WHEN 'Kamis' THEN 4 WHEN 'Jumat' THEN 5 WHEN 'Sabtu' THEN 6 ELSE 7 END")
            list_hari = [row['hari'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT ruang FROM jadwal ORDER BY ruang")
            list_ruang = [row['ruang'] for row in cursor.fetchall()]
            
            list_hari.insert(0, "-- Pilih Hari --")
            list_ruang.insert(0, "-- Pilih Ruang --")
            
            return list_hari, list_ruang
        
        except sqlite3.Error as e:
            st.error(f"Gagal mengambil data options: {e}")
            return [], []
        finally:
            conn.close()
    return [], []

def cek_ketersediaan_db(input_hari, input_ruang, input_jam_str):
    conn = get_db_connection()
    if not conn: return "ERROR", None
    try:
        cursor = conn.cursor()
        query = """
            SELECT nama_matakuliah, jam_mulai_hhmm, jam_selesai_hhmm
            FROM jadwal WHERE hari = ? AND ruang = ? AND ? >= jam_mulai_hhmm AND ? < jam_selesai_hhmm
        """
        cursor.execute(query, (input_hari, input_ruang, input_jam_str, input_jam_str))
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
    page_icon="logo-universitas.png",
    layout="centered"
)

st.title("Sistem Pengecekan Ketersediaan Lab USN")
st.caption("Penerapan Finite State Automata (NFA)")

# --- CSS UNTUK IKON SVG DI TAB (Tetap Sama) ---
icon_search_uri = get_svg_as_data_uri("icon-search.svg")
icon_info_uri = get_svg_as_data_uri("icon-info.svg")
st.markdown(f"""
    <style>
    /* ... (CSS Anda tetap di sini, disembunyikan agar ringkas) ... */
    [data-testid="stTab"]:nth-of-type(1) > div::before {{
        content: ""; display: inline-block; width: 1em; height: 1em;
        margin-right: 0.4em; vertical-align: -0.15em;
        background-color: currentColor;
        mask-image: url("{icon_search_uri}"); mask-size: 100% 100%; mask-repeat: no-repeat;
    }}
    [data-testid="stTab"]:nth-of-type(2) > div::before {{
        content: ""; display: inline-block; width: 1em; height: 1em;
        margin-right: 0.4em; vertical-align: -0.15em;
        background-color: currentColor;
        mask-image: url("{icon_info_uri}"); mask-size: 100% 100%; mask-repeat: no-repeat;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LOGIKA APLIKASI NFA ---

list_hari, list_ruang = get_unique_options()

if not list_hari or not list_ruang:
    st.error("Gagal memuat data jadwal dari database.")
else:
    tab_cek, tab_info = st.tabs(["Cek Ketersediaan", "Info Aplikasi"])
    
    with tab_cek:
        
        # 1. Inisialisasi State NFA (Memori Mesin)
        # State: q0, q1, q2, q3 (Tersedia), q4 (Digunakan)
        if 'dfa_state' not in st.session_state:
            st.session_state.dfa_state = 'q0'
            st.session_state.input_hari = "-- Pilih Hari --"
            st.session_state.input_ruang = "-- Pilih Ruang --"
            st.session_state.input_jam = time(8, 0) # Default jam 8 pagi
            
        # 2. Logika Transisi dan Render Halaman
        
        # === STATE q0 (Pilih Hari) ===
        if st.session_state.dfa_state == 'q0':
            st.subheader("Langkah 1: Pilih Hari (State $q_0$)")
            
            # Ambil nilai dari session state jika ada (untuk tombol back)
            idx_hari = 0
            if st.session_state.input_hari in list_hari:
                idx_hari = list_hari.index(st.session_state.input_hari)
            
            pilihan_hari = st.selectbox("1. Pilih Hari", list_hari, index=idx_hari)
            
            # Transisi Input '1' (Next)
            if st.button("Lanjut ➔", type="primary", use_container_width=True):
                # Validasi: $\delta(q_0, 0) = \{q_0\}$ (Stay)
                if pilihan_hari == "-- Pilih Hari --":
                    st.warning("⚠️ Mohon pilih hari sebelum lanjut.")
                else:
                    # Transisi: $\delta(q_0, 1) = \{q_1\}$ (Next)
                    st.session_state.input_hari = pilihan_hari
                    st.session_state.dfa_state = 'q1'
                    st.rerun()

        # === STATE q1 (Pilih Ruang) ===
        elif st.session_state.dfa_state == 'q1':
            st.subheader("Langkah 2: Pilih Ruang (State $q_1$)")
            st.caption(f"Hari terpilih: **{st.session_state.input_hari}**")
            
            idx_ruang = 0
            if st.session_state.input_ruang in list_ruang:
                idx_ruang = list_ruang.index(st.session_state.input_ruang)
                
            pilihan_ruang = st.selectbox("2. Pilih Ruang Lab", list_ruang, index=idx_ruang)
            
            col1, col2 = st.columns(2)
            with col1:
                # Transisi Input '0' (Back)
                if st.button("❮ Kembali", use_container_width=True):
                    # $\delta(q_1, 0) = \{q_0\}$
                    st.session_state.input_ruang = pilihan_ruang # Simpan pilihan
                    st.session_state.dfa_state = 'q0'
                    st.rerun()
            with col2:
                # Transisi Input '1' (Next)
                if st.button("Lanjut ➔", type="primary", use_container_width=True):
                    # Validasi: $\delta(q_0, 0) = \{q_0\}$ (Stay)
                    if pilihan_ruang == "-- Pilih Ruang --":
                        st.warning("⚠️ Mohon pilih ruang sebelum lanjut.")
                    else:
                        # $\delta(q_1, 1) = \{q_2\}$
                        st.session_state.input_ruang = pilihan_ruang
                        st.session_state.dfa_state = 'q2'
                        st.rerun()

        # === STATE q2 (Pilih Jam) ===
        elif st.session_state.dfa_state == 'q2':
            st.subheader("Langkah 3: Pilih Jam (State $q_2$)")
            st.caption(f"Hari: **{st.session_state.input_hari}** | Ruang: **{st.session_state.input_ruang}**")
            
            pilihan_jam = st.time_input("3. Pilih Jam", value=st.session_state.input_jam)
            
            col1, col2 = st.columns(2)
            with col1:
                # Transisi Input '0' (Back)
                if st.button("❮ Kembali", use_container_width=True):
                    # $\delta(q_2, 0) = \{q_1\}$
                    st.session_state.input_jam = pilihan_jam # Simpan pilihan
                    st.session_state.dfa_state = 'q1'
                    st.rerun()
            with col2:
                # Transisi Input '1' (Cek)
                if st.button("Cek Sekarang ➔", type="primary", use_container_width=True):
                    # --- INI ADALAH LOGIKA "DETERMINATOR" NFA ---
                    # Transisi: $\delta(q_2, 1) = \{q_3, q_4\}$
                    
                    st.session_state.input_jam = pilihan_jam
                    input_jam_str = pilihan_jam.strftime("%H:%M")
                    
                    # Panggil fungsi pengecekan
                    status, detail_bentrok = cek_ketersediaan_db(
                        st.session_state.input_hari,
                        st.session_state.input_ruang,
                        input_jam_str
                    )
                    
                    # Logika memilih state tujuan
                    if status == "TERSEDIA":
                        st.session_state.dfa_state = 'q3' # Pindah ke state Tersedia
                    elif status == "DIGUNAKAN":
                        st.session_state.dfa_state = 'q4' # Pindah ke state Digunakan
                    else:
                        st.error("Terjadi kesalahan saat memproses data.")
                        # Tetap di state q2
                    
                    st.rerun()

        # === STATE q3 (Hasil: Tersedia) ===
        elif st.session_state.dfa_state == 'q3':
            st.subheader("Hasil: TERSEDIA (State $q_3$)")
            st.success(f"**Status: TERSEDIA**\n\nRuang **{st.session_state.input_ruang}** dapat digunakan pada hari **{st.session_state.input_hari}** jam **{st.session_state.input_jam.strftime('%H:%M')}**.")
            
            # Transisi Input '1' (Reset)
            if st.button("Ulangi Pengecekan ➔", type="primary", use_container_width=True):
                # $\delta(q_3, 1) = \{q_0\}$
                st.session_state.dfa_state = 'q0'
                st.session_state.input_hari = "-- Pilih Hari --"
                st.session_state.input_ruang = "-- Pilih Ruang --"
                st.session_state.input_jam = time(8, 0)
                st.rerun()
            # $\delta(q_3, 0) = \emptyset$ (Tidak ada tombol back)

        # === STATE q4 (Hasil: Digunakan) ===
        elif st.session_state.dfa_state == 'q4':
            st.subheader("Hasil: DIGUNAKAN (State $q_4$)")
            st.error(f"**Status: DIGUNAKAN**\n\nRuang **{st.session_state.input_ruang}** sedang dipakai pada hari **{st.session_state.input_hari}** jam **{st.session_state.input_jam.strftime('%H:%M')}**.")
            
            # Kita panggil ulang fungsi DB untuk mendapatkan detail bentrok
            input_jam_str = st.session_state.input_jam.strftime("%H:%M")
            status, detail_bentrok = cek_ketersediaan_db(
                st.session_state.input_hari,
                st.session_state.input_ruang,
                input_jam_str
            )

            if detail_bentrok:
                with st.container(border=True):
                    st.write(f"**Matakuliah:** {detail_bentrok['nama_matakuliah']}")
                    st.write(f"**Waktu:** {detail_bentrok['jam_mulai_hhmm']} - {detail_bentrok['jam_selesai_hhmm']}")
            
            # Transisi Input '1' (Reset)
            if st.button("Ulangi Pengecekan ➔", type="primary", use_container_width=True):
                # $\delta(q_4, 1) = \{q_0\}$
                st.session_state.dfa_state = 'q0'
                st.session_state.input_hari = "-- Pilih Hari --"
                st.session_state.input_ruang = "-- Pilih Ruang --"
                st.session_state.input_jam = time(8, 0)
                st.rerun()
            # $\delta(q_4, 0) = \emptyset$ (Tidak ada tombol back)


    with tab_info:
        st.subheader("Tentang Aplikasi Ini")
        st.write(
            """
            Aplikasi ini adalah implementasi dari **Nondeterministic Finite Automata (NFA)** untuk sistem pengecekan ketersediaan ruang laboratorium.

            **Alur NFA (Model Wizard 5-State):**
            - **Alfabet Input ($\Sigma$):** `{0 (Back/Stay), 1 (Next/Cek/Reset)}`
            - **States ($Q$):** `{$q_0, q_1, q_2, q_3, q_4$}`
            - **State Awal:** `$q_0$`
            - **State Final ($F$):** `{$q_3, q_4$}`
            
            **Fungsi Transisi ($\delta$):**
            - **$\delta(q_0, 1) = \{q_1\}$** (Input 'Hari' valid)
            - **$\delta(q_0, 0) = \{q_0\}$** (Input 'Hari' tidak valid/Stay)
            - **$\delta(q_1, 1) = \{q_2\}$** (Input 'Ruang' valid)
            - **$\delta(q_1, 0) = \{q_0\}$** (Kembali ke Pilih Hari)
            - **$\delta(q_2, 0) = \{q_1\}$** (Kembali ke Pilih Ruang)
            - **$\delta(q_2, 1) = \{q_3, q_4\}$** (**Transisi Non-Deterministik**)
                - *Logika aplikasi akan memilih $q_3$ jika TERSEDIA.*
                - *Logika aplikasi akan memilih $q_4$ jika DIGUNAKAN.*
            - **$\delta(q_3, 1) = \{q_0\}$** (Reset dari hasil 'Tersedia')
            - **$\delta(q_4, 1) = \{q_0\}$** (Reset dari hasil 'Digunakan')
            - **$\delta(q_3, 0) = \emptyset$** (Tidak ada transisi 'Back' di hasil)
            - **$\delta(q_4, 0) = \emptyset$** (Tidak ada transisi 'Back' di hasil)
            
            **Teknologi yang Digunakan:**
            - Python, Streamlit (UI & State Management)
            - SQLite (Database Jadwal)
            """
        )
        st.write("---")
        st.write("Dibuat oleh: **Rizqiyah**")