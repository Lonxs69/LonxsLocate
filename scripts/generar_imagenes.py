"""Genera las imágenes de docs/img a partir de los datos del proyecto.

    pip install -r scripts/requirements.txt
    python scripts/generar_imagenes.py

Fuentes de datos abiertas (se descargan una sola vez a ~/.cache/lonxslocate):
- Fronteras: Natural Earth 1:10m (dominio público).
- Relieve y batimetría: Terrain Tiles de AWS Open Data (formato terrarium).
"""

from __future__ import annotations

import io
import json
import math
import sys
import urllib.request
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LightSource, LinearSegmentedColormap
from matplotlib.patches import Polygon, Rectangle
from matplotlib.transforms import Affine2D

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from lonxslocate.enlace import buscar_estacion, cargar_estaciones
from lonxslocate.orbita import OMEGA_TIERRA, RADIO_TIERRA, constelacion_walker

SALIDA = RAIZ / "docs" / "img"
CACHE = Path.home() / ".cache" / "lonxslocate"
URL_PAISES = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
    "ne_10m_admin_0_countries.geojson"
)
URL_TILES = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"

# Estilo parecido al de las figuras de MATLAB
plt.rcParams.update(
    {
        "font.family": ["Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.linewidth": 0.6,
        "axes.edgecolor": "#262626",
        "axes.grid": True,
        "grid.color": "#262626",
        "grid.alpha": 0.15,
        "grid.linewidth": 0.5,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "legend.fancybox": False,
        "legend.edgecolor": "#262626",
        "legend.framealpha": 1,
        "figure.facecolor": "white",
    }
)


def _descargar(url: str, destino: Path) -> Path:
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        print(f"Descargando {url}")
        urllib.request.urlretrieve(url, destino)
    return destino


def _cartesianas(lat: float, lon: float, radio: float) -> tuple[float, float, float]:
    la, lo = math.radians(lat), math.radians(lon)
    return (
        radio * math.cos(la) * math.cos(lo),
        radio * math.cos(la) * math.sin(lo),
        radio * math.sin(la),
    )


# --------------------------------------------------------------------------
# 1. Enlace Santo Domingo → LEO → Pedernales (equivale a
#    matlab/Satellite_Connection_Simulation_Chart.m, vista superior X-Y)
# --------------------------------------------------------------------------
def figura_enlace() -> None:
    origen, destino = buscar_estacion("Santo Domingo"), buscar_estacion("Pedernales")
    alt_sat, lat_sat, lon_sat = 600, 18.7, -70.5
    po = _cartesianas(origen.latitud, origen.longitud, RADIO_TIERRA)
    pd = _cartesianas(destino.latitud, destino.longitud, RADIO_TIERRA)
    ps = _cartesianas(lat_sat, lon_sat, RADIO_TIERRA + alt_sat)

    fig, ax = plt.subplots(figsize=(7.0, 5.25), dpi=100)

    # Silueta de la Tierra: malla de sphere(100) proyectada en X-Y
    u = np.linspace(-np.pi / 2, np.pi / 2, 101)
    v = np.linspace(-np.pi, np.pi, 101)
    for lat in u:
        ax.plot(RADIO_TIERRA * np.cos(lat) * np.cos(v), RADIO_TIERRA * np.cos(lat) * np.sin(v),
                color="0.5", lw=0.5, label="_")
    for lon in v:
        ax.plot(RADIO_TIERRA * np.cos(u) * np.cos(lon), RADIO_TIERRA * np.cos(u) * np.sin(lon),
                color="0.5", lw=0.5, label="_")
    ax.plot([], [], color="0.5", lw=0.8, label="Tierra (silueta)")

    th = np.linspace(0, 2 * np.pi, 200)
    r_orb = RADIO_TIERRA + alt_sat
    ax.plot(r_orb * np.cos(th), r_orb * np.sin(th), "k--", lw=1.5, label="Órbita del satélite")
    ax.plot([po[0], ps[0]], [po[1], ps[1]], "r-", lw=2, label="Enlace de subida")
    ax.plot([ps[0], pd[0]], [ps[1], pd[1]], "b-", lw=2, label="Enlace de bajada")
    ax.plot(po[0], po[1], "o", color="#00ff00", mec="#00b000", ms=6,
            label="Santo Domingo (estación base)")
    ax.plot(pd[0], pd[1], "o", color="#ff00ff", mec="#b000b0", ms=6,
            label="Pedernales (estación de bajada)")
    ax.plot(ps[0], ps[1], "o", color="k", ms=6, label="Satélite")

    xs = [po[0], pd[0], ps[0]]
    ys = [po[1], pd[1], ps[1]]
    ax.set_xlim(min(xs) - 650, max(xs) + 1100)
    ax.set_ylim(min(ys) - 650, max(ys) + 420)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title("Satélite en órbita sobre República Dominicana con enlaces de comunicación",
                 fontsize=11, fontweight="bold")
    ax.set_xlabel("X (km)")
    ax.set_ylabel("Y (km)")
    ax.legend(loc="upper right", fontsize=8.5, handlelength=2.2)
    fig.tight_layout()
    fig.savefig(SALIDA / "enlace-santo-domingo-pedernales.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# 2. Mapa de estaciones con relieve y trazas de satélites LEO
# --------------------------------------------------------------------------
LON_MIN, LON_MAX, LAT_MIN, LAT_MAX = -74.6, -67.9, 17.35, 20.35
ZOOM = 8


def _merc(lat):
    lat = np.radians(lat)
    return np.degrees(np.log(np.tan(np.pi / 4 + lat / 2)))


def _tile_xy(lon: float, lat: float) -> tuple[float, float]:
    n = 2**ZOOM
    r = math.radians(lat)
    return (lon + 180) / 360 * n, (1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * n


def _relieve() -> tuple[np.ndarray, tuple[float, float, float, float]]:
    """Mosaico de elevación (m) recortado al área del mapa, en Mercator."""
    from PIL import Image

    x0, y0 = _tile_xy(LON_MIN, LAT_MAX)
    x1, y1 = _tile_xy(LON_MAX, LAT_MIN)
    tx = range(int(x0), int(x1) + 1)
    ty = range(int(y0), int(y1) + 1)
    filas = []
    for y in ty:
        fila = []
        for x in tx:
            ruta = _descargar(URL_TILES.format(z=ZOOM, x=x, y=y), CACHE / f"t{ZOOM}_{x}_{y}.png")
            rgb = np.asarray(Image.open(io.BytesIO(ruta.read_bytes())).convert("RGB"), float)
            fila.append(rgb[..., 0] * 256 + rgb[..., 1] + rgb[..., 2] / 256 - 32768)
        filas.append(np.hstack(fila))
    elev = np.vstack(filas)
    c0, c1 = int((x0 - tx[0]) * 256), int((x1 - tx[0]) * 256)
    f0, f1 = int((y0 - ty[0]) * 256), int((y1 - ty[0]) * 256)
    return elev[f0:f1, c0:c1], (LON_MIN, LON_MAX, float(_merc(LAT_MIN)), float(_merc(LAT_MAX)))


def _colorear(elev: np.ndarray) -> np.ndarray:
    tierra = LinearSegmentedColormap.from_list(
        "tierra",
        [(0.0, "#6f9a5b"), (0.08, "#8fae6a"), (0.22, "#b8b47f"), (0.45, "#a98b62"),
         (0.75, "#8a6e55"), (1.0, "#d9d2c8")],
    )
    mar = LinearSegmentedColormap.from_list(
        "mar", [(0.0, "#2f5f8f"), (0.6, "#5d8fbd"), (0.93, "#8db8d8"), (1.0, "#b3d3e6")]
    )
    rgb_t = tierra(np.clip(elev / 3000, 0, 1))[..., :3]
    rgb_m = mar(np.clip(1 + elev / 6000, 0, 1))[..., :3]
    rgb = np.where((elev > 0)[..., None], rgb_t, rgb_m)
    ls = LightSource(azdeg=315, altdeg=40)
    sombra = ls.hillshade(np.where(elev > 0, elev, 0), vert_exag=0.05, dx=1, dy=1)
    return np.clip(rgb * (0.55 + 0.6 * sombra[..., None]), 0, 1)


def _trazas_sobre_rd() -> list[tuple[np.ndarray, np.ndarray, str, float, float]]:
    """Busca dos satélites de la constelación que pasan sobre RD y devuelve su traza."""
    sats = constelacion_walker(20, 10)

    def latlon(sat, t):
        x, y, z = sat.posicion_eci(t)
        lon = math.degrees(math.atan2(y, x) - OMEGA_TIERRA * t)
        return math.degrees(math.asin(z / math.sqrt(x * x + y * y + z * z))), (lon + 180) % 360 - 180

    objetivos = [(18.75, -70.35), (19.6, -71.9)]
    trazas = []
    for lat_o, lon_o in objetivos:
        mejor = None
        for t in range(0, 6 * 3600, 20):
            for s in sats:
                la, lo = latlon(s, t)
                d = (la - lat_o) ** 2 + (lo - lon_o) ** 2
                if mejor is None or d < mejor[0]:
                    mejor = (d, s, t, la, lo)
        _, s, t, la, lo = mejor
        ts = np.arange(t - 600, t + 600, 5)
        pts = np.array([latlon(s, k) for k in ts])
        trazas.append((pts[:, 1], _merc(pts[:, 0]), s.nombre, lo, float(_merc(la))))
    return trazas


def figura_mapa() -> None:
    elev, extension = _relieve()
    alto = 8.0 * (extension[3] - extension[2]) / (extension[1] - extension[0])
    fig = plt.figure(figsize=(8.0, alto), dpi=110)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(_colorear(elev), extent=extension, origin="upper", interpolation="bilinear")

    paises = json.loads(_descargar(URL_PAISES, CACHE / "ne_10m_paises.geojson").read_text())
    for f in paises["features"]:
        if f["properties"]["ADM0_A3"] not in ("DOM", "HTI", "PRI", "TCA", "CUB"):
            continue
        g = f["geometry"]
        polis = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poli in polis:
            anillo = np.array(poli[0])
            ax.plot(anillo[:, 0], _merc(anillo[:, 1]), color="#3a3a3a", lw=0.6, alpha=0.7)

    for lon, y, nombre, lo, la in _trazas_sobre_rd():
        ax.plot(lon, y, color="#00e5ff", lw=1.6)
        ax.plot(lo, la, "o", ms=6, mfc="none", mec="#00e5ff", mew=1.6)
        ax.plot(lo, la, "o", ms=2.5, color="#1a1a1a")
        ax.text(lo + 0.09, la - 0.05, f"{nombre.replace('LEO', 'LEO Sat')}", color="white",
                fontsize=8, va="top",
                bbox={"boxstyle": "square,pad=0.15", "fc": "#303030", "ec": "none", "alpha": 0.65})

    desplaza = {"Santiago": (0.07, 0.05), "San Francisco de Macorís": (0.07, -0.02),
                "Neiba": (0.07, -0.09), "Jimaní": (-0.07, -0.02), "Comendador": (0.07, 0.04)}
    for e in cargar_estaciones():
        y = float(_merc(e.latitud))
        ax.plot(e.longitud, y, "o", ms=5, color="#f05a1a", mec="#7a2a08", mew=0.6)
        dx, dy = desplaza.get(e.nombre, (0.07, 0.0))
        ax.text(e.longitud + dx, y + dy, e.nombre, color="white", fontsize=8,
                ha="right" if dx < 0 else "left", va="center",
                bbox={"boxstyle": "square,pad=0.15", "fc": "#303030", "ec": "none", "alpha": 0.65})

    ax.text(0.995, 0.005, "Relieve: AWS Terrain Tiles · Fronteras: Natural Earth",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=6, color="#1e1e1e",
            alpha=0.75)
    ax.set_xlim(LON_MIN, LON_MAX)
    ax.set_ylim(extension[2], extension[3])
    ax.axis("off")
    fig.savefig(SALIDA / "estaciones-rd.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# 3. Topología de la red de acceso (equivale a simulaciones/cisco)
# --------------------------------------------------------------------------
def _icono(ax, tipo: str, x: float, y: float, texto: str = "", escala: float = 1.5) -> None:
    azul, gris = "#2f6fa7", "#5b6670"
    n_parches, n_lineas, n_textos = len(ax.patches), len(ax.lines), len(ax.texts)
    if tipo == "router":
        ax.add_patch(Rectangle((x - 0.32, y - 0.08), 0.64, 0.16, fc="#3d7ab8", ec="#1f4466", lw=0.8))
        ax.add_patch(matplotlib.patches.Ellipse((x, y + 0.08), 0.64, 0.16, fc="#6fa3d6",
                                                ec="#1f4466", lw=0.8))
        ax.add_patch(matplotlib.patches.Ellipse((x, y - 0.08), 0.64, 0.16, fc="#3d7ab8",
                                                ec="#1f4466", lw=0.8, zorder=0))
    elif tipo == "switch":
        ax.add_patch(Polygon([(x - 0.35, y - 0.1), (x + 0.3, y - 0.1), (x + 0.38, y + 0.06),
                              (x - 0.27, y + 0.06)], fc="#7fa9cf", ec="#1f4466", lw=0.8))
    elif tipo == "ap":
        ax.add_patch(Rectangle((x - 0.32, y - 0.09), 0.64, 0.14, fc="#9fb4c4", ec=gris, lw=0.8))
        for k in range(-3, 4):
            ax.plot([x + k * 0.08, x + k * 0.08], [y - 0.06, y + 0.02], color=gris, lw=0.6)
    elif tipo == "torre":
        ax.add_patch(Polygon([(x - 0.15, y - 0.3), (x + 0.15, y - 0.3), (x, y + 0.25)],
                             fc="none", ec="#3b4a59", lw=1.2))
        ax.plot([x - 0.1, x + 0.1], [y - 0.12, y - 0.12], color="#3b4a59", lw=0.8)
        ax.plot([x - 0.05, x + 0.05], [y + 0.05, y + 0.05], color="#3b4a59", lw=0.8)
        for r in (0.12, 0.2):
            for s in (-1, 1):
                a = np.linspace(-0.6, 0.6, 20)
                ax.plot(x + s * r * np.cos(a), y + 0.25 + r * np.sin(a), color=azul, lw=0.8)
    elif tipo == "servidor":
        ax.add_patch(Rectangle((x - 0.13, y - 0.28), 0.26, 0.52, fc="#4f6f8a", ec="#22313f", lw=0.8))
        ax.text(x, y - 0.15, "CO", ha="center", va="center", fontsize=8, fontweight="bold",
                color="white")
    elif tipo == "satelite":
        ax.add_patch(Rectangle((x - 0.25, y - 0.12), 0.5, 0.24, fc="#c9dbe8", ec=gris, lw=0.8))
        ax.add_patch(Rectangle((x - 0.19, y - 0.07), 0.38, 0.14, fc="#7fb0d8", ec=gris, lw=0.5))
    elif tipo in ("laptop", "pc", "tablet", "telefono", "impresora"):
        if tipo == "laptop":
            ax.add_patch(Polygon([(x - 0.18, y), (x + 0.18, y), (x + 0.22, y + 0.2),
                                  (x - 0.14, y + 0.2)], fc="#7fa9cf", ec=gris, lw=0.8))
            ax.add_patch(Polygon([(x - 0.24, y - 0.08), (x + 0.2, y - 0.08), (x + 0.18, y),
                                  (x - 0.18, y)], fc="#b8c4ce", ec=gris, lw=0.8))
        elif tipo == "pc":
            ax.add_patch(Rectangle((x - 0.17, y - 0.02), 0.34, 0.22, fc="#7fa9cf", ec=gris, lw=0.8))
            ax.add_patch(Rectangle((x - 0.05, y - 0.1), 0.1, 0.08, fc="#b8c4ce", ec=gris, lw=0.6))
        elif tipo == "tablet":
            ax.add_patch(Polygon([(x - 0.2, y - 0.1), (x + 0.14, y - 0.12), (x + 0.2, y + 0.1),
                                  (x - 0.14, y + 0.12)], fc="#7fa9cf", ec=gris, lw=0.8))
        elif tipo == "telefono":
            ax.add_patch(Polygon([(x - 0.14, y - 0.06), (x + 0.02, y - 0.16), (x + 0.16, y + 0.06),
                                  (x, y + 0.16)], fc="#7fa9cf", ec=gris, lw=0.8))
        else:
            ax.add_patch(Rectangle((x - 0.18, y - 0.08), 0.36, 0.14, fc="#b8c4ce", ec=gris, lw=0.8))
            ax.add_patch(Rectangle((x - 0.12, y + 0.06), 0.24, 0.06, fc="white", ec=gris, lw=0.6))
    t = Affine2D().translate(-x, -y).scale(escala).translate(x, y) + ax.transData
    for artista in ax.patches[n_parches:] + ax.lines[n_lineas:] + ax.texts[n_textos:]:
        artista.set_transform(t)
    if texto:
        ax.text(x, y - 0.32 * escala, texto, ha="center", va="top", fontsize=7.2,
                color="#1a1a1a", linespacing=1.1)


def _puerto(ax, x, y, texto):
    ax.text(x, y, texto, fontsize=7, ha="center", va="center",
            bbox={"boxstyle": "square,pad=0.12", "fc": "white", "ec": "none"})


def figura_cisco() -> None:
    fig = plt.figure(figsize=(14.0, 5.4), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 28)
    ax.set_ylim(0, 10.8)
    ax.axis("off")

    zonas = [
        ((0.15, 3.9), 7.0, 2.6, "#ff5a1f"),
        ((7.7, 4.2), 9.0, 2.9, "#ff9cf5"),
        ((17.0, 6.6), 10.9, 3.6, "#2ef02e"),
        ((17.0, 3.7), 10.9, 2.9, "#ffff8a"),
        ((17.0, 0.2), 10.9, 3.5, "#aefcff"),
    ]
    for (x, y), w, h, c in zonas:
        ax.add_patch(Rectangle((x, y), w, h, fc=c, ec="#333333", lw=0.8, zorder=0))

    def titulo(x, y, t, fs=14):
        ax.text(x, y, t, fontsize=fs, fontweight="bold", ha="center", va="center",
                bbox={"boxstyle": "square,pad=0.2", "fc": "white", "ec": "none"})

    titulo(3.5, 3.0, "Base Station Barahona")
    titulo(12.2, 3.0, "DownLink Pedernales")
    titulo(22.5, 10.3, "PEDERNALES")
    titulo(22.5, 6.85, "OVIEDO")
    titulo(22.5, 3.95, "JUANCHO")

    # Estación base
    _icono(ax, "router", 1.0, 5.2, "1941\nR - BARAHONA")
    _icono(ax, "switch", 3.3, 5.2, "2960-24TT\nS - BARAHONA")
    _icono(ax, "ap", 5.9, 5.25, "AccessPoint-PT\nBS - ANTENA")
    for a, b in ((1.35, 2.9), (3.7, 5.55)):
        ax.plot([a, b], [5.2, 5.2], color="black", lw=1.2, zorder=0)
    _puerto(ax, 2.0, 5.42, "Gig0/0")
    _puerto(ax, 2.7, 5.42, "Fa0/1")
    _puerto(ax, 4.2, 5.42, "Fa0/2")

    # Satélite y enlaces inalámbricos
    _icono(ax, "satelite", 7.6, 9.3)
    titulo(7.6, 8.65, "LEO - SATELITE", fs=11)
    arco = np.linspace(0, np.pi, 100)
    ax.plot(7.25 + 2.9 * np.cos(arco), 6.0 + 3.2 * np.sin(arco), color="#555555", lw=0.8, zorder=0)
    ax.plot([5.95, 7.5], [5.45, 9.15], color="#6a6a6a", lw=2.2, ls=(0, (1, 1)))
    ax.plot([7.75, 9.1], [9.15, 6.1], color="#5f5fd8", lw=2.2, ls=(0, (1, 1)))

    # Downlink
    _icono(ax, "torre", 9.1, 5.75, "Cell-Tower\nAntena DownLink")
    _icono(ax, "servidor", 12.0, 5.5, "Central-Office-Server\nDownLink Station")
    _icono(ax, "router", 15.4, 5.7)
    ax.text(15.4, 5.32, "1941\nR - PEDERNALES", ha="center", va="top", fontsize=7.2)
    ax.plot([9.4, 11.85], [5.5, 5.5], color="#1f3cff", lw=1.4, zorder=0)
    ax.plot([12.15, 15.05], [5.5, 5.7], color="black", lw=1.2, zorder=0)
    _puerto(ax, 10.0, 5.72, "Coax0")
    _puerto(ax, 11.6, 5.95, "Coax0/0")
    _puerto(ax, 12.9, 5.75, "Fa0/0")
    _puerto(ax, 14.5, 5.88, "Fa0/0/0")

    # Comunidades
    comunidades = [
        (8.4, "PEDERNALES", [("laptop", 26.3, 9.6, "Laptop-PT\nLaptop0"),
                              ("telefono", 26.5, 8.4, "SMARTPHONE-PT\nSmartphone0"),
                              ("impresora", 26.2, 7.65, "Printer-PT\nPrinter0")], "Fa0/0/3"),
        (5.2, "OVIEDO", [("pc", 26.2, 5.9, "PC-PT\nPC0"),
                          ("tablet", 26.3, 4.8, "TabletPC-PT\nTablet PC1")], "Fa0/0/1"),
        (1.9, "JUANCHO", [("laptop", 26.3, 2.6, "Laptop-PT\nLaptop1"),
                           ("telefono", 26.5, 1.1, "SMARTPHONE-PT\nSmartphone1")], "Fa0/0/2"),
    ]
    for y, nombre, equipos, puerto in comunidades:
        ax.plot([15.7, 19.3], [5.7, y], color="black", lw=1.2, zorder=0)
        _puerto(ax, 16.5, 5.7 + (y - 5.7) * 0.22, puerto)
        _icono(ax, "servidor", 19.5, y, f"Central-Office-Server\nCO - {nombre}")
        _icono(ax, "torre", 22.9, y + 0.15, f"Cell-Tower\nTower{nombre.title()}")
        ax.plot([19.65, 22.75], [y, y + 0.05], color="#1f3cff", lw=1.4, zorder=0)
        _puerto(ax, 20.6, y + 0.25, "Coax0/0")
        _puerto(ax, 22.4, y + 0.35, "Coax0")
        for tipo, ex, ey, txt in equipos:
            ax.plot([23.05, ex - 0.25], [y + 0.3, ey], color="#5f5fd8", lw=2, ls=(0, (1, 1)),
                    zorder=0)
            _icono(ax, tipo, ex, ey, txt)
        _puerto(ax, 18.75, 5.7 + (y - 5.7) * 0.85 + 0.2, "Fa0/0")

    fig.savefig(SALIDA / "red-acceso-pedernales.png")
    plt.close(fig)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    figura_enlace()
    figura_mapa()
    figura_cisco()
    print(f"Imágenes guardadas en {SALIDA}")


if __name__ == "__main__":
    main()
