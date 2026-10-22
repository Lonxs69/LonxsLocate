"""Geometría del enlace estación ↔ satélite: elevación, distancia, latencia y pérdidas."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

from .orbita import OMEGA_TIERRA, RADIO_TIERRA, VELOCIDAD_LUZ, Satelite

RUTA_ESTACIONES = Path(__file__).resolve().parent.parent / "data" / "estaciones.csv"


@dataclass(frozen=True)
class Estacion:
    nombre: str
    tipo: str
    region: str
    latitud: float
    longitud: float
    altitud_m: float = 0.0

    def posicion_eci(self, t: float = 0.0, rotacion: bool = True) -> tuple[float, float, float]:
        """Posición inercial (km). Si ``rotacion`` es False la Tierra queda fija,
        igual que en las simulaciones originales de MATLAB."""
        r = RADIO_TIERRA + self.altitud_m / 1000
        lat = math.radians(self.latitud)
        lon = math.radians(self.longitud) + (OMEGA_TIERRA * t if rotacion else 0.0)
        return (
            r * math.cos(lat) * math.cos(lon),
            r * math.cos(lat) * math.sin(lon),
            r * math.sin(lat),
        )


def cargar_estaciones(ruta: Path | str = RUTA_ESTACIONES) -> list[Estacion]:
    with open(ruta, encoding="utf-8") as f:
        return [
            Estacion(
                fila["nombre"],
                fila["tipo"],
                fila["region"],
                float(fila["latitud"]),
                float(fila["longitud"]),
                float(fila.get("altitud_m") or 0),
            )
            for fila in csv.DictReader(f)
        ]


def buscar_estacion(nombre: str, estaciones: list[Estacion] | None = None) -> Estacion:
    estaciones = estaciones if estaciones is not None else cargar_estaciones()
    clave = nombre.strip().lower()
    for e in estaciones:
        if e.nombre.lower() == clave:
            return e
    raise KeyError(f"Estación no encontrada: {nombre}")


def _resta(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _norma(v):
    return math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2)


def geometria(
    pos_estacion: tuple[float, float, float], pos_sat: tuple[float, float, float]
) -> tuple[float, float]:
    """Devuelve (elevación en grados, distancia oblicua en km)."""
    d = _resta(pos_sat, pos_estacion)
    distancia = _norma(d)
    cenit = _norma(pos_estacion)
    seno_el = sum(d[k] * pos_estacion[k] for k in range(3)) / (distancia * cenit)
    return math.degrees(math.asin(max(-1.0, min(1.0, seno_el)))), distancia


def elevacion(est: Estacion, sat: Satelite, t: float = 0.0, rotacion: bool = True) -> float:
    return geometria(est.posicion_eci(t, rotacion), sat.posicion_eci(t))[0]


def latencia_ms(distancia_km: float) -> float:
    """Retardo de propagación en un sentido, en milisegundos."""
    return distancia_km / VELOCIDAD_LUZ * 1000


def perdida_espacio_libre_db(distancia_km: float, frecuencia_mhz: float) -> float:
    """FSPL (Free Space Path Loss) en dB."""
    return 20 * math.log10(distancia_km) + 20 * math.log10(frecuencia_mhz) + 32.44


def radio_huella_km(altitud_km: float, elevacion_min_deg: float = 10.0) -> float:
    """Radio sobre la superficie del área que ve al satélite con al menos
    ``elevacion_min_deg`` grados de elevación."""
    eps = math.radians(elevacion_min_deg)
    angulo_central = math.acos(RADIO_TIERRA * math.cos(eps) / (RADIO_TIERRA + altitud_km)) - eps
    return RADIO_TIERRA * angulo_central


def satelite_sobre(lat: float, lon: float, altitud_km: float, nombre: str = "SAT") -> tuple:
    """Posición fija de un satélite sobre un punto (como en
    ``Satellite_Connection_Simulation_Chart.m``)."""
    return Estacion(nombre, "sat", "", lat, lon, altitud_km * 1000).posicion_eci(rotacion=False)
