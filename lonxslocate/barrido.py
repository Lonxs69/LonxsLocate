"""Barrido de configuraciones de constelación.

Cada configuración se evalúa de forma independiente, así que el barrido se
puede repartir en procesos locales o en funciones AWS Lambda (ver ``aws/``).
"""

from __future__ import annotations

import itertools
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .cobertura import simular_cobertura
from .enlace import RUTA_ESTACIONES, cargar_estaciones
from .orbita import RADIO_TIERRA, constelacion_walker

PLANOS = [6, 8, 10, 12, 15, 20]
SATS_POR_PLANO = [4, 6, 8, 10, 12]
ALTITUDES_KM = [550, 800, 1200]


def generar_configuraciones(
    planos: list[int] = PLANOS,
    sats_por_plano: list[int] = SATS_POR_PLANO,
    altitudes_km: list[float] = ALTITUDES_KM,
    inclinacion_deg: float = 98.0,
    horas: float = 24.0,
    paso_s: float = 120.0,
) -> list[dict]:
    return [
        {
            "id": f"p{p}-s{s}-h{int(h)}",
            "planos": p,
            "sats_por_plano": s,
            "altitud_km": h,
            "inclinacion_deg": inclinacion_deg,
            "horas": horas,
            "paso_s": paso_s,
        }
        for p, s, h in itertools.product(planos, sats_por_plano, altitudes_km)
    ]


def evaluar_configuracion(config: dict, ruta_estaciones: Path | str = RUTA_ESTACIONES) -> dict:
    """Simula una configuración y devuelve sus métricas para todas las estaciones."""
    sats = constelacion_walker(
        config["planos"],
        config["sats_por_plano"],
        semieje_km=RADIO_TIERRA + config["altitud_km"],
        inclinacion_deg=config.get("inclinacion_deg", 98.0),
    )
    resultados = simular_cobertura(
        cargar_estaciones(ruta_estaciones),
        sats,
        duracion_h=config.get("horas", 24.0),
        paso_s=config.get("paso_s", 120.0),
        elevacion_min_deg=config.get("elevacion_min_deg", 10.0),
    )
    peor = min(resultados, key=lambda r: r.porcentaje)
    return {
        **config,
        "total_satelites": len(sats),
        "cobertura_min_pct": round(peor.porcentaje, 2),
        "cobertura_media_pct": round(sum(r.porcentaje for r in resultados) / len(resultados), 2),
        "hueco_maximo_min": max(r.hueco_maximo_min for r in resultados),
        "peor_estacion": peor.estacion,
        "visibles_promedio": round(sum(r.visibles_promedio for r in resultados) / len(resultados), 2),
    }


def barrido_local(configs: list[dict], procesos: int | None = None) -> list[dict]:
    with ProcessPoolExecutor(max_workers=procesos) as pool:
        return list(pool.map(evaluar_configuracion, configs))


def mejores(resultados: list[dict], cobertura_objetivo: float = 99.9, n: int = 5) -> list[dict]:
    """Configuraciones que cumplen el objetivo, de la más barata a la más cara.

    Se desempata por altitud más baja (menor latencia) y luego por más
    satélites visibles en promedio (más redundancia).
    """
    validas = [r for r in resultados if r["cobertura_min_pct"] >= cobertura_objetivo]
    validas.sort(key=lambda r: (r["total_satelites"], r["altitud_km"], -r["visibles_promedio"]))
    return validas[:n]
