import os
import sys
import argparse
import itertools
import pandas as pd
import json
import datetime
import csv
from config import *


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cp', type=int, required=True, help='CP value to query')
    return parser.parse_args()


def load_base_stats():
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    base_stat_fp = BASESTAT_CSV_TEMPLATE.format(date=today_str)
    if not os.path.exists(base_stat_fp):
        sys.exit(f"Base stats CSV not found at {base_stat_fp}, please run scraper first.")
    print(f"Loading base stats from {base_stat_fp}")
    return pd.read_csv(base_stat_fp)


def check_data_consistency(df_stat, cp_val):
    print("Checking data consistency...")

    poke_names = df_stat['Pokemon'].tolist()

    d_evo = {}
    with open(EVOLUTION_CSV, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            items = [e for e in line.split(',') if e]
            for item in items:
                if item not in d_evo:
                    d_evo[item] = []
                d_evo[item].append(items)

    evo_names = sorted(set(d_evo.keys()))
    collect_names = []
    if os.path.exists(COLLECTED_CSV_TEMPLATE.format(cp=cp_val)):
        with open(COLLECTED_CSV_TEMPLATE.format(cp=cp_val), 'r', encoding='utf-8') as f:
            collect_names = [line.split(',')[0] for line in f.read().strip().split('\n')]

    errors = False
    for name in poke_names:
        if name not in d_evo:
            print(f"Warning: '{name}' in base stats but not in evolution.csv")
            errors = True
    for name in evo_names:
        if name not in poke_names:
            print(f"Warning: '{name}' in evolution.csv but not in base stats")
            errors = True
    for name in collect_names:
        if name not in poke_names:
            print(f"Warning: '{name}' in collected.csv but not in base stats")
            errors = True
    for name in poke_names:
        if name not in collect_names:
            print(f"Warning: '{name}' in base stats but not in collected.csv")
            errors = True

    if errors:
        sys.exit("Data inconsistency detected. Please correct CSV files before proceeding.")

    print(f"Data consistency check completed.")
    return d_evo


def load_multiplier():
    with open(MULTIPLIER_CSV, 'r', encoding='utf-8') as f:
        multiplier = {line.split(',')[0]: line.split(',')[1] for line in f.readlines()}
    return multiplier


def calculate_cp(attack, defense, hp, attack_iv, defense_iv, hp_iv, multiplier):
    cp = ((attack + attack_iv) * (defense + defense_iv)**0.5 * (hp + hp_iv)**0.5 * multiplier**2) / 10
    return int(cp)


def create_cp_files(df_stat, d_multiplier, cp_val):
    print(f"Creating CP files for CP={cp_val}...")
    output_folder = OUTPUT_CP_IV_FOLDER_TEMPLATE.format(cp=cp_val)
    os.makedirs(output_folder, exist_ok=True)
    
    for _, row in df_stat.iterrows():
        name = row['Pokemon']
        hp = row['HP']
        attack = row['Attack']
        defense = row['Defense']
        
        cp_file_path = os.path.join(output_folder, f"cp{cp_val}_{name}.csv")
        if os.path.exists(cp_file_path):
            continue  

        cp_entries = []
        iv_ranges = range(16)
        for attack_iv, defense_iv, hp_iv, (level, multiplier_str) in itertools.product(
            iv_ranges, iv_ranges, iv_ranges, d_multiplier.items()
        ):
            cp_int = calculate_cp(
                attack, defense, hp, attack_iv, defense_iv, hp_iv, float(multiplier_str)
            )
            if cp_int == cp_val:
                cp_entries.append(','.join([name, f"LV{level}", str(attack_iv), str(defense_iv), str(hp_iv), str(cp_int)]))

        with open(cp_file_path, 'w', encoding='utf-8') as f:
            f.write(','.join(['Name', 'Level', 'Attack_IV', 'Defense_IV', 'HP_IV', 'CP']) + '\n')
            f.write('\n'.join(cp_entries))

        print(f"Created CP file: {cp_file_path}")

    print(f"CP file creation completed.")

def create_evolution_cp_file(d_evo, df_stat, d_multiplier, cp_val):
    print(f"Creating evolution CP CSV for CP={cp_val}...")

    with open(COLLECTED_CSV_TEMPLATE.format(cp=cp_val), 'r', encoding='utf-8') as f:
        collected = {i.split(',')[0]: i.split(',')[1].strip() for i in f.read().strip().split('\n')}

    output_file_path = OUTPUT_ALL_FILE_TEMPLATE.format(cp=cp_val)

    with open(output_file_path, 'w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out)
        writer.writerow([
            "Pokemon", "CP", "Level", "IV_Attack", "IV_Defense", "IV_HP",
            "Evolution(CP)", "Collected"
        ])

        for poke_name in df_stat['Pokemon']:

            cp_file_folder = OUTPUT_CP_IV_FOLDER_TEMPLATE.format(cp=cp_val)
            cp_file_path = os.path.join(cp_file_folder, f"cp{cp_val}_{poke_name}.csv")
            if not os.path.exists(cp_file_path):
                continue

            with open(cp_file_path, 'r', encoding='utf-8') as f:
                cp_entries = f.read().strip().split('\n')[1:]  # Skip header

            for cp_entry in cp_entries:
                _, level, attack_iv, defense_iv, hp_iv, cp_int = cp_entry.split(',')

                cp_val_int = int(cp_int)
                attack_iv = int(attack_iv)
                defense_iv = int(defense_iv)
                hp_iv = int(hp_iv)

                evo_paths = d_evo.get(poke_name, [])

                # Handle Pokémon that do not evolve
                if not evo_paths:
                    base_pokemon = poke_name
                    evo_chain_str = f"{poke_name}({cp_val_int})"
                    writer.writerow([
                        poke_name, cp_val_int, level, attack_iv, defense_iv, hp_iv,
                        base_pokemon, evo_chain_str
                    ])
                    continue

                for evo_path in evo_paths:

                    evo_chain = []
                    
                    for evo_poke in evo_path:

                        evo_stats = df_stat.loc[df_stat['Pokemon'] == evo_poke]
                        evo_base_attack = int(evo_stats['Attack'].values[0])
                        evo_base_defense = int(evo_stats['Defense'].values[0])
                        evo_base_hp = int(evo_stats['HP'].values[0])
                        cp_calc = calculate_cp(
                            evo_base_attack, evo_base_defense, evo_base_hp,
                            int(attack_iv), int(defense_iv), int(hp_iv),
                            float(d_multiplier[level.replace('LV', '')])
                        )
                        evo_chain.append(f"{evo_poke}({cp_calc})")
                    
                    evo_chain_str = '-'.join(evo_chain)

                    writer.writerow([
                        poke_name, cp_val_int, level, attack_iv, defense_iv, hp_iv,
                        evo_chain_str, collected[poke_name]
                    ])

    print("CSV file creation completed.")

if __name__ == "__main__":
    args = parse_args()
    df_stats = load_base_stats()
    d_evo = check_data_consistency(df_stats, args.cp)
    d_multiplier = load_multiplier()
    create_cp_files(df_stats, d_multiplier, args.cp)
    create_evolution_cp_file(d_evo, df_stats, d_multiplier, args.cp)
