"""Modulo principal del gestor de inventario y ventas de "La Esquina".

Aqui vive casi toda la logica del negocio. Historicamente este archivo
lo fueron parchando varias personas, asi que hay de todo un poco.
"""

from datetime import datetime
from typing import NamedTuple

# ---------------------------------------------------------------
# Reglas de negocio
# ---------------------------------------------------------------
TASA_IVA = 0.16

# Descuento por volumen: se aplica sobre el subtotal de la venta.
UMBRAL_DESCUENTO_ALTO = 1000
TASA_DESCUENTO_ALTO = 0.10
UMBRAL_DESCUENTO_MEDIO = 500
TASA_DESCUENTO_MEDIO = 0.05

# Clientes VIP: extra sobre el subtotal si la compra (ya con descuento
# por volumen) supera el monto minimo.
PREFIJO_CLIENTE_VIP = "VIP"
MONTO_MINIMO_VIP = 200
TASA_DESCUENTO_VIP = 0.02

NOMBRE_TIENDA = "TIENDA LA ESQUINA"
FORMATO_FECHA = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------
# Estado global de la aplicacion (inventario, ventas y contadores)
# ---------------------------------------------------------------
INVENTARIO = {}
VENTAS = []
contador_ventas = 0
ultimo_error = ""


def reiniciar_sistema():
    """Borra todo el estado del sistema (inventario, ventas y folios)."""
    global contador_ventas, ultimo_error
    INVENTARIO.clear()
    VENTAS.clear()
    contador_ventas = 0
    ultimo_error = ""


def _fallar(mensaje, resultado=False):
    """Guarda el motivo del fallo en ultimo_error y regresa `resultado`."""
    global ultimo_error
    ultimo_error = mensaje
    return resultado


def agregarProducto(codigo, nombre, precio, stock):
    """Valida los datos y da de alta un producto en el inventario."""
    if not codigo:
        return _fallar("codigo vacio")
    if codigo in INVENTARIO:
        return _fallar("el producto ya existe")
    if precio <= 0:
        return _fallar("precio invalido")
    if stock < 0:
        return _fallar("stock invalido")
    INVENTARIO[codigo] = {
        "codigo": codigo,
        "nombre": nombre,
        "precio": precio,
        "stock": stock,
    }
    return True


def eliminar_producto(codigo):
    """Quita un producto del inventario. Regresa False si no existe."""
    if codigo not in INVENTARIO:
        return _fallar("producto no existe")
    del INVENTARIO[codigo]
    return True


def actualizar_stock(codigo, cantidad):
    """Suma unidades al stock (o resta si la cantidad es negativa)."""
    if codigo not in INVENTARIO:
        return _fallar("producto no existe")
    nuevo_stock = INVENTARIO[codigo]["stock"] + cantidad
    if nuevo_stock < 0:
        return _fallar("el stock no puede quedar negativo")
    INVENTARIO[codigo]["stock"] = nuevo_stock
    return True


def buscarProducto(texto):
    """Busca productos cuyo nombre contenga el texto (sin importar mayusculas)."""
    texto_buscado = texto.lower()
    return [
        producto
        for producto in INVENTARIO.values()
        if texto_buscado in producto["nombre"].lower()
    ]


class Importes(NamedTuple):
    """Desglose del cobro de una compra (montos sin redondear salvo total)."""

    subtotal: float
    descuento: float
    impuesto: float
    total: float


def _descuento_por_volumen(subtotal):
    """Descuento que corresponde al subtotal segun los umbrales de volumen."""
    if subtotal >= UMBRAL_DESCUENTO_ALTO:
        return subtotal * TASA_DESCUENTO_ALTO
    if subtotal >= UMBRAL_DESCUENTO_MEDIO:
        return subtotal * TASA_DESCUENTO_MEDIO
    return 0


def _es_cliente_vip(cliente):
    """Indica si el codigo de cliente tiene el prefijo VIP."""
    return bool(cliente) and cliente.startswith(PREFIJO_CLIENTE_VIP)


def _calcular_importes(precio, cantidad, cliente=None):
    """Calcula subtotal, descuentos, IVA y total de una compra.

    Es la unica fuente de verdad de los precios: la usan tanto
    registrar_venta como cotizar, asi que nunca pueden diferir.
    """
    subtotal = precio * cantidad
    descuento = _descuento_por_volumen(subtotal)
    if _es_cliente_vip(cliente) and subtotal - descuento > MONTO_MINIMO_VIP:
        descuento = descuento + subtotal * TASA_DESCUENTO_VIP
    base = subtotal - descuento
    impuesto = base * TASA_IVA
    return Importes(subtotal, descuento, impuesto, round(base + impuesto, 2))


def _validar_venta(codigo, cantidad):
    """Regresa el motivo por el que la venta no procede, o None si es valida."""
    if not codigo:
        return "codigo vacio"
    if codigo not in INVENTARIO:
        return "producto no existe"
    if cantidad is None or cantidad <= 0:
        return "cantidad invalida"
    if INVENTARIO[codigo]["stock"] < cantidad:
        return "stock insuficiente"
    return None


def _armar_ticket(venta, mostrar_descuento):
    """Genera el ticket en texto plano de una venta ya registrada."""
    lineas = [
        NOMBRE_TIENDA,
        "----------------------------",
        f"Folio: {venta['folio']}",
        f"{venta['nombre']} x{venta['cantidad']}",
        f"Subtotal: ${venta['subtotal']}",
    ]
    if mostrar_descuento:
        lineas.append(f"Descuento: -${venta['descuento']}")
    lineas.append(f"IVA: ${venta['impuesto']}")
    lineas.append(f"TOTAL: ${venta['total']}")
    return "\n".join(lineas) + "\n"


def registrar_venta(codigo, cantidad, cliente=""):
    """Registra una venta: valida, cobra, descuenta stock y genera el ticket.

    Si algo falla regresa None y deja el motivo en ultimo_error.
    """
    global contador_ventas
    error = _validar_venta(codigo, cantidad)
    if error:
        return _fallar(error, None)

    producto = INVENTARIO[codigo]
    importes = _calcular_importes(producto["precio"], cantidad, cliente)
    producto["stock"] = producto["stock"] - cantidad
    contador_ventas = contador_ventas + 1
    venta = {
        "folio": contador_ventas,
        "codigo": codigo,
        "nombre": producto["nombre"],
        "cantidad": cantidad,
        "subtotal": round(importes.subtotal, 2),
        "descuento": round(importes.descuento, 2),
        "impuesto": round(importes.impuesto, 2),
        "total": importes.total,
        "cliente": cliente,
        "fecha": datetime.now().strftime(FORMATO_FECHA),
    }
    venta["ticket"] = _armar_ticket(venta, importes.descuento > 0)
    VENTAS.append(venta)
    return venta


def cotizar(codigo, cantidad):
    """Calcula cuanto costaria una compra sin registrar la venta.

    No valida stock ni aplica el descuento VIP.
    """
    if codigo not in INVENTARIO:
        return _fallar("producto no existe", None)
    if cantidad is None or cantidad <= 0:
        return _fallar("cantidad invalida", None)
    return _calcular_importes(INVENTARIO[codigo]["precio"], cantidad).total
