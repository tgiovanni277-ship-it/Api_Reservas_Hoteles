from datetime import date

ESTADOS_PERMITIDOS = {"pendiente", "confirmada", "cancelada"}


def validar_reserva_hotel(data):
    if not isinstance(data, dict):
        return "Envía un objeto JSON"
    for campo in ("huesped", "correo", "habitacion"):
        valor = data.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            return f"{campo} debe ser un texto no vacío"
    correo = data["correo"].strip()
    if "@" not in correo or correo.startswith("@") or correo.endswith("@"):
        return "correo debe tener un formato válido"
    fechas = {}
    for campo in ("fecha_entrada", "fecha_salida"):
        valor = data.get(campo)
        if not isinstance(valor, str):
            return f"{campo} debe tener formato AAAA-MM-DD"
        try:
            fechas[campo] = date.fromisoformat(valor)
        except ValueError:
            return f"{campo} debe tener formato AAAA-MM-DD"
    if fechas["fecha_salida"] <= fechas["fecha_entrada"]:
        return "fecha_salida debe ser posterior a fecha_entrada"
    cantidad = data.get("numero_huespedes")
    if type(cantidad) is not int or cantidad < 1:
        return "numero_huespedes debe ser un entero positivo"
    estado = data.get("estado")
    if not isinstance(estado, str) or estado not in ESTADOS_PERMITIDOS:
        return "estado debe ser pendiente, confirmada o cancelada"
    return None


def normalizar_reserva(data):
    return {
        "huesped": data["huesped"].strip(),
        "correo": data["correo"].strip().lower(),
        "habitacion": data["habitacion"].strip(),
        "fecha_entrada": data["fecha_entrada"],
        "fecha_salida": data["fecha_salida"],
        "numero_huespedes": data["numero_huespedes"],
        "estado": data["estado"],
    }
