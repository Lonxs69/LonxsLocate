PY ?= python3

.PHONY: test lint demo cobertura imagenes limpiar

test:
	$(PY) -m unittest discover -s tests -v

lint:
	pipx run ruff check lonxslocate tests

demo:
	$(PY) -m lonxslocate estaciones
	$(PY) -m lonxslocate enlace
	$(PY) -m lonxslocate huella

cobertura:
	$(PY) -m lonxslocate cobertura --geo --csv cobertura.csv

imagenes:
	$(PY) -m pip install -q -r scripts/requirements.txt
	$(PY) scripts/generar_imagenes.py

limpiar:
	rm -rf __pycache__ */__pycache__ .ruff_cache cobertura.csv
