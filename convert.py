from __future__ import division
from collections import OrderedDict
import pandas as pd 
import copy
import logging 
import argparse

logging.basicConfig(format = u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.NOTSET)

CADRU = 'Cadru didactic'
DISCI = 'Denumire disciplina'
HEADER = ["Denumire post",
"Nume si prenume",
"Functia didactica",
"Titlul stiintific",
"Transa de vechime in invatamantul superior",
"Titular angajat",
"Disciplina",
"Facultatea",
"Cod act",
"Nume act",
"An de studiu",
"Nr serii",
"Nr grupe",
"Nr doct",
"Total OC",
"Total ore curs",
"Curs sem 1",
"Curs sem 2",
"Total ore ls",
"LS sem 1",
"LS sem 2",
"Alte activit.", # hidden column
"Nr sp sem 1",
"Nr sp sem 2",
"Pozitia"]

def filter_by_strict(dataframe, col_name,by):
    return dataframe[dataframe[col_name].str.contains(by)]

def norma_vacanta(dataframe):
    return dataframe[dataframe[CADRU].isnull()]

def grupe_an(grup):
    l = [str(elem) for elem in list(grup["Cod formatiune"])]
    return l

def serii_curs(grup):
    grupe = grupe_an(grup)
    return list(set([str(grupa)[0:2] for grupa in grupe]))

def is_final_sem(grup):
    row = grup.iloc[0]
    sem_terminal_cti = (row["Semestru"] == 2 and row["An de studii"] == 4 and  'CTI' in row["Domeniu"])
    sem_terminal_master_fmi = (row["Semestru"] == 2 and (row["An de studii"] == 3 or row["An de studii"] == 5) and not 'CTI' in row["Domeniu"])
    return sem_terminal_cti or sem_terminal_master_fmi

def cod_act(grup):
    row = grup.iloc[0]
    an_terminal_inf = (row["An de studii"] == 5 or row["An de studii"] == 4) and "INF" in row["Domeniu"]
    if an_terminal_inf:
        return 2
    return 1

def get_nr_sapt(grup):
    if (is_final_sem(grup)):
        return 10
    return 14

def ore_curs_sem(grup, semestru):
    total = 0
    grup = grup[grup['Tip'] == 'C']
    grup = grup[grup['Semestru'] == semestru]
    for index, row in grup.iterrows():
        total += row["Numar ore / saptamana"]
    if not total:
        return ''
    return total

def ore_other_sem(grup, semestru):
    total = 0
    grup = grup[grup['Tip'] != 'C']
    grup = grup[grup['Semestru'] == semestru]
    for index, row in grup.iterrows():
        total += row["Numar ore / saptamana"]
    if not total:
        return ''
    return total

def lect_or_assist(grup):
    if len(grup[grup['Tip'] == 'C']):
        return "Lector"
    return "Asistent"

def create_posturi(grupuri_facultate, domeniu = "CTI", preloaded_values = {}):
    outdat = pd.DataFrame(columns = HEADER)
    for idx, (name, grup) in enumerate(grupuri_facultate):
        d = OrderedDict.fromkeys(HEADER, "")
        if preloaded_values:
            d = copy.deepcopy(preloaded_values)
        d["Denumire post"] = lect_or_assist(grup)
        d["Titular angajat"] = "NU"
        d["Nume si prenume"] = "Vacant"
        d["Disciplina"] = grup["Denumire disciplina"]
        d["Facultatea"] = domeniu
        d["Cod act"] = cod_act(grup)
        #d["Nume act"] = "Licenta"
        d["An de studiu"] = grup["An de studii"]
        d["Nr serii"] = ", ".join(serii_curs(grup))
        grupe = grupe_an(grup)
        d["Nr grupe"] = ", ".join(grupe)
        d["Total OC"] = ""
        d["Total ore curs"] = ""
        d["Curs sem 1"] = ore_curs_sem(grup, 1) 
        d["Curs sem 2"] = ore_curs_sem(grup, 2)
        d["Total ore ls"] = ""
        d["LS sem 1"] = ore_other_sem(grup, 1)
        d["LS sem 2"] = ore_other_sem(grup, 2)
        d["Nr sp sem 1"] = 14
        d["Nr sp sem 2"] = get_nr_sapt(grup)
        d["Pozitia"] = ''
        temp = pd.DataFrame(d)
        outdat = outdat.append(temp)
    outdat = outdat.drop_duplicates()
    return outdat

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", dest = "domeniu", type=str, action='store', default = 'CTI',
                        help="Domeniu / Facultate", choices=['INF', 'CTI', 'MAT'])
    parser.add_argument("-i", type=str, dest = "input", action='store', default = 'input.xlsx',
                        help="Fisier de input")
    parser.add_argument("-o", type=str, dest = "output", action='store', 
                        help="Fisier de output")
    args = parser.parse_args()

    outfis = args.output if args.output else args.domeniu + "_output.xlsx"

    data = pd.read_excel(args.input)
    filtrat = filter_by_strict(data, 'Domeniu', args.domeniu)
    filtrat_vacant = norma_vacanta(filtrat)
    filtrat_vacant.to_excel(args.domeniu + '_vacant.xlsx')
    cti_grupate = filtrat_vacant.groupby(DISCI)
    posturi = create_posturi(cti_grupate, domeniu = args.domeniu)
    posturi.to_excel(outfis, index = False, columns = HEADER)

if __name__ == '__main__':
    main()