#**********************************************#
#  Programa Gravador de Tags Chipless de RFID  #
#					V:2.0					   #
#**********************************************#
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import threading
from matplotlib.ticker import FuncFormatter
from pandas.plotting import table
from scipy.spatial import distance
from scipy.spatial.distance import minkowski, chebyshev
from scipy import interpolate
from scipy.stats import pearsonr
F1 =   78000000
F2 = 6000000000
step =  1000000
f =    70000000
f_minima =   70000000
f_maxima = 6000000000
sinais_rf = []
lock = threading.Lock()
num_attempts = 4
leitura_concluida = False

#***********************************************#
#  ID da tag RFID que está sendo gravada no BD  #
#												#
ID = "6"										#
#												#
#												#
#***********************************************#  

def sweeper(prob_lvl):
    global f, sinais_rf, leitura_concluida, ID, F1, F2, step, pasta_principal
    if f < F1:
        with lock:
            f += step
        return f
    if prob_lvl and not leitura_concluida:
        with lock:
            sinais_rf.append((f, prob_lvl))
            f += step
        if f > F2 and not leitura_concluida:
            with lock:
                sinais_rf_tratados = [] 
                for sinal in sinais_rf:
                    sinais_rf_tratados.append(tratar_real(*sinal))
                configurar_parametros()
                pasta_principal = criar_pastas()
                salvar_dados(sinais_rf_tratados, pasta_principal, ID)
                plotar_graficos(sinais_rf_tratados, pasta_principal, ID, formato='png')
                plotar_graficos(sinais_rf_tratados, pasta_principal, ID, formato='pdf')
                sinais_rf = []
                leitura_concluida = True
                f -= step
    return f

def tratar_real(f, prob_lvl):
    freq = f
    amplitude = prob_lvl
    magnitude = prob_lvl if prob_lvl >= 0 else -prob_lvl
    fase = 0 if prob_lvl >= 0 else np.pi
    potencia_absoluta = calcular_potencia_absoluta(magnitude, fase)
    potencia_dbm = calcular_potencia_dbm(potencia_absoluta)
    return {"frequencia": freq,  "magnitude": magnitude, "potencia_dbm": potencia_dbm}

def criar_pastas():
    pasta_principal = '/mnt/d/SpuR_(v2.0)/BD'
    pastas = ['Figuras', 'S2P', 'Tags_BD']
    for pasta in pastas:
        caminho_pasta = os.path.join(pasta_principal, pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
    return pasta_principal

def save_figure(fig, path, dpi=300, format='png'):
    for attempt in range(num_attempts):
        fig.savefig(path, dpi=dpi, format=format)
        if os.path.isfile(path):
            break

def gerar_pasta_figuras(nome_grafico, formato, pasta_principal, ID):
    caminho_pasta = f'{pasta_principal}/Figuras/Tag_{ID}/{formato}'
    os.makedirs(caminho_pasta, exist_ok=True)
    return f'{caminho_pasta}/{nome_grafico}.{formato}'

def configurar_parametros():
    plt.rcParams['lines.linewidth'] = 2
    plt.rcParams['lines.color'] = 'blue'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.color'] = 'gray'
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['figure.figsize'] = [10, 5]
    plt.rcParams['font.size'] = 14
    plt.rcParams['font.family'] = 'serif'
    plt.rcParams['legend.loc'] = 'lower right'  # Localização da legenda
    plt.rcParams['legend.frameon'] = True  # Habilita ou desabilita o quadro da legenda
    plt.rcParams['legend.framealpha'] = 0.5 # Transparência do quadro da legenda
    plt.rcParams['legend.facecolor'] = 'white'  # Cor de fundo da legenda
    plt.rcParams['legend.edgecolor'] = 'black'  # Cor da borda da legenda
    plt.rcParams['legend.fontsize'] = 10  # Tamanho da fonte da legenda
    plt.legend(title='Tag ID: {ID}')
    plt.rcParams['legend.title_fontsize'] = 12  # Define o tamanho da fonte do título da legenda

def plotar_grafico(df, coluna, titulo, ylabel, legenda, nome_grafico, pasta_principal, ID, formato, y_minimo, y_maximo):
    fig, axs = plt.subplots()
    formatter = FuncFormatter(format_decimal)
    axs.yaxis.set_major_formatter(formatter)
    axs.plot(df['frequencia'], df[coluna], label=legenda)
    axs.set_title(titulo)
    axs.set_xlabel('Frequência (GHz)')
    axs.set_ylabel(ylabel)
    axs.set_xlim([f_minima, f_maxima])
    axs.set_ylim([y_minimo, y_maximo])
    axs.legend(title='Legenda')
    save_figure(fig, gerar_pasta_figuras(nome_grafico, formato, pasta_principal, ID), format=formato)
    plt.close(fig)

def plotar_graficos(sinais_rf_tratados, pasta_principal, ID, formato):
    if sinais_rf_tratados:
        df_real = pd.DataFrame(sinais_rf_tratados)
        plotar_grafico(df_real, 'magnitude', f'Magnitude vs Frequência - Tag ID: {ID}', 'Magnitude (V)', 'Magnitude (V)', f'SpuR_BD_{ID}_mag', pasta_principal, ID, formato, y_minimo=-1, y_maximo=1.5) 
        plotar_grafico(df_real, 'potencia_dbm', f'Potência Absoluta vs Frequência - Tag ID: {ID}', 'Potência Absoluta (dBm)', 'Potência (dBm)', f'SpuR_BD_{ID}_dbm', pasta_principal, ID, formato, y_minimo=-40, y_maximo=20)

def salvar_dados(sinais_rf_tratados, pasta_principal, ID):
    if sinais_rf_tratados:
        df = pd.DataFrame(sinais_rf_tratados)
        caminho_arquivo = f'{pasta_principal}/Tags_BD/Tag_ID_{ID}.csv'
        df.to_csv(caminho_arquivo, index=False)
        arquivo_csv = f'{pasta_principal}/SpuR_v2.0_BD.csv'
        if os.path.exists(arquivo_csv):
            df_existente = pd.read_csv(arquivo_csv, index_col='frequencia')
            df_existente[f'mag_(Tag_ID_{ID})'] = df.set_index('frequencia')['magnitude']
            df_existente = df_existente.sort_index(axis=1)
            df_existente.to_csv(arquivo_csv)
        else:
            df_novo = pd.DataFrame(df.set_index('frequencia')['magnitude'])
            df_novo.columns = [f'mag_(Tag_ID_{ID})']
            df_novo.to_csv(arquivo_csv)
        with open(f'{pasta_principal}/S2P/Tag_ID_{ID}.s2p', 'w') as f:
            f.write(f'!	Parâmetros S - Tag_ID_{ID} \n')
            f.write('#	Hz	S	MA	R	50 \n')
            f.write('!	Freq	magS11	angS11	magS21	angS21	magS12	angS12	magS22	angS22\n')
            for index, row in df.iterrows():
                f.write(f'{row["frequencia"]}	0	0	{row["magnitude"]}	0	0	0	0	0\n')

def format_decimal(x, pos):
    return '{:.2f}'.format(x)

def calcular_potencia_absoluta(magnitude, angle):
    z = magnitude * np.exp(1j * angle)
    pot = (np.real(z)**2 + np.imag(z)**2) / 50
    return pot

def calcular_potencia_dbm(pot):
    if pot > 0:
        pot_dbm = 10 * np.log10(pot * 1000)
        return pot_dbm
    else:
        return None
