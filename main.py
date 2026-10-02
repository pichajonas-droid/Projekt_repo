import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# --- 1. Nastavení cest k souborům ---
SCRIPT_DIR = Path(__file__).resolve().parent

# rtklib
rtklib_exe = SCRIPT_DIR / "RTKLIB" / "rnx2rtkp.exe"

# observacni a navigacni RINEX soubory
obs_file = SCRIPT_DIR / "data" / "Pixel 10a__RNX__20260814113503.26o"
base_file = SCRIPT_DIR / "data" / "gope226j30.26o"
nav_file = SCRIPT_DIR / "data" / "BRDC00IGS_R_20262260000_01D_MN.rnx"

# konfiguracni soubor a vystup
conf_file = SCRIPT_DIR / "nastaveni.conf"
out_pos_file = SCRIPT_DIR / "output" / "vysledek.pos"

# Přesné efemeridy a hodiny
ef_file = SCRIPT_DIR / "data" / "IGS0OPSFIN_20262260000_01D_15M_ORB.SP3"
clk_file = SCRIPT_DIR / "data" / "IGS0OPSFIN_20262260000_01D_30S_CLK.CLK"





# --- 2. Spuštění RTKLIBu přes Python ---
print("Spouštím výpočet v RTKLIBu...")
# Příkaz vypadá takto: rnx2rtkp.exe -k nastaveni.conf -o vysledek.pos moje_mereni.26o base.26o nav.rnx
command = [
    rtklib_exe,
    "-k", conf_file,
    "-o", out_pos_file,
    obs_file,
    base_file,
    nav_file,
    ef_file,
    clk_file
]

# Spuštění procesu
try:
    subprocess.run(command, check=True, cwd=SCRIPT_DIR)
    print(f"Výpočet dokončen! Výsledky uloženy do: {out_pos_file}")
except subprocess.CalledProcessError as e:
    print(f"Chyba při běhu RTKLIBu: {e}")
    exit()




# --- 3. Načtení a vizualizace výsledků pomocí Pandas ---
if out_pos_file.exists:
    # RTKLIB ukládá výsledky do textového souboru, hlavička začíná '%'
    # Přeskočíme řádky s hlavičkou kromě toho posledního, který obsahuje názvy sloupců
    
    # Najdeme řádek s názvy sloupců (obvykle poslední začínající na '%')
    with open(out_pos_file, 'r') as f:
        lines = f.readlines()
        header_line_idx = [i for i, line in enumerate(lines) if line.startswith('%')][-1]
    
    # Načtení dat
    df = pd.read_csv(out_pos_file, skiprows=header_line_idx, sep=r'\s+')
    
    # Odstranění úvodního '%' z názvu prvního sloupce pro lepší manipulaci
    df.rename(columns={df.columns[0]: df.columns[0].replace('%', '')}, inplace=True)
    
    print("\nPrvních 5 vypočtených pozic:")
    print(df.head())

    # --- 4. Vizualizace rozptylu pozice (Šum a Multipath v praxi) ---
    # Pokud jste zvolili výstup 'xyz' nebo 'llh', názvy sloupců se mohou mírně lišit (např. 'x-ecef(m)' nebo 'latitude(deg)')
    # Zde předpokládáme kartézské ECEF souřadnice (x, y, z) nebo lokální (e, n, u)
    
    # Pro jednoduchou ukázku rozptylu odečteme průměrnou hodnotu, abychom dostali odchylky v metrech
    # (Předpokládáme sloupce x-ecef(m) a y-ecef(m), upravte podle skutečné hlavičky souboru)
    x_col = df.columns[2] # Typicky 3. sloupec je X / Lat
    y_col = df.columns[3] # Typicky 4. sloupec je Y / Lon
    
    df['d_x'] = df[x_col] - df[x_col].mean()
    df['d_y'] = df[y_col] - df[y_col].mean()

    # Vykreslení
    plt.figure(figsize=(8, 8))
    plt.scatter(df['d_x'], df['d_y'], alpha=0.5, marker='.', label='Vypočtené epochy')
    plt.axhline(0, color='red', linestyle='--')
    plt.axvline(0, color='red', linestyle='--')
    plt.title(f"Rozptyl polohy L1 (Standardní odchylka: X={df['d_x'].std():.2f}m, Y={df['d_y'].std():.2f}m)")
    plt.xlabel("Odchylka v ose X (m)")
    plt.ylabel("Odchylka v ose Y (m)")
    plt.grid(True)
    plt.axis('equal')
    plt.legend()
    plt.show()