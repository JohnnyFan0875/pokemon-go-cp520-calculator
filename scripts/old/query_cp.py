import os
import sys
import pandas as pd
import requests
import argparse
import datetime
import time



def get_parser():

    parser = argparse.ArgumentParser()
    parser.add_argument('--cp',type=int,required=True,help='CP value to query')
    args = parser.parse_args()

    return args



def query_cp(): #via pd.read_html

    start_time = time.time()
    print('Start crawling cp online')

    base_stat_fp = os.path.join(script_path,'base_stat_%s.csv'%(datetime.datetime.now().strftime("%Y%m%d")))
    
    if not os.path.exists(base_stat_fp):
        url = 'https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_base_stats_(GO)'
        r = requests.get(url)
        df_poke_stat = pd.read_html(r.text)[0]

        li_column = df_poke_stat.columns.tolist()
        d_idx = {li_column.index(i):i for i in li_column if any(j in i.lower() for j in ['pok','hp','attack','defense'])}
        df_poke_stat = df_poke_stat.iloc[:,list(d_idx.keys())]
        li_column_new = ['Pokemon' if i.lower().startswith('pok') else i for i in d_idx.values()]
        df_poke_stat.columns = li_column_new
        df_poke_stat['Pokemon'] = df_poke_stat['Pokemon'].apply(lambda x: x.replace('é','e').replace('♀',' Female').replace('♂',' Male').replace(',','').replace(' Forme',' Form').replace(' From',' Form'))

        df_poke_stat.to_csv(base_stat_fp, index=False)

    else:
        df_poke_stat = pd.read_csv(os.path.join(script_path,'base_stat_%s.csv'%(datetime.datetime.now().strftime("%Y%m%d"))))

    print('Start crawling cp online --- complete. Total spent %.2fs for this step.'%(time.time()-start_time))
    return df_poke_stat



def check_data():

    start_time = time.time()
    print('Start checking data')

    li_poke_name = df_poke_stat.values.tolist()
    li_poke_name = [i[0] for i in li_poke_name if i[0] != '']
    
    d_evo = dict()
    with open(evolution_fp,'r',encoding='utf-8') as evo_input:
        for line in evo_input.readlines():
            line = line.strip()
            for element in line.split(','):
                if element != '':
                    d_evo[element] = [i for i in line.split(',') if i != '']
    li_evo = sorted(dict.fromkeys(list(d_evo.keys())))

    collected_fp = os.path.join(script_path,f'cp{args.cp}_collected.csv')
    if os.path.exists(collected_fp):
        with open(collected_fp,'r',encoding='utf-8') as collect_input:
            li_collect = [i.split(',')[0] for i in collect_input.read().strip().split('\n')]
    else:
        li_collect = list()

    check = False
    for name in li_poke_name:
        if name not in li_evo:
            print(name + ' in base_stat.csv, not in evolution.csv')
            check = True
    for name in li_evo:
        if name not in li_poke_name:
            print(name + ' in evolution.csv, not in base_stat.csv')
            check = True

    if check:
        sys.exit('Please modify csv first. Program stop.')
    else:
        with open(os.path.join(script_path,f'cp{args.cp}_collected.csv'),'a',encoding='utf-8') as collect_output:
            for name in li_poke_name:
                if name not in li_collect:
                    collect_output.write(f'\n{name},NO')

    print('Start checking data --- complete. Total spent %.2fs for this step.'%(time.time()-start_time))
    return d_evo, li_poke_name
    


def create_cp_file():

    start_time = time.time()
    print('Start creating cp file')

    d_multiplyer = dict()
    with open(os.path.join(script_path,'multiplyer.txt'),'r',encoding='utf-8') as multiplyer_input:
        for line in multiplyer_input.readlines():
            d_multiplyer[line.split('\t')[0]] =  line.split('\t')[1].strip()

    os.makedirs(os.path.join(script_path,'cp'+str(args.cp)),exist_ok=True)
    
    for _, row in df_poke_stat.iterrows():
        name, hp, attack, defense = [row[i] for i in ['Pokemon','HP','Attack','Defense']]
        poke_cp_file = os.path.join(script_path,'cp'+str(args.cp),'cp%s_%s.csv'%(str(args.cp),name))
        if not os.path.exists(poke_cp_file):
                        
            with open(poke_cp_file,'w',encoding='utf-8') as cp_output:
                stat_li = [(ATTACK,DEFENSE,HP,level) for ATTACK in range(16) for DEFENSE in range(16) for HP in range(16) for level in d_multiplyer]
                for stat in stat_li:
                    cp = ((attack+stat[0])*(defense+stat[1])**0.5*(hp+stat[2])**0.5*float(d_multiplyer[stat[3]])**2)/10
                    cp_str = str(cp).split('.')[0]
                    if cp_str == str(args.cp):
                        cp_output.write(','.join([name,'LV'+stat[3]] + [str(i) for i in list(stat)[:3]] + ['cp'+str(args.cp)]) + '\n')

            print(name + ' cp' + str(args.cp) + ' file created.')

    print('Start creating cp file --- complete. Total spent %.2fs for this step.'%(time.time()-start_time))
    return d_multiplyer



def create_evolution_cp_file():

    start_time = time.time()
    print('Start creating evolution cp file')

    for name in li_poke_name:
        
        cp_fp = os.path.join(script_path,f'cp{args.cp}',f'cp{args.cp}_{name}.csv')
        cp_evo_fp = cp_fp.replace('.csv','_evo.txt')

        if not os.path.exists(cp_evo_fp):
            with open(cp_fp,'r',encoding='utf-8') as f_input, open(cp_evo_fp,'w',encoding='utf-8') as f_output:
                for line in f_input.readlines():
                    level = line.split(',')[1]
                    attack, defense, hp = [int(i) for i in line.split(',')[2:5]]

                    for idx, element in enumerate(d_evo[name]):
                        base_attack = int(df_poke_stat.loc[df_poke_stat['Pokemon']==element,'Attack'].iloc[0])
                        base_defense = int(df_poke_stat.loc[df_poke_stat['Pokemon']==element,'Defense'].iloc[0])
                        base_hp = int(df_poke_stat.loc[df_poke_stat['Pokemon']==element,'HP'].iloc[0])
                        cp = ((base_attack+attack)*(base_defense+defense)**0.5*(base_hp+hp)**0.5*float(d_multiplyer[level.replace('LV','')])**2)/10
                        cp_str = str(cp).split('.')[0]
                        if idx == 0:
                            f_output.write(f'{element}({attack}-{defense}-{hp})({level})_{element}({cp_str})')
                        else:
                            f_output.write(f'_{element}({cp_str})')
                    f_output.write('\n')

            print(name + ' cp' + str(args.cp) + ' evolution file created.')

    print('Start creating evolution cp file --- complete. Total spent %.2fs for this step.'%(time.time()-start_time))
                    


def create_final_file():

    start_time = time.time()
    print('Start creating final file')

    with open(os.path.join(script_path,f'cp{args.cp}_collected.csv'),'r',encoding='utf-8') as f_input,\
         open(os.path.join(script_path,f'cp{args.cp}_All.txt'),'w',encoding='utf-8') as f_output1,\
         open(os.path.join(script_path,f'cp{args.cp}_NonCollected.txt'),'w',encoding='utf-8') as f_output2:
        
        li_collect = [i.split(',')[0] for i in f_input.read().strip().split('\n') if i.split(',')[1].strip() == 'YES']

        li_all, li_noncollected = list(), list()
        for name in li_poke_name:
            with open(os.path.join(script_path,f'cp{args.cp}',f'cp{args.cp}_{name}_evo.txt'),'r',encoding='utf-8') as f_input2:
                for line in f_input2.readlines():
                    li_all.append(line.strip())
                    if name not in li_collect:
                        li_noncollected.append(line.strip())

        li_all = sorted(list(dict.fromkeys(li_all)))
        li_noncollected = sorted(list(dict.fromkeys(li_noncollected)))

        f_output1.write('\n'.join(li_all))
        f_output2.write('\n'.join(li_noncollected))

    print('Start creating final file --- complete. Total spent %.2fs for this step.'%(time.time()-start_time))



if __name__ == "__main__":

    start_time = time.time()
    print('Start pokemon go cp query pipeline')

    script_path = os.path.dirname(os.path.abspath(__file__))
    evolution_fp = os.path.join(script_path,'evolution.csv')

    args = get_parser()

    df_poke_stat = query_cp()

    d_evo, li_poke_name = check_data()

    d_multiplyer = create_cp_file()

    create_evolution_cp_file()

    create_final_file()

    print('Start pokemon go cp query pipeline --- complete. Total spent %.2fs for this program.'%(time.time()-start_time))


