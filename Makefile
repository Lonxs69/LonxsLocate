PY ?= python3

.PHONY: test lint demo cobertura limpiar

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

limpiar:
	rm -rf __pycache__ */__pycache__ .ruff_cache cobertura.csv
