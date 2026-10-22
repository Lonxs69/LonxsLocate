"""Mecánica orbital básica para órbitas circulares (modelo esférico de la Tierra)."""

from __future__ import annotations

import math
from dataclasses import dataclass

MU_TIERRA = 398_600.4418  # km^3/s^2, parámetro gravitacional estándar
RADIO_TIERRA = 6_371.0  # km, radio medio
OMEGA_TIERRA = 7.292_115_9e-5  # rad/s, velocidad de rotación sidérea
VELOCIDAD_LUZ = 299_792.458  # km/s


def periodo_orbital(semieje_km: float) -> float:
    """Periodo de una órbita en segundos (tercera ley de Kepler)."""
    return 2 * math.pi * math.sqrt(semieje_km**3 / MU_TIERRA)


def movimiento_medio(semieje_km: float) -> float:
    """Velocidad angular media de la órbita en rad/s."""
    return math.sqrt(MU_TIERRA / semieje_km**3)


@dataclass(frozen=True)
class Satelite:
    """Satélite en órbita circular definido por sus elementos keplerianos."""

    nombre: str
    semieje_km: float
    inclinacion_deg: float
    raan_deg: float
    anomalia_deg: float = 0.0

    @property
    def altitud_km(self) -> float:
        return self.semieje_km - RADIO_TIERRA

    def posicion_eci(self, t: float) -> tuple[float, float, float]:
        """Posición inercial (km) del satélite t segundos después de la época."""
        u = math.radians(self.anomalia_deg) + movimiento_medio(self.semieje_km) * t
        i = math.radians(self.inclinacion_deg)
        raan = math.radians(self.raan_deg)
        cu, su = math.cos(u), math.sin(u)
        cr, sr = math.cos(raan), math.sin(raan)
        a = self.semieje_km
        return (
            a * (cr * cu - sr * su * math.cos(i)),
            a * (sr * cu + cr * su * math.cos(i)),
            a * su * math.sin(i),
        )


def satelite_geo(nombre: str = "GEO Sat", longitud_deg: float = 0.0) -> Satelite:
    """Satélite geoestacionario sobre la longitud indicada."""
    return Satelite(nombre, 42_164.0, 0.0, 0.0, longitud_deg)


def constelacion_walker(
    planos: int,
    sats_por_plano: int,
    semieje_km: float = 7_000.0,
    inclinacion_deg: float = 98.0,
    fase: int = 1,
    escalonada: bool = True,
) -> list[Satelite]:
    """Genera una constelación tipo Walker.

    Con ``escalonada=False`` reproduce la red "no escalonada" del script
    ``Non_Step_Satellite_Network.m``: todos los planos arrancan con el
    mismo desfase, sin escalonamiento entre ellos.
    """
    sats = []
    total = planos * sats_por_plano
    for p in range(planos):
        raan = 360.0 * p / planos
        desfase = 360.0 * fase * p / total if escalonada else 0.0
        for s in range(sats_por_plano):
            anomalia = 360.0 * s / sats_por_plano + desfase
            sats.append(
                Satelite(f"LEO {p + 1}-{s + 1}", semieje_km, inclinacion_deg, raan, anomalia)
            )
    return sats
