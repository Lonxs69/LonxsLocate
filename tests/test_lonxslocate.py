import math
import unittest

from lonxslocate.cli import main
from lonxslocate.cobertura import simular_cobertura
from lonxslocate.enlace import (
    Estacion,
    buscar_estacion,
    cargar_estaciones,
    elevacion,
    geometria,
    latencia_ms,
    perdida_espacio_libre_db,
    radio_huella_km,
    satelite_sobre,
)
from lonxslocate.orbita import (
    RADIO_TIERRA,
    Satelite,
    constelacion_walker,
    periodo_orbital,
    satelite_geo,
)


class TestOrbita(unittest.TestCase):
    def test_periodo_geo_es_un_dia_sidereo(self):
        self.assertAlmostEqual(periodo_orbital(42_164.0) / 3600, 23.93, places=1)

    def test_periodo_leo(self):
        self.assertAlmostEqual(periodo_orbital(RADIO_TIERRA + 600) / 60, 96.5, delta=0.5)

    def test_radio_constante_en_orbita_circular(self):
        sat = Satelite("x", 7_000.0, 98.0, 45.0, 10.0)
        for t in (0, 600, 3_000, 10_000):
            self.assertAlmostEqual(math.dist((0, 0, 0), sat.posicion_eci(t)), 7_000.0, places=6)

    def test_walker_tamano_y_escalonamiento(self):
        sats = constelacion_walker(20, 10)
        self.assertEqual(len(sats), 200)
        self.assertNotEqual(sats[0].anomalia_deg, sats[10].anomalia_deg)
        planos = constelacion_walker(4, 2, escalonada=False)
        self.assertEqual(planos[0].anomalia_deg, planos[2].anomalia_deg)


class TestEnlace(unittest.TestCase):
    def test_satelite_en_cenit(self):
        est = Estacion("e", "uplink", "", 4.0, -74.0)
        el, d = geometria(est.posicion_eci(rotacion=False), satelite_sobre(4.0, -74.0, 600))
        self.assertAlmostEqual(el, 90.0, places=4)
        self.assertAlmostEqual(d, 600.0, places=4)

    def test_latencia_geo(self):
        self.assertAlmostEqual(latencia_ms(35_786), 119.4, delta=0.1)

    def test_fspl_referencia(self):
        # 1 km a 1 MHz = 32.44 dB por definición
        self.assertAlmostEqual(perdida_espacio_libre_db(1, 1), 32.44, places=2)

    def test_huella_crece_con_altitud(self):
        self.assertLess(radio_huella_km(500), radio_huella_km(1_200))
        self.assertAlmostEqual(radio_huella_km(600, 0), RADIO_TIERRA * math.acos(RADIO_TIERRA / 6_971))

    def test_geo_fijo_sobre_su_longitud_con_rotacion(self):
        est = Estacion("e", "uplink", "", 0.0, -74.0)
        geo = satelite_geo(longitud_deg=-74.0)
        for t in (0, 3_600, 43_200):
            self.assertGreater(elevacion(est, geo, t), 89.0)


class TestDatos(unittest.TestCase):
    def test_csv_estaciones(self):
        estaciones = cargar_estaciones()
        self.assertEqual(len(estaciones), 15)
        for e in estaciones:
            self.assertIn(e.tipo, ("uplink", "downlink"))
            self.assertTrue(-5 < e.latitud < 14 and -82 < e.longitud < -66, e.nombre)

    def test_busqueda_sin_distinguir_mayusculas(self):
        self.assertEqual(buscar_estacion("bogotá").region, "Cundinamarca")
        with self.assertRaises(KeyError):
            buscar_estacion("Madrid")


class TestCobertura(unittest.TestCase):
    def test_constelacion_densa_cubre_colombia(self):
        est = [buscar_estacion("Uribia"), buscar_estacion("Leticia")]
        res = simular_cobertura(est, constelacion_walker(20, 10), duracion_h=3, paso_s=120)
        for r in res:
            self.assertGreater(r.porcentaje, 95)

    def test_un_satelite_deja_huecos(self):
        est = [buscar_estacion("Bogotá")]
        res = simular_cobertura(est, constelacion_walker(1, 1), duracion_h=6, paso_s=60)
        self.assertLess(res[0].porcentaje, 30)
        self.assertGreater(res[0].hueco_maximo_min, 60)


class TestCLI(unittest.TestCase):
    def test_comandos(self):
        for argv in (["estaciones"], ["enlace"], ["huella", "550"]):
            self.assertEqual(main(argv), 0)


if __name__ == "__main__":
    unittest.main()
