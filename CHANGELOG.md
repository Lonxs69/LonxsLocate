# Changelog

## [1.4.0] - 2026-10-22
### Agregado
- Comando `barrido`: evalúa 90 diseños de constelación en paralelo y devuelve el mínimo que cubre ≥ 99.9 % en todas las estaciones (64 satélites a 1 200 km frente a los 200 del diseño inicial).
- Ejecución en AWS con `barrido --aws`: Step Functions (Map) + Lambda + S3 + Glue + Athena, en Terraform.
- Despliegue desde GitHub Actions por OIDC, sin llaves guardadas.
- CI valida formato y sintaxis de Terraform.
- Figuras propias generadas desde los datos (`make imagenes`) y banner del proyecto.

### Cambiado
- El proyecto se llama ahora **LonxsLocate**.
- README con títulos centrados y sección sobre el papel de AWS.

## [1.3.0] - 2026-10-22
### Cambiado
- Las 15 estaciones terrenas ahora son de República Dominicana: 8 uplink (Santo Domingo, Santiago, La Romana, Puerto Plata, San Juan, Barahona, Higüey, San Francisco de Macorís) y 7 downlink rurales (Pedernales, Comendador, Dajabón, Jimaní, Neiba, Sabana Grande de Boyá, Constanza).
- Enlace por defecto: Santo Domingo → LEO → Pedernales. GEO de respaldo sobre 70° O.
- `FullSatelliteSimulation.m` carga las estaciones desde el CSV en lugar de tenerlas escritas a mano.
- Finales de línea normalizados a LF.

### Agregado
- `ModulationofPackets.m`: número de paquetes y latencia configurables, con fragmentación de paquetes cuando la latencia supera el umbral.
- `cobertura --csv` para exportar resultados.
- Opción global `--estaciones` para analizar otro país o región.
- `Makefile` con `test`, `lint`, `demo` y `cobertura`.

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
- Scripts de MATLAB (Satellite Communications Toolbox): enlace estación base → LEO → estación de bajada, modulación AM de paquetes, red no escalonada y simulación completa con 200 satélites LEO + 1 GEO.
- Simulación de la red de acceso rural en Cisco Packet Tracer.
- Videos de Universe Sandbox.
