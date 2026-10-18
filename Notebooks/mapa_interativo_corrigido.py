import json
from pathlib import Path

import folium
from branca.colormap import LinearColormap
from folium.plugins import GroupedLayerControl

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------
BASE = Path("Mapas/São Paulo")
SAIDA_HTML = BASE / "Mapa Interativo - Histórico Eleitoral - Boulos.html"
SAIDA_INDEX = Path("index.html")  # cópia com o nome exigido pelo GitHub Pages

# True  -> só um ano visível por vez (seleção exclusiva)
# False -> caixas de seleção comuns (pode ligar mais de um ano)
SELECAO_EXCLUSIVA = True

CORES = ["white", "#FEF67C", "#FDD663", "#FCBF49", "#FBA730", "#FA9316", "#F97B00"]

# Cada ano: pasta, nome correto do arquivo, nome antigo (legado), campo de votos e intervalos.
# Os nomes "legado" existem porque o notebook de criação salvou 2018 e 2020_1
# com o sufixo "_2020" por engano.
CAMADAS = [
    {
        "nome": "Mapa de Votos - Boulos - 2018",
        "pasta": "2018/Mapa_Boulos_2018/Geojson",
        "arquivo": "mapa_votos_guilherme_boulos_2018.geojson",
        "legado": "mapa_votos_guilherme_boulos_2020.geojson",
        "campo": "QT_VOTOS_NOMINAIS_VALIDOS",
        "intervalos": [484, 833, 1182, 1531, 1880, 2229, 2578],
    },
    {
        "nome": "Mapa de Votos - Boulos - 2020 - 1º Turno",
        "pasta": "2020/Mapa_Boulos_2020_1/Geojson",
        "arquivo": "mapa_votos_guilherme_boulos_2020_1.geojson",
        "legado": "mapa_votos_guilherme_boulos_2020.geojson",
        "campo": "QT_VOTOS",
        "intervalos": [8689, 12395, 16101, 19807, 23513, 27219, 30925],
    },
    {
        "nome": "Mapa de Votos - Boulos - 2020 - 2º Turno",
        "pasta": "2020/Mapa_Boulos_2020_2/Geojson",
        "arquivo": "mapa_votos_guilherme_boulos_2020_2.geojson",
        "legado": None,
        "campo": "QT_VOTOS",
        "intervalos": [16239, 26733, 37228, 47723, 58218, 68713, 79208],
    },
    {
        "nome": "Mapa de Votos - Boulos - 2022",
        "pasta": "2022/Mapa_Boulos_2022/Geojson",
        "arquivo": "mapa_votos_guilherme_boulos_2022.geojson",
        "legado": None,
        "campo": "QT_VOTOS",
        "intervalos": [4455, 6432, 8410, 10387, 12365, 14342, 16320],
    },
]


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def localizar_geojson(cfg):
    """Retorna o caminho do GeoJSON. Prefere o nome correto (com o ano);
    se só existir o nome antigo, usa-o e avisa."""
    pasta = BASE / cfg["pasta"]
    correto = pasta / cfg["arquivo"]
    if correto.exists():
        return correto
    if cfg["legado"] and (pasta / cfg["legado"]).exists():
        print(f"[aviso] '{cfg['arquivo']}' não encontrado; usando o nome antigo "
              f"'{cfg['legado']}'. Renomeie o arquivo para evitar confusão.")
        return pasta / cfg["legado"]
    raise FileNotFoundError(f"GeoJSON não encontrado: {correto}")


def criar_style_function(colormap, campo):
    # Função-fábrica: cada camada guarda o seu próprio colormap e campo
    # (evita o problema de 'late binding' de lambdas dentro de loops).
    def style(feature):
        return {
            "fillColor": colormap(feature["properties"][campo]),
            "color": "black",
            "weight": 1,
            "fillOpacity": 0.7,
        }
    return style


# ---------------------------------------------------------------------------
# Construção do mapa
# ---------------------------------------------------------------------------
m = folium.Map(location=[-23.5505, -46.6333], tiles="cartodbpositron", zoom_start=10)

camadas_criadas = []
for i, cfg in enumerate(CAMADAS):
    caminho = localizar_geojson(cfg)
    with open(caminho, encoding="utf-8") as f:
        dados = json.load(f)

    iv = cfg["intervalos"]
    colormap = LinearColormap(CORES, vmin=min(iv), vmax=max(iv))

    camada = folium.GeoJson(
        dados,
        style_function=criar_style_function(colormap, cfg["campo"]),
        tooltip=folium.features.GeoJsonTooltip(
            fields=["FIRST_NOME", cfg["campo"]], aliases=["Nome:", "Votos:"]
        ),
        name=cfg["nome"],
        overlay=True,
        show=(i == 0),  # só a primeira (2018) começa visível
    )
    camada.add_to(m)
    camadas_criadas.append(camada)
    print(f"[ok] {cfg['nome']}  <-  {caminho}")

folium.LayerControl(collapsed=False).add_to(m)

if SELECAO_EXCLUSIVA:
    GroupedLayerControl(
        groups={"Eleição": camadas_criadas},
        exclusive_groups=True,
        collapsed=False,
    ).add_to(m)

SAIDA_HTML.parent.mkdir(parents=True, exist_ok=True)
m.save(str(SAIDA_HTML))
m.save(str(SAIDA_INDEX))
print(f"Salvo em: {SAIDA_HTML}\nSalvo em: {SAIDA_INDEX.resolve()}")
