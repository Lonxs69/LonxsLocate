"""Simulación de cobertura en el tiempo: ¿hay siempre un satélite visible?"""

from __future__ import annotations

from dataclasses import dataclass

from .enlace import Estacion, geometria
from .orbita import Satelite


@dataclass
class ResultadoCobertura:
    estacion: str
    porcentaje: float
    hueco_maximo_min: float
    visibles_promedio: float


def simular_cobertura(
    estaciones: list[Estacion],
    satelites: list[Satelite],
    duracion_h: float = 24.0,
    paso_s: float = 60.0,
    elevacion_min_deg: float = 10.0,
    rotacion: bool = True,
) -> list[ResultadoCobertura]:
    pasos = int(duracion_h * 3600 / paso_s) + 1
    stats = {e.nombre: {"ok": 0, "suma": 0, "hueco": 0, "max_hueco": 0} for e in estaciones}

    for k in range(pasos):
        t = k * paso_s
        pos_sats = [s.posicion_eci(t) for s in satelites]
        for e in estaciones:
            pe = e.posicion_eci(t, rotacion)
            visibles = sum(1 for ps in pos_sats if geometria(pe, ps)[0] >= elevacion_min_deg)
            st = stats[e.nombre]
            st["suma"] += visibles
            if visibles:
                st["ok"] += 1
                st["hueco"] = 0
            else:
                st["hueco"] += 1
                st["max_hueco"] = max(st["max_hueco"], st["hueco"])

    return [
        ResultadoCobertura(
            nombre,
            100.0 * st["ok"] / pasos,
            st["max_hueco"] * paso_s / 60,
            st["suma"] / pasos,
        )
        for nombre, st in stats.items()
    ]
