-- Consultas útiles sobre los resultados de los barridos.
-- Base de datos: lonxslocate_<entorno>, tabla: resultados.
-- La partición "barrido" usa projection "injected": siempre filtrar por ella.

-- 1. Constelaciones más baratas que cubren todo el país
SELECT planos, sats_por_plano, total_satelites, altitud_km,
       cobertura_min_pct, visibles_promedio
FROM resultados
WHERE barrido = '20261022T120000Z'
  AND cobertura_min_pct >= 99.9
ORDER BY total_satelites, altitud_km, visibles_promedio DESC
LIMIT 10;

-- 2. Frontera costo / cobertura: mejor cobertura posible por cantidad de satélites
SELECT total_satelites,
       max(cobertura_min_pct)   AS mejor_cobertura_min,
       min(hueco_maximo_min)    AS menor_hueco_min
FROM resultados
WHERE barrido = '20261022T120000Z'
GROUP BY total_satelites
ORDER BY total_satelites;

-- 3. Qué estación limita más los diseños que NO llegan al objetivo
SELECT peor_estacion, count(*) AS configuraciones
FROM resultados
WHERE barrido = '20261022T120000Z'
  AND cobertura_min_pct < 99.9
GROUP BY peor_estacion
ORDER BY configuraciones DESC;

-- 4. Efecto de la altitud con la misma cantidad de satélites
SELECT altitud_km, avg(cobertura_min_pct) AS cobertura_min_promedio
FROM resultados
WHERE barrido = '20261022T120000Z'
  AND total_satelites = 80
GROUP BY altitud_km
ORDER BY altitud_km;
