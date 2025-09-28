def parse_pickup_details(prompt):
    """
    Extracts phone number and pickup time from the prompt safely.
    Expected format: "phone_number, pickup_time"
    """
    try:
        parts = [part.strip() for part in prompt.split(',')]
        if len(parts) < 2:
            return "Número o tiempo faltante", "Número o tiempo faltante"  # Placeholder for missing values
        return parts[0], parts[1]
    except Exception as e:
        return "Error de formato", "Error de formato"  # Error handling

def parse_delivery_details(prompt):
    """
    Extracts address and delivery zone from the prompt safely.
    Expected format: "address, zone"
    """
    try:
        parts = [part.strip() for part in prompt.split(',')]
        if len(parts) < 2:
            return "Dirección o zona faltante", "Dirección o zona faltante"  # Placeholder for missing values
        return parts[0], parts[1]
    except Exception as e:
        return "Error de formato", "Error de formato"  # Error handling

def parse_payment_method(prompt):
    """
    Analiza el método de pago del prompt y devuelve un diccionario con la información.
    Asumimos que el prompt incluirá una descripción del método de pago seleccionado.
    """
    # Este ejemplo es muy básico y debe ser ampliado según los métodos de pago específicos y sus detalles.
    methods = {
        "tarjeta": {"method": "Tarjeta", "info": None},  # Aquí se podría requerir más información, como tipo de tarjeta, etc.
        "efectivo": {"method": "Efectivo"},
        "transferencia": {"method": "Transferencia", "info": None},  # Se podría requerir detalles como banco, número de cuenta, etc.
        "yape": {"method": "Yape", "info": None}  # Se podría requerir un número de teléfono o identificador Yape.
    }
    # Normalizar y buscar el método en el texto
    prompt_lower = prompt.lower()
    for key in methods:
        if key in prompt_lower:
            return methods[key]  # Retorna el diccionario correspondiente al método encontrado
    return {"method": "Desconocido"}  # Retorna un valor predeterminado si no se encuentra ningún método conocido

def format_order_review(evaluated_response, order_type, user_name, order_details):
    style_container = "style='border: 2px solid #ccc; padding: 10px; background: #fff; color: #333; max-width: 400px; margin: 20px auto; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'"
    style_header = "style='font-weight: bold; color: #d10000; margin-bottom: 10px; border-bottom: 1px solid #d10000; padding-bottom: 5px;'"
    style_list = "style='list-style-type: none; padding-left: 0; margin-top: 10px; margin-bottom: 10px;'"
    style_item = "style='margin-bottom: 5px; padding-left: 0;'"

    # Limpia la respuesta evaluada antes de formatearla
    clean_evaluated_response = clean_response(evaluated_response)
    items_formatted = f"<ul {style_list}>{clean_evaluated_response}</ul>"

    response_lines = [
        f"<div {style_container}>",
        f"<h3 {style_header}>Resumen del Pedido</h3>",
        f"<p {style_header}>Cliente: {user_name}</p>",
        f"<p {style_header}>Productos solicitados:</p>{items_formatted}",
        f"<p {style_header}>Tipo de pedido: {'Recogida' if order_type == 'pickup' else 'Entrega'}</p>",
    ]

    if order_type == "pickup":
        response_lines.extend([
            f"<p {style_header}>Recoger en: {order_details.get('pickup_location', 'Ubicación no especificada')}</p>",
            f"<p {style_header}>Teléfono: {order_details.get('phone', 'Teléfono no proporcionado')}</p>"
        ])
    else:
        response_lines.extend([
            f"<p {style_header}>Dirección: {order_details.get('address', 'Dirección no proporcionada')}</p>",
            f"<p {style_header}>Zona: {order_details.get('zone', 'Zona no especificada')}</p>",
            f"<p {style_header}>Teléfono: {order_details.get('phone', 'Teléfono no proporcionado')}</p>",
            f"<p {style_header}>Método de pago: {order_details.get('method', 'Método no proporcionado')}</p>"
        ])

    response_lines.append("</div>")  # Cierra el contenedor del ticket
    return "".join(response_lines)

def generate_pickup_order_preview(order_details, items):
    style_container = "style='border: 2px solid #ccc; padding: 10px; background: #fff; color: #333; max-width: 400px; margin: 20px auto; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'"
    style_header = "style='font-weight: bold; color: #d10000; margin-bottom: 10px; border-bottom: 1px solid #d10000; padding-bottom: 5px;'"
    style_list = "style='list-style-type: none; padding-left: 0; margin-top: 10px; margin-bottom: 10px;'"
    style_item = "style='margin-bottom: 5px; padding-left: 0;'"

    items_formatted = "".join([f"<li {style_item}>{item['name']} x {item['quantity']}</li>" for item in items])

    response_lines = [
        f"<div {style_container}>",
        f"<h3 {style_header}>Resumen del Pedido para Recogida</h3>",
        f"<p {style_header}>Teléfono: {order_details.get('phone', 'Teléfono no proporcionado')}</p>",
        f"<p {style_header}>Método de Pago: {order_details.get('method', 'Método no proporcionado')}</p>",
        f"<p {style_header}>Tiempo de Recogida: {order_details.get('pickup_time', 'Tiempo no proporcionado')} minutos</p>",
        f"<p {style_header}>Productos solicitados:</p>",
        f"<ul {style_list}>{items_formatted}</ul>",
        f"<p>Para confirmar tu pedido, escribe o haz clic en '<strong>confirmar pedido</strong>'.</p>",
        f"<p>Si necesitas modificar algún dato, escribe '<strong>modificar</strong>'.</p>",
        "</div>"
    ]

    return "".join(response_lines)


def parse_order_items(prompt):
    """
    Parses the items from user input and returns a list of item dictionaries.
    Expected input format: '2 chicken, 3 beer' etc.
    """
    items = []
    parts = prompt.split(',')
    for part in parts:
        try:
            quantity, item = part.strip().split(maxsplit=1)
            items.append({"name": item.strip(), "quantity": int(quantity)})
        except ValueError:
            print("Error parsing items: Invalid format used.")
    return items

def clean_json_response(json_response):
    # Eliminar líneas o caracteres que no son parte del contenido JSON
    clean_response = json_response.replace("```json", "").replace("```", "").strip()
    return clean_response

def clean_response(input_text):
    # Elimina los marcadores específicos de tu respuesta
    clean_text = input_text.replace("```html", "").replace("```", "")
    return clean_text