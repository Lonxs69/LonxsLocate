PY ?= python3

.PHONY: test lint demo cobertura barrido imagenes tf-validar limpiar

test:
	$(PY) -m unittest discover -s tests -v

lint:
	pipx run ruff check lonxslocate tests aws

demo:
	$(PY) -m lonxslocate estaciones
	$(PY) -m lonxslocate enlace
	$(PY) -m lonxslocate huella

cobertura:
	$(PY) -m lonxslocate cobertura --geo --csv cobertura.csv

barrido:
	$(PY) -m lonxslocate barrido --json barrido.json

imagenes:
	$(PY) -m pip install -q -r scripts/requirements.txt
	$(PY) scripts/generar_imagenes.py

tf-validar:
	cd aws/terraform && terraform fmt -check -recursive && terraform init -backend=false -input=false && terraform validate

limpiar:
	rm -rf __pycache__ */__pycache__ .ruff_cache cobertura.csv barrido.json aws/terraform/.build
