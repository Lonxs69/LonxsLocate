# Changelog

## [1.2.0] - 2026-10-22
### Agregado
- Comando `cobertura`: simula 24 h de una constelación Walker y mide el porcentaje de tiempo con al menos un satélite visible por estación, el hueco máximo y los satélites visibles en promedio.
- Rotación terrestre en la simulación (activa por defecto; `--sin-rotacion` reproduce el modelo original).
- Opción `--geo` para agregar un satélite geoestacionario de respaldo.
- CI en GitHub Actions con Python 3.9, 3.11 y 3.13.

## [1.1.0] - 2026-10-22
### Agregado
- Paquete `lonxslocate` en Python sin dependencias: mecánica orbital, geometría de enlace, latencia y pérdidas en espacio libre (FSPL).
- Comandos `estaciones`, `enlace` y `huella`.
- `data/estaciones.csv` como fuente única de las 15 estaciones (8 uplink, 7 downlink).
- `matlab/cargar_estaciones.m` para usar el CSV desde MATLAB.

## [1.0.0]
### Inicial
- Scripts de MATLAB (Satellite Communications Toolbox): enlace Bogotá → LEO → Uribia, modulación AM de paquetes, red no escalonada y simulación completa con 200 satélites LEO + 1 GEO.
- Simulación en Cisco Packet Tracer para La Guajira.
- Videos de Universe Sandbox.
