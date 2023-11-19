#**********************************************#
#   Programa Leitor de Tags Chipless de RFID   #
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
from collections import Counter
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
f_minima = 1500000000
f_maxima = 6000000000
y_minima = -60
y_maxima = 20
tag_mais_provavel = None
sinais_rf = []
pasta_principal = '/mnt/d/SpuR_(v2.0)/BD'
BD = 'SpuR_v2.0_BD.csv'
lock = threading.Lock()
num_attempts = 4
leitura_concluida = False

#***********************************************#
#    ID da tag RFID que está sendo Lida no BD   #
#												#
ID = "Teste"									#
#												#
#												#
#***********************************************#  

def sweeper(prob_lvl):
    global f, sinais_rf, leitura_concluida, ID, F1, F2, step, banco_de_dados
    if f < F1 or (prob_lvl is None and leitura_concluida):
        f += step
        return f
    if prob_lvl and not leitura_concluida:
        sinais_rf.append((f, prob_lvl))
        f += step
        if f > F2+1 and not leitura_concluida:
            sinais_rf_tratados = [] 
            for sinal in sinais_rf:
                sinais_rf_tratados.append(tratar_real(*sinal))
            configurar_parametros()
            banco_de_dados = ler_banco_de_dados()
            tag_mais_provavel, comparacoes = identificar_tag_mais_provavel(banco_de_dados, sinais_rf_tratados)
            banco_de_dados_tratados = tratar_banco_de_dados(banco_de_dados, tag_mais_provavel)
            salvar_dados(tag_mais_provavel, sinais_rf_tratados, banco_de_dados)
            criar_tabela_comparacao(comparacoes, tag_mais_provavel)
            plotar_graficos(sinais_rf_tratados, banco_de_dados, tag_mais_provavel, pasta_principal, ID, 'png')
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

def ler_banco_de_dados():
    caminho_arquivo = f'{pasta_principal}/{BD}'
    banco_de_dados = pd.read_csv(caminho_arquivo)
    return banco_de_dados

def identificar_tag_mais_provavel(banco_de_dados, leitura):
    distancias = calcular_distancias(banco_de_dados, leitura)
    if len(distancias) > 0 and len(distancias[0]) > 0:
        tags_com_minimos = [min(distancias, key=lambda x: x[i])[0] for i in range(1, len(distancias[0])) if len(distancias[0]) > i]
        contagem_tags = Counter(tags_com_minimos)
        tag_mais_provavel = contagem_tags.most_common(1)[0][0]
    else:
        tag_mais_provavel = None

    return tag_mais_provavel, distancias

def tratar_banco_de_dados(banco_de_dados, tag_mais_provavel):
    df = pd.DataFrame(banco_de_dados)
    banco_de_dados_tratados = []
    for coluna in df.columns:
        if 'Tag_ID_' in coluna:
            ID_str = coluna.split('_')[-1]
            ID_str = ''.join(filter(str.isdigit, ID_str))
            ID = int(ID_str)
            for index, row in df.iterrows():
                f = row['frequencia']
                prob_lvl = row[coluna]
                if ID == tag_mais_provavel:
                    dado_tratado = tratar_real(f, prob_lvl)
                    banco_de_dados_tratados.append(dado_tratado)
    return banco_de_dados_tratados

def salvar_dados(tag_mais_provavel, sinais_rf_tratados, banco_de_dados):
    pasta_principal = criar_pastas(tag_mais_provavel)
    caminho_arquivo_lido = os.path.join(pasta_principal, 'Tags_Lidas', f'Tag_Mais_Provavel_{tag_mais_provavel}', f'Tag_Lida_{tag_mais_provavel}.csv')
    caminho_arquivo_comparado = os.path.join(pasta_principal, 'Tags_Lidas', f'Tag_Mais_Provavel_{tag_mais_provavel}', f'Tag_Comparada_{tag_mais_provavel}.csv')
    salvar_em_csv(sinais_rf_tratados, caminho_arquivo_lido)
    salvar_em_csv(banco_de_dados, caminho_arquivo_comparado)



def criar_tabela_comparacao(comparacoes, tag_mais_provavel):
    pasta_principal = '/mnt/d/SpuR_(v2.0)/BD'
    df = pd.DataFrame(comparacoes, columns=['Tag', 'Distância Euclidiana', 'Distância Manhattan', 'Distância Chebyshev', 'Correlação'])
    # Convertendo a coluna 'Tag' para numérico
    df['Tag'] = pd.to_numeric(df['Tag'], errors='coerce')
    # Calcula a tag de menor distância para cada modelo
    menor_distancia = df.min()
    # Adiciona a linha de menor distância ao DataFrame
    df = df.append(menor_distancia, ignore_index=True)
    # Salva o DataFrame como um arquivo CSV sem índice
    df.to_csv(f'{pasta_principal}/Tags_Lidas/Tag_Mais_Provavel_{tag_mais_provavel}/tabela_comparacao_{tag_mais_provavel}.csv', index=False)
    # Salva o DataFrame como um arquivo TXT sem índice
    with open(f'{pasta_principal}/Tags_Lidas/Tag_Mais_Provavel_{tag_mais_provavel}/tabela_comparacao_{tag_mais_provavel}.txt', 'w') as f:
        f.write(df.to_string(index=False))
   # Cria e salva a tabela como uma imagem PNG e PDF
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')
    tbl = table(ax, df, cellLoc = 'center', loc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.5)
    ax.set_title(f'Tag mais provável Nº {tag_mais_provavel}')  # Define o título da tabela
    plt.tight_layout()
    plt.savefig(f'{pasta_principal}/Tags_Lidas/Tag_Mais_Provavel_{tag_mais_provavel}/tabela_comparacao_{tag_mais_provavel}.png', dpi=600)
    plt.savefig(f'{pasta_principal}/Tags_Lidas/Tag_Mais_Provavel_{tag_mais_provavel}/tabela_comparacao_{tag_mais_provavel}.pdf')

def plotar_graficos(sinais_rf_tratados, banco_de_dados, tag_mais_provavel, pasta_principal, ID, formato):
    if sinais_rf_tratados:
        df_real = pd.DataFrame(sinais_rf_tratados)
        df_banco = pd.DataFrame(banco_de_dados)
        coluna_banco_mag = f'mag_(Tag_ID_{tag_mais_provavel})'
        plotar_grafico(df_real, df_banco, 'magnitude', coluna_banco_mag, f'Magnitude vs Frequência - Tag Mais Provável {tag_mais_provavel}', 'Magnitude (V)', f'Magnitude_{tag_mais_provavel}', pasta_principal, ID, formato, -1, 1.5, tag_mais_provavel)
        coluna_banco_dbm = 'potencia_dbm'
        df_banco_dbm = converter_para_dbm(df_banco, coluna_banco_mag)
        plotar_grafico(df_real, df_banco_dbm, 'potencia_dbm', coluna_banco_dbm, f'Potência Absoluta vs Frequência- Tag Mais Provável {tag_mais_provavel}', 'Potência Absoluta (dBm)', f'Potencia_dBm_{tag_mais_provavel}', pasta_principal, ID, formato, -40, 20, tag_mais_provavel)

def converter_para_dbm(df, coluna_magnitude):
    mag = df[coluna_magnitude]
    pot_dbm = []
    for magnitude in mag:
        pot = (magnitude**2) / 50
        pot_dbm.append(10 * np.log10(pot * 1000))
    df['potencia_dbm'] = pot_dbm
    return df

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
    plt.rcParams['legend.loc'] = 'lower right'
    plt.rcParams['legend.frameon'] = True
    plt.rcParams['legend.framealpha'] = 0.5
    plt.rcParams['legend.facecolor'] = 'white'
    plt.rcParams['legend.edgecolor'] = 'black'
    plt.rcParams['legend.fontsize'] = 10
    plt.legend(title='Tag ID: {ID}')
    plt.rcParams['legend.title_fontsize'] = 12
           
def plotar_grafico(df1, df2, coluna, coluna_banco, titulo, ylabel, nome_grafico, pasta_principal, ID, formato, y_minimo, y_maximo, tag_mais_provavel):
    fig, axs = plt.subplots()
    formatter = FuncFormatter(format_decimal)
    axs.yaxis.set_major_formatter(formatter)
    axs.plot(df1['frequencia'], df1[coluna], label='Sinal Tratado', color='blue')
    if 'mag_(Tag_ID_{})'.format(tag_mais_provavel) in df2.columns:
        axs.plot(df2['frequencia'], df2[coluna_banco], label='Banco de Dados', color='red')
    axs.set_title(titulo)
    axs.set_xlabel('Frequência (GHz)')
    axs.set_ylabel(ylabel)
    axs.set_xlim([f_minima, f_maxima])
    axs.set_ylim([float(y_minimo), float(y_maximo)])
    axs.legend(title='Legenda')
    caminho_completo = f'{pasta_principal}/Tags_Lidas/Tag_Mais_Provavel_{tag_mais_provavel}'
    save_figure(fig, gerar_pasta_figuras(nome_grafico, formato, caminho_completo, ID), format='png')
    plt.close(fig)

def calcular_potencia_absoluta(magnitude, angle):
    z = magnitude * np.exp(1j * angle)
    pot = (np.real(z)**2 + np.imag(z)**2) / 50
    return pot

def calcular_potencia_dbm(pot):
    if (pot > 0).any():
        pot_dbm = 10 * np.log10(pot * 1000)
        return pot_dbm
    else:
        return None

def calcular_distancias(banco_de_dados, leitura):
    if isinstance(leitura, list):
        leitura = pd.DataFrame(leitura)

    banco_de_dados = banco_de_dados[(banco_de_dados['frequencia'] >= F1) & (banco_de_dados['frequencia'] <= F2)]
    leitura = leitura[(leitura['frequencia'] >= F1) & (leitura['frequencia'] <= F2)]
    distancias = []

    for coluna in banco_de_dados.columns:
        if coluna.startswith('mag_(Tag_ID_'):
            tag_banco = banco_de_dados[coluna]
            if len(banco_de_dados['frequencia']) > 0 and len(tag_banco) > 0:
                f_banco = interpolate.interp1d(banco_de_dados['frequencia'], tag_banco)
                tag_banco_interp = f_banco(leitura['frequencia'])
                #tag_banco_interp = f_banco(banco_de_dados[coluna])
                dist_euclidean = distance.euclidean(leitura['magnitude'], tag_banco_interp)
                dist_manhattan = distance.cityblock(leitura['magnitude'], tag_banco_interp)
                dist_chebyshev = distance.chebyshev(leitura['magnitude'], tag_banco_interp)
                dist_correlation = 1 - pearsonr(leitura['magnitude'], tag_banco_interp)[0]
                distancias.append((coluna[len('mag_(Tag_ID_'):-1], dist_euclidean, dist_manhattan, dist_chebyshev, dist_correlation))
    return distancias

def criar_pastas(tag_mais_provavel):
    import os
    if not all(c.isalnum() or c in '-_' for c in tag_mais_provavel):
        raise ValueError(f"Nome de tag inválido: {tag_mais_provavel}")
    pasta_principal = '/mnt/d/SpuR_(v2.0)/BD'
    if not os.path.isdir(pasta_principal):
        raise FileNotFoundError(f"Caminho não encontrado: {pasta_principal}")
    pastas = ['Tags_Lidas',  f'Tags_Lidas/Tag_Mais_Provavel_{tag_mais_provavel}']
    for pasta in pastas:
        caminho_pasta = os.path.join(pasta_principal, pasta)
        os.makedirs(caminho_pasta, exist_ok=True)
    return pasta_principal


def salvar_em_csv(dados, caminho_arquivo):
    import pandas as pd
    if isinstance(dados, list) and all(isinstance(d, dict) for d in dados):
        df = pd.DataFrame(dados)
    elif isinstance(dados, pd.DataFrame):
        df = dados
    else:
        raise ValueError("Os dados devem ser uma lista de dicionários ou um DataFrame do pandas")
    df.to_csv(caminho_arquivo, index=False)

def format_decimal(x, pos):
    # Converte um número em uma string formatada com duas casas decimais.
    return '{:.2f}'.format(x)

def gerar_pasta_figuras(nome_grafico, formato, caminho_completo, ID):
    caminho_pasta = f'{caminho_completo}'
    os.makedirs(caminho_pasta, exist_ok=True)
    return f'{caminho_pasta}/{nome_grafico}.{formato}'

def save_figure(fig, path, dpi=300, format='png'):
    num_attempts = 3
    for attempt in range(num_attempts):
        fig.savefig(path, dpi=dpi, format=format)
        if os.path.isfile(path):
            break
