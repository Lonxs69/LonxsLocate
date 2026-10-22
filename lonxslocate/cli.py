"""Interfaz de línea de comandos: ``python -m lonxslocate <comando>``."""

from __future__ import annotations

import argparse

from . import __version__
from .cobertura import simular_cobertura
from .enlace import (
    buscar_estacion,
    cargar_estaciones,
    geometria,
    latencia_ms,
    perdida_espacio_libre_db,
    radio_huella_km,
    satelite_sobre,
)
from .orbita import RADIO_TIERRA, constelacion_walker, periodo_orbital, satelite_geo


def _tabla(encabezados: list[str], filas: list[list]) -> str:
    anchos = [max(len(str(x)) for x in col) for col in zip(encabezados, *filas)]

    def linea(fila):
        return "  ".join(str(x).ljust(a) for x, a in zip(fila, anchos))

    return "\n".join([linea(encabezados), "  ".join("-" * a for a in anchos), *map(linea, filas)])


def cmd_estaciones(args) -> None:
    filas = [
        [e.nombre, e.tipo, e.region, f"{e.latitud:.4f}", f"{e.longitud:.4f}", int(e.altitud_m)]
        for e in cargar_estaciones()
        if args.tipo in (None, e.tipo)
    ]
    print(_tabla(["Estación", "Tipo", "Región", "Lat", "Lon", "Alt (m)"], filas))


def cmd_enlace(args) -> None:
    origen = buscar_estacion(args.origen)
    destino = buscar_estacion(args.destino)
    pos_sat = satelite_sobre(args.sat_lat, args.sat_lon, args.altitud)

    el_up, d_up = geometria(origen.posicion_eci(rotacion=False), pos_sat)
    el_dn, d_dn = geometria(destino.posicion_eci(rotacion=False), pos_sat)

    print(f"Enlace {origen.nombre} → satélite ({args.altitud:.0f} km) → {destino.nombre}\n")
    print(
        _tabla(
            ["Tramo", "Elevación", "Distancia", "Latencia", f"FSPL @ {args.frecuencia:g} MHz"],
            [
                ["Subida", f"{el_up:.1f}°", f"{d_up:,.0f} km", f"{latencia_ms(d_up):.2f} ms",
                 f"{perdida_espacio_libre_db(d_up, args.frecuencia):.1f} dB"],
                ["Bajada", f"{el_dn:.1f}°", f"{d_dn:,.0f} km", f"{latencia_ms(d_dn):.2f} ms",
                 f"{perdida_espacio_libre_db(d_dn, args.frecuencia):.1f} dB"],
            ],
        )
    )
    total = latencia_ms(d_up + d_dn)
    print(f"\nLatencia extremo a extremo: {total:.2f} ms  (ida y vuelta: {2 * total:.2f} ms)")
    if min(el_up, el_dn) < 10:
        print("Aviso: elevación por debajo de 10°, el enlace sería poco fiable.")

    geo = satelite_sobre(0.0, args.sat_lon, 42_164.0 - RADIO_TIERRA)
    d_geo = geometria(origen.posicion_eci(rotacion=False), geo)[1] + geometria(
        destino.posicion_eci(rotacion=False), geo
    )[1]
    print(f"Comparación con GEO en la misma longitud: {latencia_ms(d_geo):.1f} ms")


def cmd_huella(args) -> None:
    filas = []
    for alt in args.altitudes:
        semieje = RADIO_TIERRA + alt
        filas.append(
            [
                f"{alt:,.0f} km",
                f"{periodo_orbital(semieje) / 60:.1f} min",
                f"{radio_huella_km(alt, args.elevacion):,.0f} km",
                f"{latencia_ms(alt):.2f} ms",
            ]
        )
    print(f"Elevación mínima: {args.elevacion:g}°\n")
    print(_tabla(["Altitud", "Periodo", "Radio de huella", "Latencia al cénit"], filas))


def cmd_cobertura(args) -> None:
    estaciones = [e for e in cargar_estaciones() if args.tipo in (None, e.tipo)]
    sats = constelacion_walker(
        args.planos,
        args.sats,
        semieje_km=RADIO_TIERRA + args.altitud,
        inclinacion_deg=args.inclinacion,
        escalonada=not args.no_escalonada,
    )
    if args.geo:
        sats.append(satelite_geo(longitud_deg=-70.0))

    modo = "no escalonada" if args.no_escalonada else "escalonada"
    print(
        f"Constelación {modo}: {args.planos} planos × {args.sats} satélites = {len(sats)} en total"
        f" | {args.altitud:g} km, {args.inclinacion:g}° | {args.horas:g} h, paso {args.paso:g} s"
        f" | rotación terrestre: {'no' if args.sin_rotacion else 'sí'}\n"
    )
    resultados = simular_cobertura(
        estaciones, sats, args.horas, args.paso, args.elevacion, rotacion=not args.sin_rotacion
    )
    print(
        _tabla(
            ["Estación", "Cobertura", "Hueco máx.", "Visibles (prom.)"],
            [
                [r.estacion, f"{r.porcentaje:.1f} %", f"{r.hueco_maximo_min:.0f} min",
                 f"{r.visibles_promedio:.1f}"]
                for r in resultados
            ],
        )
    )
    peor = min(resultados, key=lambda r: r.porcentaje)
    print(f"\nPeor estación: {peor.estacion} ({peor.porcentaje:.1f} %)")


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="lonxslocate",
        description="Diseño y análisis de redes satelitales LEO/GEO para República Dominicana.",
    )
    p.add_argument("--version", action="version", version=f"lonxsLocate {__version__}")
    sub = p.add_subparsers(dest="comando", required=True)

    s = sub.add_parser("estaciones", help="lista las estaciones terrenas")
    s.add_argument("--tipo", choices=["uplink", "downlink"])
    s.set_defaults(func=cmd_estaciones)

    s = sub.add_parser("enlace", help="calcula el enlace estación → satélite → estación")
    s.add_argument("--origen", default="Santo Domingo")
    s.add_argument("--destino", default="Pedernales")
    s.add_argument("--altitud", type=float, default=600, help="altitud del satélite en km")
    s.add_argument("--sat-lat", type=float, default=18.7)
    s.add_argument("--sat-lon", type=float, default=-70.5)
    s.add_argument("--frecuencia", type=float, default=12_000, help="MHz (por defecto banda Ku)")
    s.set_defaults(func=cmd_enlace)

    s = sub.add_parser("huella", help="periodo y área de cobertura según la altitud")
    s.add_argument("altitudes", nargs="*", type=float, default=[500, 600, 1200, 2000, 35_786])
    s.add_argument("--elevacion", type=float, default=10)
    s.set_defaults(func=cmd_huella)

    s = sub.add_parser("cobertura", help="simula la cobertura de una constelación en el tiempo")
    s.add_argument("--planos", type=int, default=20)
    s.add_argument("--sats", type=int, default=10, help="satélites por plano")
    s.add_argument("--altitud", type=float, default=629, help="km (semieje 7000 km)")
    s.add_argument("--inclinacion", type=float, default=98)
    s.add_argument("--horas", type=float, default=24)
    s.add_argument("--paso", type=float, default=60, help="segundos")
    s.add_argument("--elevacion", type=float, default=10)
    s.add_argument("--tipo", choices=["uplink", "downlink"])
    s.add_argument("--geo", action="store_true", help="agrega un satélite GEO de respaldo sobre 70° O")
    s.add_argument("--no-escalonada", action="store_true")
    s.add_argument("--sin-rotacion", action="store_true", help="Tierra fija, como en MATLAB")
    s.set_defaults(func=cmd_cobertura)
    return p


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    args.func(args)
    return 0
