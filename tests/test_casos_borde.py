"""Pruebas de caracterización agregadas durante el reto.

Se escribieron ANTES de refactorizar, contra el código original, para fijar
comportamiento observable que la suite original no cubría (texto del ticket,
mensajes de error, umbrales exactos de descuento, formato de reportes y
persistencia). Los archivos de prueba originales no se modificaron.
"""

import json

import almacen
import gestor
import reportes


def _alta(codigo="A1", nombre="Producto", precio=100.0, stock=50):
    assert gestor.agregarProducto(codigo, nombre, precio, stock)


# --- Mensajes de error (main.py los muestra al usuario) -------------------


def test_mensajes_de_error_de_alta():
    assert gestor.agregarProducto("", "X", 10.0, 1) is False
    assert gestor.ultimo_error == "codigo vacio"
    assert gestor.agregarProducto(None, "X", 10.0, 1) is False
    assert gestor.ultimo_error == "codigo vacio"
    _alta("A1")
    gestor.agregarProducto("A1", "X", 10.0, 1)
    assert gestor.ultimo_error == "el producto ya existe"
    gestor.agregarProducto("A2", "X", 0, 1)
    assert gestor.ultimo_error == "precio invalido"
    gestor.agregarProducto("A3", "X", 10.0, -1)
    assert gestor.ultimo_error == "stock invalido"


def test_mensajes_de_error_de_venta_respetan_el_orden_de_validacion():
    _alta("A1", stock=2)
    assert gestor.registrar_venta("", 1) is None
    assert gestor.ultimo_error == "codigo vacio"
    assert gestor.registrar_venta(None, 1) is None
    assert gestor.ultimo_error == "codigo vacio"
    assert gestor.registrar_venta("ZZZ", 0) is None
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.registrar_venta("A1", None) is None
    assert gestor.ultimo_error == "cantidad invalida"
    assert gestor.registrar_venta("A1", 3) is None
    assert gestor.ultimo_error == "stock insuficiente"


def test_mensajes_de_error_de_cotizar_stock_y_eliminar():
    _alta("A1", stock=1)
    assert gestor.cotizar("ZZZ", 1) is None
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.cotizar("A1", 0) is None
    assert gestor.ultimo_error == "cantidad invalida"
    assert gestor.actualizar_stock("ZZZ", 1) is False
    assert gestor.ultimo_error == "producto no existe"
    assert gestor.actualizar_stock("A1", -2) is False
    assert gestor.ultimo_error == "el stock no puede quedar negativo"
    assert gestor.eliminar_producto("ZZZ") is False
    assert gestor.ultimo_error == "producto no existe"


def test_cotizar_no_valida_stock_ni_modifica_nada():
    _alta("A1", precio=10.0, stock=1)
    assert gestor.cotizar("A1", 5) == 58.0
    assert gestor.INVENTARIO["A1"]["stock"] == 1
    assert gestor.VENTAS == []


# --- Umbrales de descuento -------------------------------------------------


def test_umbrales_exactos_de_descuento_por_volumen():
    _alta("A1", precio=1.0, stock=5000)
    assert gestor.registrar_venta("A1", 499)["descuento"] == 0
    assert gestor.registrar_venta("A1", 500)["descuento"] == 25.0
    assert gestor.registrar_venta("A1", 999)["descuento"] == 49.95
    assert gestor.registrar_venta("A1", 1000)["descuento"] == 100.0


def test_descuento_vip_requiere_prefijo_y_monto_minimo():
    _alta("A1", precio=100.0, stock=100)
    # $200 sin descuento por volumen: no supera los $200 -> sin extra VIP
    assert gestor.registrar_venta("A1", 2, "VIP1")["descuento"] == 0
    # $300 -> supera $200 -> 2 % VIP
    assert gestor.registrar_venta("A1", 3, "VIP1")["descuento"] == 6.0
    # el prefijo distingue mayúsculas y debe ir al inicio
    assert gestor.registrar_venta("A1", 3, "vip1")["descuento"] == 0
    assert gestor.registrar_venta("A1", 3, "XVIP")["descuento"] == 0
    assert gestor.registrar_venta("A1", 3, "VI")["descuento"] == 0
    assert gestor.registrar_venta("A1", 3, None)["descuento"] == 0


def test_vip_no_aplica_en_cotizacion():
    _alta("A1", precio=100.0, stock=50)
    venta_vip = gestor.registrar_venta("A1", 6, "VIP007")
    assert gestor.cotizar("A1", 6) != venta_vip["total"]


# --- Registro de venta y ticket --------------------------------------------


def test_registro_de_venta_completo():
    _alta("A1", nombre="Café", precio=100.0, stock=50)
    venta = gestor.registrar_venta("A1", 6, "VIP007")
    assert venta["folio"] == 1
    assert venta["codigo"] == "A1"
    assert venta["nombre"] == "Café"
    assert venta["cantidad"] == 6
    assert venta["subtotal"] == 600.0
    assert venta["descuento"] == 42.0
    assert venta["impuesto"] == 89.28
    assert venta["total"] == 647.28
    assert venta["cliente"] == "VIP007"
    assert len(venta["fecha"]) == 19


def test_ticket_con_descuento():
    _alta("A1", nombre="Café", precio=100.0, stock=50)
    ticket = gestor.registrar_venta("A1", 6)["ticket"]
    assert ticket == (
        "TIENDA LA ESQUINA\n"
        "----------------------------\n"
        "Folio: 1\n"
        "Café x6\n"
        "Subtotal: $600.0\n"
        "Descuento: -$30.0\n"
        "IVA: $91.2\n"
        "TOTAL: $661.2\n"
    )


def test_ticket_sin_descuento_omite_la_linea():
    _alta("A1", nombre="Café", precio=10.0, stock=50)
    ticket = gestor.registrar_venta("A1", 2)["ticket"]
    assert "Descuento" not in ticket
    assert ticket.endswith("IVA: $3.2\nTOTAL: $23.2\n")


def test_buscar_producto_sin_coincidencias_y_texto_vacio():
    _alta("A1", nombre="Café")
    _alta("A2", nombre="Azúcar")
    assert gestor.buscarProducto("xyz") == []
    assert len(gestor.buscarProducto("")) == 2


# --- Reportes ---------------------------------------------------------------


def test_texto_del_reporte_de_inventario(capsys):
    _alta("A1", nombre="Leche", precio=26.0, stock=3)
    _alta("A2", nombre="Azúcar", precio=32.5, stock=40)
    texto = reportes.reporte_inventario()
    assert texto == (
        "===== INVENTARIO =====\n"
        "A1 | Leche | $26.0 | stock: 3  <-- STOCK BAJO\n"
        "A2 | Azúcar | $32.5 | stock: 40\n"
        "Valor total del inventario: $1378.0\n"
    )
    assert capsys.readouterr().out == texto + "\n"


def test_texto_del_resumen_de_ventas(capsys):
    _alta("A1", nombre="Café", precio=10.0, stock=50)
    gestor.registrar_venta("A1", 2)
    texto = reportes.resumen_ventas()
    assert texto == (
        "===== RESUMEN DE VENTAS =====\n"
        "Folio 1: Café x2 = $23.2\n"
        "Numero de ventas: 1\n"
        "Total del dia: $23.2\n"
    )
    assert capsys.readouterr().out == texto + "\n"


def test_stock_bajo_es_estrictamente_menor_a_cinco():
    _alta("A1", stock=5)
    _alta("A2", stock=4)
    assert [p["codigo"] for p in reportes.productos_stock_bajo()] == ["A2"]


def test_mas_vendidos_conserva_el_orden_en_empates_y_respeta_n():
    _alta("A1", stock=100)
    _alta("B1", stock=100)
    _alta("C1", stock=100)
    gestor.registrar_venta("A1", 2)
    gestor.registrar_venta("B1", 2)
    gestor.registrar_venta("C1", 5)
    assert reportes.mas_vendidos() == [("C1", 5), ("A1", 2), ("B1", 2)]
    assert reportes.mas_vendidos(1) == [("C1", 5)]
    assert reportes.mas_vendidos(10) == [("C1", 5), ("A1", 2), ("B1", 2)]


# --- Persistencia -------------------------------------------------------------


def test_formato_del_json_guardado(tmp_path):
    ruta = tmp_path / "datos.json"
    _alta("A1", nombre="Café", precio=10.0, stock=5)
    gestor.registrar_venta("A1", 1)
    almacen.guardar_datos(str(ruta))
    texto = ruta.read_text(encoding="utf-8")
    assert '"nombre": "Café"' in texto  # ensure_ascii=False
    datos = json.loads(texto)
    assert set(datos) == {"inventario", "ventas", "contador"}
    assert datos["contador"] == 1


def test_cargar_json_corrupto_regresa_false_y_conserva_estado(tmp_path):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    _alta("A1")
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert "A1" in gestor.INVENTARIO


def test_cargar_archivo_inexistente_deja_mensaje(tmp_path):
    assert almacen.cargar_datos(str(tmp_path / "nada.json")) is False
    assert gestor.ultimo_error == "el archivo no existe"


def test_cargar_sin_contador_usa_cero(tmp_path):
    ruta = tmp_path / "viejo.json"
    ruta.write_text('{"inventario": {}, "ventas": []}', encoding="utf-8")
    assert almacen.cargar_datos(str(ruta)) is True
    _alta("A1", precio=10.0)
    assert gestor.registrar_venta("A1", 1)["folio"] == 1


def test_cargar_reemplaza_en_sitio_las_colecciones(tmp_path):
    ruta = str(tmp_path / "datos.json")
    inventario, ventas = gestor.INVENTARIO, gestor.VENTAS
    _alta("A1", precio=10.0)
    gestor.registrar_venta("A1", 1)
    almacen.guardar_datos(ruta)
    gestor.reiniciar_sistema()
    almacen.cargar_datos(ruta)
    assert gestor.INVENTARIO is inventario
    assert gestor.VENTAS is ventas
    assert len(ventas) == 1


# --- Agregadas con la refactorización del manejo de errores -----------------
# Antes, un JSON válido pero sin la clave "inventario" lanzaba KeyError DESPUÉS
# de vaciar el inventario (estado perdido). Ahora se rechaza sin tocar nada.


def test_json_sin_estructura_esperada_no_borra_el_estado(tmp_path):
    ruta = tmp_path / "incompleto.json"
    ruta.write_text('{"ventas": []}', encoding="utf-8")
    _alta("A1")
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"
    assert "A1" in gestor.INVENTARIO


def test_json_que_no_es_objeto_se_rechaza(tmp_path):
    ruta = tmp_path / "lista.json"
    ruta.write_text("[1, 2, 3]", encoding="utf-8")
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"


def test_archivo_binario_se_reporta_como_corrupto(tmp_path):
    ruta = tmp_path / "binario.json"
    ruta.write_bytes(b"\xff\xfe\x00\x81")
    assert almacen.cargar_datos(str(ruta)) is False
    assert gestor.ultimo_error == "archivo corrupto"


def test_ruta_que_es_directorio_no_truena(tmp_path):
    assert almacen.cargar_datos(str(tmp_path)) is False
    assert gestor.ultimo_error == "no se pudo leer el archivo"
