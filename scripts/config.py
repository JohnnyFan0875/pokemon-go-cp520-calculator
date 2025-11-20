import os

DATA_FOLDER = './data'
EVOLUTION_CSV = './data/evolution.csv'
MULTIPLIER_CSV = './data/multiplyer.csv'
COLLECTED_CSV = './data/cp{cp}_collected.csv'
BASESTAT_CSV ='./data/base_stat_{date}.csv'

OUTPUT_CP_FOLDER = './output/cp{cp}'
OUTPUT_CP_IV_FOLDER = os.path.join(OUTPUT_CP_FOLDER, 'pokemon_iv')
OUTPUT_ALL_FILE = os.path.join(OUTPUT_CP_FOLDER, 'cp{cp}_all_evolutions.csv')
