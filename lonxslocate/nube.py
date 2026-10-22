"""Lanza un barrido en AWS Step Functions y lee el ranking que deja Athena.

Requiere ``pip install lonxslocate[aws]`` (boto3) y credenciales de AWS.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone


def barrido_aws(state_machine_arn: str, configs: list[dict], espera_s: float = 5.0) -> list[dict]:
    import boto3

    region = state_machine_arn.split(":")[3]
    sfn = boto3.client("stepfunctions", region_name=region)
    athena = boto3.client("athena", region_name=region)

    id_barrido = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ejecucion = sfn.start_execution(
        stateMachineArn=state_machine_arn,
        name=f"barrido-{id_barrido}",
        input=json.dumps({"id_barrido": id_barrido, "configuraciones": configs}),
    )["executionArn"]
    print(f"Barrido {id_barrido} lanzado: {len(configs)} configuraciones en paralelo")

    while True:
        estado = sfn.describe_execution(executionArn=ejecucion)
        if estado["status"] != "RUNNING":
            break
        time.sleep(espera_s)
    if estado["status"] != "SUCCEEDED":
        raise RuntimeError(f"La ejecución terminó en {estado['status']}: {ejecucion}")

    query_id = json.loads(estado["output"])["ranking"]["query_id"]
    filas = athena.get_query_results(QueryExecutionId=query_id)["ResultSet"]["Rows"]
    encabezados = [c["VarCharValue"] for c in filas[0]["Data"]]
    return [
        {k: c.get("VarCharValue") for k, c in zip(encabezados, fila["Data"])} for fila in filas[1:]
    ]
