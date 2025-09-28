def generate_html_response(data, category):
    # Header que cambia según la categoría
    header = "<h2 style='color: #de3210;'>Productos en la carta disponibles:</h2>" if category == "products" \
        else "<h2 style='color: #de3210;'>Promociones Actuales:</h2>"

    # Generar las filas de la tabla
    rows = []
    for i, item in enumerate(data):
        background_color = '#f2f2f2' if i % 2 == 0 else '#ffffff'
        row = f"<tr style='background-color: {background_color};'>"
        row += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'><img src='{item['image']}' alt='Imagen'></td>"
        row += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'>{item['name']}</td>"
        row += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'>{item['description']}</td>"
        if category == "products":
            row += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'>S/. {item['price']}</td></tr>"
        else:
            row += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'>Ahora: S/. {item['promotional_price']}</td>"
            row += f"<td style='padding: 8px; border-bottom: 1px solid #ddd;'>Incluye: {item['included']}</td></tr>"
        rows.append(row)

    # Estilos de la tabla
    table_style = "<style>.product-table {width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden;} .product-table th {background-color: #de3210; color: white; padding: 12px;} .product-table img {width: 100px; height: auto;}</style>"

    # Cabecera de la tabla, ahora incluyendo una columna para la imagen
    table_header = "<table class='product-table'><thead><tr><th>Imagen</th><th>Nombre</th><th>Descripción</th><th>Precio</th>"
    if category == "promotions":
        table_header += "<th>Incluye</th>"
    table_header += "</tr></thead><tbody>"

    # Pie de la tabla
    table_footer = "</tbody></table>"

    # Construcción de la respuesta HTML completa
    return f"{table_style}{header}{table_header}{''.join(rows)}{table_footer}"
