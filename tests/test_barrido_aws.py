import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from lonxslocate.barrido import evaluar_configuracion, generar_configuraciones, mejores

RAIZ = Path(__file__).resolve().parent.parent


def _cargar_handler():
    spec = importlib.util.spec_from_file_location("handler", RAIZ / "aws" / "lambda" / "handler.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class S3Falso:
    def __init__(self):
        self.objetos = {}

    def put_object(self, Bucket, Key, Body, ContentType):  # misma firma que boto3
        self.objetos[(Bucket, Key)] = Body


CONFIG_RAPIDA = {
    "id": "p6-s4-h550",
    "planos": 6,
    "sats_por_plano": 4,
    "altitud_km": 550,
    "inclinacion_deg": 98.0,
    "horas": 1,
    "paso_s": 300,
}


class TestBarrido(unittest.TestCase):
    def test_grilla_completa_y_ids_unicos(self):
        configs = generar_configuraciones()
        self.assertEqual(len(configs), 6 * 5 * 3)
        self.assertEqual(len({c["id"] for c in configs}), len(configs))

    def test_evaluar_devuelve_metricas(self):
        r = evaluar_configuracion(CONFIG_RAPIDA)
        self.assertEqual(r["total_satelites"], 24)
        self.assertTrue(0 <= r["cobertura_min_pct"] <= r["cobertura_media_pct"] <= 100)
        self.assertIn(r["peor_estacion"], {"Pedernales", "Dajabón", "Santo Domingo", "Higüey",
                                           "Comendador", "Jimaní", "Neiba", "Constanza",
                                           "Sabana Grande de Boyá", "Santiago", "La Romana",
                                           "Puerto Plata", "San Juan de la Maguana", "Barahona",
                                           "San Francisco de Macorís"})

    def test_mejores_prioriza_menos_satelites_y_menor_altitud(self):
        resultados = [
            {"total_satelites": 100, "altitud_km": 550, "cobertura_min_pct": 100, "visibles_promedio": 2},
            {"total_satelites": 64, "altitud_km": 1200, "cobertura_min_pct": 100, "visibles_promedio": 1},
            {"total_satelites": 64, "altitud_km": 800, "cobertura_min_pct": 100, "visibles_promedio": 1},
            {"total_satelites": 24, "altitud_km": 550, "cobertura_min_pct": 60, "visibles_promedio": 1},
        ]
        top = mejores(resultados, 99.9)
        self.assertEqual([(r["total_satelites"], r["altitud_km"]) for r in top],
                         [(64, 800), (64, 1200), (100, 550)])


class TestLambda(unittest.TestCase):
    def test_handler_guarda_linea_json_particionada(self):
        handler = _cargar_handler()
        s3 = S3Falso()
        with mock.patch.dict(os.environ, {"RESULTADOS_BUCKET": "bucket-prueba"}):
            salida = handler.handler({"id_barrido": "20261022T120000Z", "config": CONFIG_RAPIDA},
                                     None, s3=s3)

        clave = ("bucket-prueba", "resultados/barrido=20261022T120000Z/p6-s4-h550.json")
        self.assertIn(clave, s3.objetos)
        cuerpo = s3.objetos[clave].decode("utf-8")
        self.assertTrue(cuerpo.endswith("\n"))
        fila = json.loads(cuerpo)
        self.assertEqual(fila["barrido_id"], "20261022T120000Z")
        self.assertEqual(salida["s3"], "s3://bucket-prueba/" + clave[1])

    def test_definicion_step_functions_es_json_valido(self):
        plantilla = (RAIZ / "aws" / "terraform" / "barrido.asl.json").read_text(encoding="utf-8")
        definicion = json.loads(
            plantilla.replace("${concurrencia}", "100")
            .replace("${lambda_arn}", "arn:aws:lambda:us-east-1:000000000000:function:x")
            .replace("${workgroup}", "wg")
            .replace("${base_datos}", "db")
            .replace("${cobertura_objetivo}", "99.9")
        )
        self.assertEqual(definicion["StartAt"], "EvaluarConfiguraciones")
        self.assertEqual(definicion["States"]["EvaluarConfiguraciones"]["Next"], "Rankear")


if __name__ == "__main__":
    unittest.main()
