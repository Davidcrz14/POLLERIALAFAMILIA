# helpers.py
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def openai_request(instruccion, prompt, model="gpt-4-turbo"):
    """
    Función general para enviar solicitudes a OpenAI. Esta función envía una instrucción específica
    junto con el prompt del usuario y devuelve la respuesta estructurada de la IA.
    """
    full_prompt = f"{instruccion}\nIndicación: {prompt}"
    messages = [
        {"role": "system", "content": "Procesa la siguiente solicitud basada en la instrucción proporcionada."},
        {"role": "user", "content": full_prompt}
    ]
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error utilizando OpenAI: {e}")
        return None

def openai_request_context(instruccion, prompt, messages, model="gpt-4-turbo"):
    """
    Función general para enviar solicitudes a OpenAI. Esta función envía una instrucción específica
    junto con el prompt del usuario y utiliza los mensajes proporcionados como contexto para la conversación.
    Devuelve la respuesta estructurada de la IA.
    """
    full_prompt = f"{instruccion}\nIndicación: {prompt}"
    # Añadir el prompt al final de los mensajes existentes
    messages.append({"role": "system", "content": "Procesa la siguiente solicitud basada en la instrucción proporcionada."})
    messages.append({"role": "user", "content": full_prompt})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error utilizando OpenAI: {e}")
        return None

def preprocess_and_classify(prompt, context):
    last_topic = context['last_topic'] if 'last_topic' in context else 'general'
    last_prompt = context['last_prompt'] if 'last_prompt' in context else ''
    is_modifying_order = context.get('is_modifying_order', False)
    in_conversation_mode = context.get('in_conversation_mode', False)

    print("last_prompt: " + last_prompt)
    print("last_topic: " + last_topic)
    print("is_modifying_order: " + str(is_modifying_order))
    print("in_conversation_mode: " + str(in_conversation_mode))

    # Agregando la nueva categoría "Confirmar pedido"
    if "confirmar pedido" in prompt.lower() or "confirmo pedido" in prompt.lower():
        return {'categoria': 'Confirmar Pedido', 'mensaje': prompt}

    if "modificar" in prompt.lower():
        context['is_modifying_order'] = True
        return {'categoria': 'Modificar Pedido', 'mensaje': prompt}

    # Ajuste de la instrucción para simplificar la lógica
    instruction = (
        "Dado el contexto actual de la conversación, que incluye el último tema '{last_topic}', "
        "la última pregunta '{last_prompt}', si el usuario está modificando un pedido ('{is_modifying_order}'), "
        "y si el usuario está en modo conversación sobre promociones o productos ('{in_conversation_mode}'), "
        "clasificar el siguiente mensaje del usuario: '{prompt}'. "
        "Si el mensaje explícitamente solicita hacer un pedido, o que contiene datos como zona, dirección, teléfono, números de contacto, "
        "menciona métodos de pago específicos como 'Yape', 'efectivo', 'tarjeta de crédito', cualquier otro método de pago, "
        "'recoger en local', 'delivery', o menciona tiempo en minutos, "
        "clasificar inmediatamente como 'Hacer un pedido', dando prioridad a esta clasificación sobre cualquier otro modo de conversación activo. "
        "Si '{is_modifying_order}' es verdadero, clasificar como 'Otro tema'. "
        "Si '{in_conversation_mode}' es verdadero y el mensaje no cumple con los criterios para ser clasificado como 'Hacer un pedido', "
        "clasificar automáticamente como 'Otro tema', independientemente de cualquier otro contenido del mensaje. "
        "Si no se cumplen las condiciones anteriores y '{in_conversation_mode}' no está activo, "
        "identificar si el mensaje está solicitando información sobre: "
        "1. Hacer un pedido, 2. Promociones, 3. Productos en la carta, 4. Otro tema. "
        "Corrige errores ortográficos y gramaticales y considera si el mensaje es un seguimiento de un tema previo "
        "o una nueva consulta independiente. "
        "La respuesta debe estar en el formato {{'categoria': 'nombre_categoria', 'mensaje': 'texto_limpio'}}. "
        "No incluyas ningún otro texto o formato en la respuesta. "
    ).format(
        last_topic=last_topic,
        last_prompt=last_prompt,
        is_modifying_order=is_modifying_order,
        in_conversation_mode=in_conversation_mode,
        prompt=prompt
    )

    try:
        response = openai_request(instruction, prompt)
        if response:
            response_data = eval(response)
            category = response_data.get('categoria', 'Otro tema')
            cleaned_text = response_data.get('mensaje', prompt)

            if in_conversation_mode and category == "Otro tema":
                detailed_instruction = (
                    "Analiza el contenido del mensaje para determinar si aún está relacionado con promociones o productos. "
                    "Considera el contexto y el contenido del mensaje. "
                    "Además, evalúa si el mensaje contiene una opinión, comentario o solicitud de recomendación sobre los productos o promociones. "
                    "Si el mensaje cumple con alguno de estos criterios, la respuesta debe ser 'True', indicando que aún está relacionado "
                    "con el tema de promociones o productos y que 'in_conversation_mode' debe mantenerse activo. "
                    "Por otro lado, si el mensaje indica claramente una intención de hacer un pedido (por ejemplo, menciona datos de zona, dirección, teléfono, "
                    "o solicita explícitamente hacer un pedido), entonces la respuesta debe ser 'False' porque el mensaje ya no se trata solo "
                    "de discutir promociones o productos sino de realizar una transacción. "
                    "Formato de respuesta esperado: {'is_related': True/False}."
                )
                response = openai_request(detailed_instruction, prompt)
                if response:
                    try:
                        response_data = eval(response)
                        still_related = response_data.get('is_related', False)
                        if still_related:
                            context['in_conversation_mode'] = True
                        else:
                            context['in_conversation_mode'] = False
                    except SyntaxError as e:
                        print(f"Syntax error in the response: {e}")
            elif category in ["Promociones", "Productos en la carta"]:
                context['in_conversation_mode'] = True

            return {'categoria': category, 'mensaje': cleaned_text}
        return {'categoria': 'Otro tema', 'mensaje': prompt}
    except SyntaxError as e:
        print(f"Syntax error in the response: {e}")
        return {'categoria': 'Otro tema', 'mensaje': prompt}
    except Exception as e:
        print(f"Error processing classification: {e}")
        return {'categoria': 'Otro tema', 'mensaje': prompt}

def smart_parse_order_items(prompt):
    """
    Utiliza OpenAI para interpretar y estructurar cadenas de pedidos. Esta instrucción se enfoca en:
    - Corregir errores ortográficos y formatos incorrectos.
    - Identificar y separar las cantidades de los nombres de los productos, incluso cuando los números son parte del nombre (como '1/4 de pollo').
    - Formatear el pedido en una lista clara donde cada elemento consta del nombre del producto seguido por 'x' y la cantidad total correspondiente.

    Ejemplo de entrada: '1/4 de pollo, 8 gaseosas pepsi y 2 porciones de papas fritas'
    Ejemplo de salida esperada: '1/4 de pollo x 1, gaseosas pepsi x 8, porciones de papas fritas x 2'

    Asegúrate de que las cantidades se reflejen correctamente según lo especificado en la entrada y que los números que son parte del nombre del producto no se alteren ni se interpreten como cantidades adicionales.
    """
    instruction = (
        "Por favor, corrige cualquier error ortográfico en la entrada y formatea la información en una lista clara y estructurada. "
        "Cada artículo debe estar claramente separado por comas y presentado en el formato 'nombre del producto x cantidad'. "
        "Es esencial distinguir entre números que son parte integral del nombre del producto (como '1/4 de pollo') y las cantidades de los artículos. "
        "Asegúrate de que cada item esté formateado como 'nombre del producto x cantidad', donde el nombre del producto es seguido por 'x' y la cantidad correspondiente, "
        "y cada item debe estar en una línea nueva precedido por un guion. Esto asegura una interpretación correcta y precisa de la cadena de entrada, "
        "evitando confusiones entre nombres y cantidades."
    )
    response_text = openai_request(instruction, prompt)
    #print(response_text)
    return format_ai_response_as_list(response_text)

def format_ai_response_as_list(text):
    """
    Convierte una cadena de texto formateada por la IA en una lista de diccionarios con nombres de artículos y cantidades.
    Asegura que los números que forman parte del nombre del artículo se mantengan intactos y que las cantidades sean interpretadas correctamente.
    """
    items = []
    lines = text.strip().split('\n')
    for line in lines:
        parts = line.split(' x ')
        if len(parts) == 2:
            item, quantity = [p.strip() for p in parts]
            try:
                quantity = int(quantity) if quantity.isdigit() else float(quantity)
                items.append({"name": item, "quantity": quantity})
            except ValueError:
                print(f"Skipping invalid line: {line}")  # Skip lines that cannot be parsed
    return items
