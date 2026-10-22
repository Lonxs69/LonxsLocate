# Cómo contribuir

¡Gracias por el interés en lonxsLocate!

1. Haz un fork y crea una rama: `git checkout -b mejora/nombre-corto`.
2. Si agregas una estación, edítala solo en `data/estaciones.csv`; MATLAB y Python leen ese mismo archivo.
3. Corre los tests antes de abrir el PR:
   ```bash
   python -m unittest discover -s tests -v
   ```
4. Mantén el código sin dependencias externas (solo librería estándar de Python).
5. Escribe los mensajes de commit en español y en presente: `agrega estación de Montecristi`.

Para proponer una región sin programar, abre un issue con la plantilla **Proponer una región**.
