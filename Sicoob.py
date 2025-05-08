import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
import numpy as np
import math
import os

def gerar_grafico_emissao(nome_base='grafico_emissoes_mestrado',
                           caminho=r"C:\Users\Usuário\PycharmProjects\PythonProject\gráfico_emissions_mestrado"):
    # Cria a pasta, se não existir
    os.makedirs(caminho, exist_ok=True)

    # Categorias
    categories = [
        r"Gasolina",
        r"Diesel",
        r"Energia Elétrica",
        r"Cama de Frango",
        r"Palha de Café",
        r"Fertilizante (N)",
        r"Calcário",
        r"Emissão Total"
    ]

    # Valores
    plantio_values = [15.06, 71.37, 10.19, 775.45, 0.00, 311.85, 715.00, 0]
    producao_values = [30.12, 31.54, 10.19, 0.00, 635.04, 1625.40, 476.67, 0]
    plantio_values[-1] = sum(plantio_values[:-1])
    producao_values[-1] = sum(producao_values[:-1])

    y_pos = np.arange(len(categories))
    bar_height = 0.35

    plt.rc('font', family='Times New Roman', size=14)
    fig, ax = plt.subplots(figsize=(12, 7))

    bars1 = ax.barh(y_pos - bar_height/2, producao_values, height=bar_height,
                    color='red', label='Produção')
    bars2 = ax.barh(y_pos + bar_height/2, plantio_values, height=bar_height,
                    color='white', edgecolor='red', hatch='//', label='Plantio')

    def arredondar_1_casa_decimal(val):
        return math.floor(val * 10 + 0.5) / 10

    def format_val(val):
        arredondado = arredondar_1_casa_decimal(val)
        return f'{arredondado:.1f}'.replace('.', ',')

    def format_pct(pct):
        arredondado = arredondar_1_casa_decimal(pct)
        return f'{arredondado:.1f}%'.replace('.', ',')

    total_plantio = plantio_values[-1]
    total_producao = producao_values[-1]
    offset = max(total_plantio, total_producao) * 0.01 + 10

    for i, bar in enumerate(bars1):
        valor = bar.get_width()
        if i != len(categories) - 1 and valor > 0:
            pct = (valor / total_producao) * 100
            label = f'{format_val(valor)} ({format_pct(pct)})' if pct >= 0.1 else f'{format_val(valor)}'
        else:
            label = format_val(valor)
        ax.text(valor + offset, bar.get_y() + bar.get_height()/2,
                label, va='center', fontsize=13, color='black')

    for i, bar in enumerate(bars2):
        valor = bar.get_width()
        if i != len(categories) - 1 and valor > 0:
            pct = (valor / total_plantio) * 100
            label = f'{format_val(valor)} ({format_pct(pct)})' if pct >= 0.1 else f'{format_val(valor)}'
        else:
            label = format_val(valor)
        ax.text(valor + offset, bar.get_y() + bar.get_height()/2,
                label, va='center', fontsize=13, color='black')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.set_xlabel('Emissões (kg CO$_2$eq ha$^{-1}$ ano$^{-1}$)', fontsize=14)
    ax.xaxis.set_major_formatter(ScalarFormatter(useMathText=True))
    ax.xaxis.get_offset_text().set_fontsize(13)
    ax.xaxis.grid(True, linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], fontsize=14, loc='lower right')

    plt.tight_layout()

    # Caminhos
    caminho_jpg = os.path.join(caminho, f"{nome_base}.jpg")
    caminho_pdf = os.path.join(caminho, f"{nome_base}.pdf")

    # Salvar arquivos
    plt.savefig(caminho_jpg, format='jpg', bbox_inches='tight', dpi=300)
    plt.savefig(caminho_pdf, format='pdf', bbox_inches='tight')

    # Mostrar gráfico na tela
    plt.show()

    # Confirmação
    print(f"✅ Gráfico salvo com sucesso:")
    print(f"📄 JPG: {caminho_jpg}")
    print(f"📄 PDF: {caminho_pdf}")

# Executar ao rodar o script
if __name__ == "__main__":
    gerar_grafico_emissao()
