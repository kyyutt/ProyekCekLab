# Ini adalah file: convert_to_db.py
# VERSI FINAL (Menyimpan data persis seperti Excel)

import pandas as pd
import sqlite3
import sys
from datetime import time

def excel_time_to_hhmm(fraction_or_time):
    if isinstance(fraction_or_time, time):
        return fraction_or_time.strftime('%H:%M')
    if isinstance(fraction_or_time, (int, float)):
        if pd.isna(fraction_or_time):
            return None
        total_minutes = round(fraction_or_time * 24 * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{int(hours):02d}:{int(minutes):02d}"
    if isinstance(fraction_or_time, str):
        if ":" in fraction_or_time:
            return fraction_or_time
    return None

def create_database():
    csv_file = "HasilQuery.xls"
    db_file = "jadwal.db"
    
    try:
        df = pd.read_excel(csv_file) 
        
        df['jam_mulai_hhmm'] = df['jam_mulai'].apply(excel_time_to_hhmm)
        df['jam_selesai_hhmm'] = df['jam_selesai'].apply(excel_time_to_hhmm)
        df.dropna(subset=['jam_mulai_hhmm', 'jam_selesai_hhmm'], inplace=True)
        
        # --- PERUBAHAN DI SINI ---
        # Kita HANYA membersihkan spasi (.str.strip())
        # Kita TIDAK pakai .str.lower()
        df['hari'] = df['hari'].astype(str).str.strip()
        df['ruang'] = df['ruang'].astype(str).str.strip()
        # --- BATAS PERUBAHAN ---
        
        df['nama_matakuliah'] = df['nama_matakuliah'].astype(str).str.strip()
        
        df_final = df[['hari', 'ruang', 'jam_mulai_hhmm', 'jam_selesai_hhmm', 'nama_matakuliah']]
        
        conn = sqlite3.connect(db_file)
        df_final.to_sql('jadwal', conn, if_exists='replace', index=False)
        
        cursor = conn.cursor()
        cursor.execute("CREATE INDEX idx_hari_ruang ON jadwal (hari, ruang)")
        conn.close()
        
        print(f"--- SUKSES (Data Sesuai Excel) ---")
        print(f"File '{csv_file}' telah dikonversi ke '{db_file}'.")
        print("Data 'ruang' dan 'hari' sekarang disimpan persis seperti aslinya.")

    except FileNotFoundError:
        print(f"[Error] File '{csv_file}' tidak ditemukan.", file=sys.stderr)
    except Exception as e:
        print(f"[Error] Terjadi kesalahan: {e}", file=sys.stderr)

if __name__ == "__main__":
    create_database()