# Fundamentos técnicos

Fórmulas que usa `lonxslocate`. Todo el modelo supone una Tierra esférica (R = 6 371 km) y órbitas circulares.

## Periodo orbital

Tercera ley de Kepler, con μ = 398 600.4418 km³/s²:

```
T = 2π · √(a³ / μ)
```

| Órbita | Semieje `a` | Periodo |
|---|---|---|
| LEO 600 km | 6 971 km | ≈ 96.5 min |
| LEO del proyecto | 7 000 km | ≈ 97 min |
| GEO | 42 164 km | ≈ 23 h 56 min (día sidéreo) |

## Posición del satélite

Para un satélite con inclinación `i`, RAAN `Ω` y argumento de latitud `u = u₀ + n·t` (con `n = √(μ/a³)`):

```
x = a (cos Ω cos u − sin Ω sin u cos i)
y = a (sin Ω cos u + cos Ω sin u cos i)
z = a  sin u sin i
```

Las estaciones giran con la Tierra a ω = 7.2921×10⁻⁵ rad/s. Por eso un satélite GEO a la misma longitud se ve siempre en el mismo punto del cielo.

## Elevación y distancia oblicua

Con `d = r_sat − r_est`:

```
distancia = |d|
sin(elevación) = (d · r_est) / (|d| · |r_est|)
```

Un satélite solo cuenta como visible si la elevación es ≥ 10° (valor configurable). Por debajo de eso, el enlace atraviesa demasiada atmósfera y obstáculos.

## Latencia

```
latencia (ms) = distancia (km) / c · 1000      con c = 299 792.458 km/s
```

Bogotá → LEO 600 km → Uribia da ≈ 5 ms. El mismo enlace por GEO da ≈ 240 ms, casi 45 veces más.

## Pérdida en espacio libre (FSPL)

```
FSPL (dB) = 20·log₁₀(d_km) + 20·log₁₀(f_MHz) + 32.44
```

## Radio de huella

Área desde la que el satélite se ve con al menos ε grados de elevación:

```
λ = arccos( R·cos ε / (R + h) ) − ε
radio = R · λ
```

## Constelación Walker

`planos × satélites por plano`, con los planos repartidos en 360° de RAAN. En la versión **escalonada** cada plano se desfasa `360°·F·p / T` respecto al anterior. Así los huecos de un plano los cubre el siguiente, y es la configuración que logra cobertura continua sobre Colombia. La **no escalonada** (todos los planos en fase) deja huecos de más de 40 minutos. Se puede comprobar con:

```bash
python -m lonxslocate cobertura --planos 10 --sats 1 --no-escalonada
```
