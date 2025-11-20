import os

DATA_FOLDER = './data'
EVOLUTION_CSV = './data/evolution.csv'
MULTIPLIER_CSV = './data/multiplyer.csv'
COLLECTED_CSV_TEMPLATE = './data/cp{cp}_collected.csv'
BASESTAT_CSV_TEMPLATE ='./data/base_stat_{date}.csv'

OUTPUT_CP_FOLDER_TEMPLATE = './output/cp{cp}'
OUTPUT_CP_IV_FOLDER_TEMPLATE = os.path.join(OUTPUT_CP_FOLDER_TEMPLATE, 'pokemon_iv')
OUTPUT_CP_EVOLUTION_FOLDER_TEMPLATE = os.path.join(OUTPUT_CP_FOLDER_TEMPLATE, 'pokemon_evolution')
OUTPUT_ALL_FILE_TEMPLATE = os.path.join(OUTPUT_CP_FOLDER_TEMPLATE, 'cp{cp}_all_evolutions.csv')
