"""Filtrado de items facturables.

Un item se factura cuando esta activo (item.activo == True). Los items
desactivados quedan guardados en el pedido pero NO cuentan para
subtotal/comision/total ni aparecen en la factura del cliente. Sirve para quitar
de un pedido lo que el cliente ya no quiere sin borrarlo (se puede reactivar).
"""


def items_a_facturar(items):
    """Items activos: los que cuentan para subtotal/comision/total."""
    return [i for i in items if i.activo]
