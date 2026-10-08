"""Reportes de la tienda: inventario, ventas y mas vendidos."""

import gestor

# Por debajo de esta cantidad un producto se reporta como "stock bajo".
STOCK_MINIMO = 5


def formatear_moneda(monto):
    """Da formato de dinero a un monto: 12.5 -> "$12.5"."""
    return "$" + str(round(monto, 2))


def productos_stock_bajo():
    """Regresa la lista de productos con stock por debajo del minimo."""
    return [
        producto
        for producto in gestor.INVENTARIO.values()
        if producto["stock"] < STOCK_MINIMO
    ]


def reporte_inventario():
    """Arma el reporte del inventario, lo imprime y lo regresa como texto."""
    texto = "===== INVENTARIO =====\n"
    valor_total = 0
    for producto in gestor.INVENTARIO.values():
        linea = (
            f"{producto['codigo']} | {producto['nombre']} | "
            f"{formatear_moneda(producto['precio'])} | stock: {producto['stock']}"
        )
        if producto["stock"] < STOCK_MINIMO:
            linea = linea + "  <-- STOCK BAJO"
        texto = texto + linea + "\n"
        valor_total = valor_total + producto["precio"] * producto["stock"]
    texto = texto + "Valor total del inventario: " + formatear_moneda(valor_total)
    texto = texto + "\n"
    print(texto)
    return texto


def total_vendido():
    """Suma el total (con IVA) de todas las ventas registradas."""
    return round(sum(venta["total"] for venta in gestor.VENTAS), 2)


def mas_vendidos(n=3):
    """Regresa los n productos mas vendidos como lista de (codigo, unidades)."""
    unidades_por_codigo = {}
    for venta in gestor.VENTAS:
        codigo = venta["codigo"]
        unidades_por_codigo[codigo] = (
            unidades_por_codigo.get(codigo, 0) + venta["cantidad"]
        )
    ranking = list(unidades_por_codigo.items())
    # ordenamiento de burbuja (TODO: algun dia usar sorted)
    for i in range(len(ranking)):
        for j in range(0, len(ranking) - i - 1):
            if ranking[j][1] < ranking[j + 1][1]:
                ranking[j], ranking[j + 1] = ranking[j + 1], ranking[j]
    return ranking[0:n]


def resumen_ventas():
    """Arma el resumen de ventas del dia, lo imprime y lo regresa."""
    texto = "===== RESUMEN DE VENTAS =====\n"
    total_del_dia = 0
    for venta in gestor.VENTAS:
        texto = texto + (
            f"Folio {venta['folio']}: {venta['nombre']} x{venta['cantidad']}"
            f" = {formatear_moneda(venta['total'])}\n"
        )
        total_del_dia = total_del_dia + venta["total"]
    texto = texto + "Numero de ventas: " + str(len(gestor.VENTAS)) + "\n"
    texto = texto + "Total del dia: " + formatear_moneda(total_del_dia) + "\n"
    print(texto)
    return texto
