"""AWS Lambda: evalúa UNA configuración de constelación y guarda el resultado en S3.

Step Functions invoca esta función en paralelo, una vez por configuración.
Cada resultado se escribe como una línea JSON en
``s3://<bucket>/resultados/barrido=<id>/<config>.json`` para consultarlo con Athena.
"""

from __future__ import annotations

import json
import os

from lonxslocate.barrido import evaluar_configuracion

_s3 = None


def _cliente_s3():
    global _s3
    if _s3 is None:
        import boto3  # incluido en el runtime de Lambda

        _s3 = boto3.client("s3")
    return _s3


def handler(event: dict, context=None, s3=None) -> dict:
    id_barrido = event["id_barrido"]
    config = event["config"]
    resultado = evaluar_configuracion(config)
    resultado["barrido_id"] = id_barrido

    bucket = os.environ["RESULTADOS_BUCKET"]
    clave = f"resultados/barrido={id_barrido}/{config['id']}.json"
    (s3 or _cliente_s3()).put_object(
        Bucket=bucket,
        Key=clave,
        Body=(json.dumps(resultado, ensure_ascii=False) + "\n").encode("utf-8"),
        ContentType="application/json",
    )
    return {
        "id": config["id"],
        "cobertura_min_pct": resultado["cobertura_min_pct"],
        "s3": f"s3://{bucket}/{clave}",
    }
