"""Feature flag central de la mecanica de "llego".

Cuando FACTURAR_SOLO_LLEGADOS esta en True, solo se facturan/muestran los items
marcados como "llegado" (el cliente paga unicamente lo que llego). Cuando esta en
False (estado actual), se factura TODO: subtotal/comision/total cuentan todos los
items activos y se oculta la columna "Llego".

Para reactivar la mecanica en el futuro:
  1. Poner FACTURAR_SOLO_LLEGADOS = True aqui.
  2. Volver a mostrar la columna "Llego" en el frontend (Factura.jsx,
     FacturaPublica.jsx) y en el Excel (export.py) usando el mismo flag espejo.
"""

FACTURAR_SOLO_LLEGADOS = False


def items_a_facturar(items_activos):
    """Items que entran en el calculo de subtotal/comision/total."""
    if FACTURAR_SOLO_LLEGADOS:
        return [i for i in items_activos if i.llegado]
    return list(items_activos)
