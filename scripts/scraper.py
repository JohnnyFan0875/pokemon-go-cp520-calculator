import datetime
import pandas as pd
import requests
import lxml
import os
from io import StringIO

from config import BASESTAT_CSV

def scrape_base_stats():
    """
    Scrapes Pokémon base stats from Bulbapedia and saves cleaned CSV.
    Only scrapes if today's file not present.
    """
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    base_stat_fp = BASESTAT_CSV.format(date=today_str)

    if os.path.exists(base_stat_fp):
        print(f'Base stats already exists at {base_stat_fp}')
        return pd.read_csv(base_stat_fp)

    print('Scraping Pokémon base stats...')
    url = 'https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_base_stats_(GO)'
    r = requests.get(url)
    df = pd.read_html(StringIO(r.text))[0]

    # Select relevant columns and rename as needed
    columns = df.columns.tolist()
    selected_idx = {i: col for i, col in enumerate(columns)
                    if col in ['Pokémon.1', 'HP', 'Attack', 'Defense']}
    df = df.iloc[:, list(selected_idx.keys())]
    new_columns = ['Pokemon' if col.lower().startswith('pok') else col for col in selected_idx.values()]
    df.columns = new_columns

    # Clean Pokemon names
    def clean_name(x):
        return (x.replace('é', 'e')
                    .replace('♀', ' Female')
                    .replace('♂', ' Male')
                    .replace(',', '')
                    .replace(' Forme', ' Form')
                    .replace(' From', ' Form'))
    df['Pokemon'] = df['Pokemon'].apply(clean_name)

    # Save CSV
    df.to_csv(base_stat_fp, index=False)
    print(f'Saved base stats to {base_stat_fp}')

    return df

if __name__ == "__main__":
    scrape_base_stats()
