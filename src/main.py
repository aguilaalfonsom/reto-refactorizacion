"""Punto de entrada del gestor de tienda (menu interactivo en consola).

Este es el unico modulo que conversa con el usuario (input/print del menu);
las reglas de negocio viven en gestor, reportes y almacen.
"""

from collections.abc import Callable

import almacen
import gestor
import reportes

ARCHIVO = "datos_ejemplo.json"


def pedir_numero(mensaje: str) -> float:
    """Pide un numero al usuario hasta que escriba algo valido."""
    while True:
        respuesta = input(mensaje)
        try:
            return float(respuesta)
        except ValueError:
            print("Eso no es un numero, intenta de nuevo.")


def pedir_entero(mensaje: str) -> int:
    """Pide un numero y lo trunca a entero (cantidades y stock)."""
    return int(pedir_numero(mensaje))


def mostrar_error() -> None:
    """Muestra el motivo del ultimo fallo registrado por el gestor."""
    print("Error:", gestor.ultimo_error)


# --- Acciones del menu: una funcion por opcion -------------------------------


def opcion_agregar_producto() -> None:
    codigo = input("Codigo: ")
    nombre = input("Nombre: ")
    precio = pedir_numero("Precio: ")
    stock = pedir_entero("Stock inicial: ")
    if gestor.agregarProducto(codigo, nombre, precio, stock):
        print("Producto agregado.")
    else:
        mostrar_error()


def opcion_registrar_venta() -> None:
    codigo = input("Codigo del producto: ")
    cantidad = pedir_entero("Cantidad: ")
    cliente = input("Codigo de cliente (enter si no tiene): ")
    venta = gestor.registrar_venta(codigo, cantidad, cliente)
    if venta is None:
        mostrar_error()
        return
    print(venta["ticket"])


def opcion_cotizar() -> None:
    codigo = input("Codigo del producto: ")
    cantidad = pedir_entero("Cantidad: ")
    total = gestor.cotizar(codigo, cantidad)
    if total is None:
        mostrar_error()
        return
    print("Total estimado (con IVA): $" + str(total))


def opcion_mas_vendidos() -> None:
    for codigo, unidades in reportes.mas_vendidos():
        print(codigo, "->", unidades, "unidades")


def opcion_stock_bajo() -> None:
    productos = reportes.productos_stock_bajo()
    if not productos:
        print("No hay productos con stock bajo.")
        return
    for producto in productos:
        print("OJO:", producto["nombre"], "solo tiene", producto["stock"], "unidades")


def opcion_guardar_y_salir() -> None:
    almacen.guardar_datos(ARCHIVO)
    print("Datos guardados. Hasta luego.")


OPCION_SALIR = "8"

# Opcion -> (texto que se muestra, accion que se ejecuta)
OPCIONES: dict[str, tuple[str, Callable[[], object]]] = {
    "1": ("Agregar producto", opcion_agregar_producto),
    "2": ("Registrar venta", opcion_registrar_venta),
    "3": ("Cotizar", opcion_cotizar),
    "4": ("Reporte de inventario", reportes.reporte_inventario),
    "5": ("Resumen de ventas", reportes.resumen_ventas),
    "6": ("Mas vendidos", opcion_mas_vendidos),
    "7": ("Alertas de stock bajo", opcion_stock_bajo),
    OPCION_SALIR: ("Guardar y salir", opcion_guardar_y_salir),
}


def mostrar_menu() -> None:
    print("")
    for clave, (texto, _accion) in OPCIONES.items():
        print(f"{clave}) {texto}")


def cargar_datos_iniciales() -> None:
    if almacen.hay_archivo(ARCHIVO):
        almacen.cargar_datos(ARCHIVO)
        print("Datos cargados de", ARCHIVO)


def menu() -> None:
    """Ciclo principal: muestra el menu y ejecuta la opcion elegida."""
    print("Bienvenido al gestor de la tienda La Esquina")
    cargar_datos_iniciales()
    while True:
        mostrar_menu()
        opcion = input("Opcion: ")
        if opcion not in OPCIONES:
            print("Opcion no valida.")
            continue
        _texto, accion = OPCIONES[opcion]
        accion()
        if opcion == OPCION_SALIR:
            break


if __name__ == "__main__":
    menu()
