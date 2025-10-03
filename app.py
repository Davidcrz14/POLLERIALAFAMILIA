from flask import Flask, request, jsonify, session
from flask_session import Session  # Asegúrate de instalar esto con pip install Flask-Session
from flask_cors import CORS
from openai import OpenAI
import redis
import json
import re

from helpers import smart_parse_order_items, preprocess_and_classify, openai_request, openai_request_context
from keywords import KEY_PHRASES_ORDER, KEY_PHRASES_PRODUCT_PROMOTIONS, KEY_PHRASES_PRODUCT, KEY_PHRASES_PROMOTIONS
from request import get_product_info, get_promotion_info, store_order
from response import generate_html_response
from config import OPENAI_API_KEY
from utilities import format_order_review, parse_payment_method, clean_json_response, generate_pickup_order_preview

app = Flask(__name__)

####################### local ##########################
CORS(app, supports_credentials=True)  # Habilita el soporte para credenciales
# Configura CORS para permitir tu dominio y manejar cookies de sesión

#Configuración local
# Configuración para la sesión
app.config["SECRET_KEY"] = "una_clave_secreta_muy_segura"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)

####################### producción ######################
"""
CORS(app, supports_credentials=True, origins=["http://www.pollerialafamilia.com", "https://www.pollerialafamilia.com",
                                              "http://pollerialafamilia.com", "https://pollerialafamilia.com"],
     allow_headers=["Content-Type", "Authorization", "X-Session-Id"],
     expose_headers=["X-Session-Id"])
# Esto habilita CORS para todos los dominios y rutas; ajusta según necesidad.

# Configura la aplicación para utilizar sesiones basadas en cookies seguras
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
    SESSION_REFRESH_EACH_REQUEST=True,
    SECRET_KEY="una_clave_secreta_muy_segura",
    SESSION_TYPE="redis",
    SESSION_REDIS=redis.Redis(
        host='red-cq5nvg6ehbks73brnkvg',
        port=6379,
        ssl_cert_reqs=None
    ),
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True
)
Session(app)
"""

###########################################3

# Configuración de la sesión usando archivos
"""
app.config["SECRET_KEY"] = "una_clave_secreta_muy_segura"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)
"""

###########################################3
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/ask', methods=['POST'])
def ask_gpt():
    data = request.json
    raw_prompt = data.get('prompt', "").lower()
    user_id_encrypted = data.get('user_id')  # Recibe el ID del usuario encriptado
    user_name = data.get('user_name')  # Recibe el nombre del usuario

    # Inicializa el estado de la conversación si no existe
    if 'conversation_state' not in session:
        reset_conversation_state(user_name)

    conversation_state = session['conversation_state']
    messages = session['messages']

    # Procesa y clasifica el mensaje del usuario
    result = preprocess_and_classify(raw_prompt, conversation_state)
    category = result['categoria']
    prompt = result['mensaje']

    print(category)

    # Añade el mensaje del usuario a la sesión
    messages.append({"role": "user", "content": prompt})
    update_conversation_state(conversation_state, category, prompt)

    # Deriva la respuesta según la categoría
    return route_message_based_on_category(category, prompt, messages, conversation_state, user_id_encrypted)

def reset_conversation_state(user_name):
    """Resets the conversation state for a new session."""
    session['conversation_state'] = {
        "status": "listening",
        "context": "general",
        "user_name": user_name,
        "order": {
            "items": [],
            "details": {}
        },
        "last_topic": "general",
        "last_prompt": "",
        "is_modifying_order": False,
        "in_conversation_mode": False  # Añadir el nuevo flag aquí
    }
    session['messages'] = []
    if user_name:
        session['messages'].append({"role": "system", "content": f"El usuario se llama {user_name}."})

    # Mensaje adicional como una instrucción fija
    confirm_instruction = ("Tener en cuenta que si se desea confirmar un pedido, el usuario debe decir 'confirmar pedido'. "
                           "Eso haz saber cuando veas que el usuario quiere confirmar o si está seguro")
    session['messages'].append({"role": "system", "content": confirm_instruction})

def update_conversation_state(context, category, prompt):
    context['last_topic'] = category
    context['last_prompt'] = prompt
    # Actualizar el flag in_conversation_mode según la categoría del mensaje
    if category in ["Promociones", "Productos en la carta"]:
        context['in_conversation_mode'] = True

def route_message_based_on_category(category, prompt, messages, conversation_state, user_id_encrypted):
    if category == "Hacer un pedido":
        # Chequear si se está en modo de modificación de pedido
        if conversation_state["is_modifying_order"]:
            # Si is_modifying_order es true, manejar como conversación general
            return handle_general_conversation(prompt, messages)
        else:
            # Procesar normalmente según el contexto actual
            if conversation_state["context"] == "general":
                return initiate_order_conversation(prompt, messages, conversation_state)
            elif conversation_state["context"] == "ordering":
                return handle_order_process(prompt, messages, conversation_state)
    elif category == "Confirmar Pedido":
        return handle_confirm_order(messages, user_id_encrypted)
    elif category == "Promociones":
        return handle_promotion_queries(prompt, messages)
    elif category == "Productos en la carta":
        return handle_product_queries(prompt, messages)
    return handle_general_conversation(prompt, messages)

def handle_confirm_order(messages, user_id_encrypted):
    # Obtener información de los productos
    api_data = get_product_info()

    # Convertir la información de productos a un formato JSON que pueda ser utilizado en la instrucción
    products_json = json.dumps(api_data)

    # Preparar una instrucción para OpenAI GPT solicitando la estructura de datos en JSON
    instruccion = (
        "Genera un objeto JSON que sea directamente utilizable en un backend de Laravel sin necesidad de "
        "ajustes adicionales. El JSON debe listar productos con 'name', 'quantity' y 'unit_price'. Utiliza la "
        "siguiente información de productos para los nombres y precios: {products_json}. Incluye "
        "'order_type' establecido como 'ai_assistant', una dirección completa con 'street', 'number' y 'district', "
        "así como 'delivery_zone', 'phone', 'total_amount', 'payment_method', 'note' y 'reference'. "
        "Los campos 'note' y 'reference' deben incorporar automáticamente cualquier información relevante "
        "de la conversación que no esté incluida en otros campos. El JSON debe ser preciso, estar estructurado "
        "de forma clara y listo para uso inmediato en Laravel. Asegúrate de que todos los keys están en inglés y que "
        "el formato del JSON es directo y sin comentarios adicionales. "
        "Si el pedido es para recogida en local, utiliza los siguientes valores para la dirección: "
        "'street': 'Av. Antigua Panamericana Sur Mz:41 Lt:1', 'number': 'sn', 'district': 'Chilca', "
        "'delivery_zone': 'Local - Chilca'. No olvides todos los demás datos."
    ).format(products_json=products_json)

    prompt = ("Crea un objeto JSON con la estructura requerida, directamente y sin comentarios, para integración inmediata en un backend "
              "de Laravel. Por favor, enfócate en la claridad y precisión del formato JSON. DIRECTO CON LA SOLUCIÓN, NADA DE RODEOS")

    # Llamar a openai_request pasando los mensajes actuales como contexto
    json_response = openai_request_context(instruccion, prompt, messages)
    print("Respuesta de confirmación:")
    print(json_response)

    # Convertir la respuesta JSON a un diccionario Python para procesar
    if isinstance(json_response, str):
        cleaned_json_response = clean_json_response(json_response)
        try:
            # Convertir la respuesta JSON a un diccionario Python para procesar
            order_data = json.loads(cleaned_json_response)
            order_data['encrypted_user_id'] = user_id_encrypted

            # Enviar el pedido a la API para su registro
            api_response = store_order(order_data)
            if api_response:
                response_message = "Tu pedido ha sido confirmado y registrado con éxito. ¡Gracias por tu compra! Llegaremos en un máximo de 30 minutos."
            else:
                response_message = "Hubo un problema al registrar tu pedido. Por favor, intenta nuevamente."
        except json.JSONDecodeError:
            response_message = "Error al procesar la información del pedido. Verifica que la respuesta esté en formato JSON válido."
    else:
        response_message = "Respuesta inesperada. Se esperaba un JSON."

    # Agregar el mensaje de respuesta a los mensajes de la conversación y devolver la respuesta
    messages.append({"role": "assistant", "content": response_message})
    return jsonify({"response": response_message})

def handle_promotion_queries(prompt, messages):
    api_data = get_promotion_info()  # Suponiendo que esta función existe
    html_response = generate_html_response(api_data, "promotions")
    messages.append({"role": "assistant", "content": html_response})
    session['conversation_state']['last_context'] = "promotions"
    session['messages'] = messages
    return jsonify({"response": html_response})

def handle_product_queries(prompt, messages):
    api_data = get_product_info()  # Suponiendo que esta función existe
    html_response = generate_html_response(api_data, "products")
    messages.append({"role": "assistant", "content": html_response})
    session['conversation_state']['last_context'] = "products"
    session['messages'] = messages
    return jsonify({"response": html_response})

def reset_order_state(conversation_state):
    """
    Esta función limpia la información del pedido actual en el estado de la conversación.
    """
    conversation_state["order"] = {
        "items": [],
        "details": {}
    }
    conversation_state["status"] = "collecting_items"  # Reiniciar el estado a la recolección de items
    conversation_state["context"] = "ordering"  # Establecer el contexto específico para el pedido

def initiate_order_conversation(prompt, messages, conversation_state):
    reset_order_state(conversation_state)  # Resetear el estado del pedido
    response = "Estás ordenando un pedido. ¡Claro! Por favor, indica los productos que deseas ordenar junto con la cantidad de cada uno."
    messages.append({"role": "assistant", "content": response})
    return jsonify({"response": response})

def handle_order_process(prompt, messages, conversation_state):
    order = conversation_state["order"]
    status = conversation_state["status"]

    print("status: "+ status)

    if status == "collecting_items":
        # Lógica para manejar la recolección de items
        handle_collecting_items(prompt, messages, conversation_state, order)
    elif status == "choosing_type":
        # Lógica para manejar la elección entre recoger o delivery
        handle_choosing_type(prompt, messages, conversation_state)
    elif status == "collecting_address":
        # Lógica para manejar la recolección de dirección
        handle_collecting_address(prompt, messages, conversation_state, order)
    elif status == "collecting_zone":
        # Lógica para manejar la recolección de zona
        handle_collecting_zone(prompt, messages, conversation_state, order)
    elif status == "collecting_phone":
        # Lógica para manejar la recolección del teléfono
        handle_collecting_phone(prompt, messages, conversation_state, order)
    elif status == "collecting_payment_method":
        # Lógica para manejar la recolección del método de pago
        handle_collecting_payment_method(prompt, messages, conversation_state, order)
    elif status == "collecting_pickup_phone":
        # Lógica para manejar la recolección del teléfono para recogida
        handle_collecting_pickup_phone(prompt, messages, conversation_state, order)
    elif status == "collecting_pickup_payment_method":
        # Lógica para manejar la recolección del método de pago para recogida
        handle_collecting_pickup_payment_method(prompt, messages, conversation_state, order)
    elif status == "collecting_pickup_time":
        # Lógica para manejar la recolección del tiempo de recogida
        handle_collecting_pickup_time(prompt, messages, conversation_state, order)
    elif status == "confirming_order":
        # Lógica para confirmar el pedido
        handle_confirming_order(prompt, messages, conversation_state, order)
    else:
        # Manejo de error o estado no reconocido
        handle_unknown_state(messages)

    return jsonify({"response": messages[-1]['content']})  # Devuelve la última respuesta agregada

def handle_collecting_items(prompt, messages, conversation_state, order):
    items_detail = smart_parse_order_items(prompt)
    if items_detail:
        order["items"].extend(items_detail)
        conversation_state["status"] = "choosing_type"
        response = "¿Este pedido es para recoger en el local o para delivery? Por favor especifica."
    else:
        response = "No pude entender los ítems correctamente. Por favor indica los productos y sus cantidades nuevamente."
    messages.append({"role": "assistant", "content": response})

def handle_choosing_type(prompt, messages, conversation_state):
    recoger_keywords = ["recoger", "recojo"]

    if any(keyword in prompt.lower() for keyword in recoger_keywords):
        conversation_state["status"] = "collecting_pickup_phone"
        response = "Entendido, para recoger. Por favor, proporciona tu número de teléfono."
    else:
        conversation_state["status"] = "collecting_address"
        response = "Para delivery. Por favor, proporciona tu dirección completa."

    messages.append({"role": "assistant", "content": response})

def handle_collecting_address(prompt, messages, conversation_state, order):
    order["details"]["address"] = prompt
    conversation_state["status"] = "collecting_zone"
    response = ("Gracias. Ahora especifica la zona de entrega. Las zonas disponibles son: "
                "<ul>"
                "<li>Zona 1: Cobertura en el mismo Chilca. Costo: S/1.00.</li>"
                "<li>Zona 2: Cobertura extendida alrededor de Chilca, incluyendo áreas residenciales y comerciales. Costo: S/2.50.</li>"
                "<li>Zona 3: Cobertura en 15 de Enero, Papa León, Olof Palme, Benjamin, Salinas, Playa Yaya, Playa San Pedro. Costo: S/3.00.</li>"
                "</ul>")
    messages.append({"role": "assistant", "content": response})

def handle_collecting_zone(prompt, messages, conversation_state, order):
    order["details"]["zone"] = prompt
    conversation_state["status"] = "collecting_phone"
    response = "Perfecto. ¿Cuál es tu número de teléfono?"
    messages.append({"role": "assistant", "content": response})

def handle_collecting_phone(prompt, messages, conversation_state, order):
    order["details"]["phone"] = prompt
    conversation_state["status"] = "collecting_payment_method"
    response = "Finalmente, ¿cuál será el método de pago? Opciones disponibles: Tarjeta, Efectivo, Transferencia, Yape."
    messages.append({"role": "assistant", "content": response})

def handle_collecting_payment_method(prompt, messages, conversation_state, order):
    # Parsear método de pago del prompt
    payment_method_info = parse_payment_method(prompt)
    if "method" in payment_method_info:
        order["details"].update(payment_method_info)  # Actualizar con el método de pago
    else:
        order["details"]["method"] = "Desconocido"  # Manejar caso de método no identificado

    # Obtener información actualizada de productos desde la base de datos
    # Asignando los precios correctamente a los detalles de los productos
    product_names = [item["name"] for item in order["items"]]
    products = get_product_info()
    product_details = {product["name"]: product["price"] for product in products}

    print(order['details'].get('zone'))

    # Preparar datos para enviar a la IA
    order_info = {
        "items": order["items"],
        "product_details": product_details,
        "zone_fee": order['details'].get('zone')  # Asegúrate de que esta clave existe y es correcta
    }

    # Instrucción detallada para OpenAI
    detailed_instruction = (
        "Utiliza la información de los productos y detalles del pedido proporcionados para generar un fragmento de HTML. "
        "Primero, compara y empareja los nombres de los productos en el pedido con los nombres en los detalles de los productos, considerando posibles variaciones o abreviaturas. "
        "Luego, para cada producto en el pedido, crea un elemento <li> dentro de un <ul> con el formato: "
        "'{nombre del producto} x {cantidad} - {costo total}', donde: "
        "'nombre del producto' es el nombre tal como debería aparecer basándote en los detalles de los productos, "
        "'cantidad' es la cantidad solicitada en el pedido, "
        "'precio unitario' corresponde al precio en 'product_details' para ese producto, y "
        "'costo total' es el cálculo del 'precio unitario' multiplicado por la 'cantidad'. "
        "Agrega una línea <hr>, y luego presenta los gastos adicionales según la zona de entrega especificada en 'order_details' con un formato adecuado. "
        "Si la zona es 'zona 1', añade un costo de 1 sol. Si es 'zona 2', el costo es de 2.50 soles. Para 'zona 3', el costo es de 3.00 soles. "
        "Suma estos gastos al total de los productos para calcular el total final. "
        "Muestra esta información en un formato que detalle 'Gastos por entrega' y 'Total a pagar'. "
        "El HTML generado solo debe contener elementos <ul>, <li>, <hr>, y otros necesarios para mostrar los costos, sin incluir etiquetas <html>, <body> o cualquier otra estructura HTML no solicitada."
    )

    # Convertir a JSON y enviar a OpenAI
    json_order_info = json.dumps(order_info, ensure_ascii=False)
    openai_response = openai_request(detailed_instruction, json_order_info)

    # Formatear la revisión del pedido
    order_review = format_order_review(openai_response, "delivery" if "address" in order['details'] else "pickup", conversation_state["user_name"], order['details'])

    # Construir la respuesta HTML
    response_html = f"""
    <div>
        <h2>Confirmación de tu pedido</h2>
        <p>{order_review}</p>
        <p>Por favor, revisa todos los detalles de tu pedido cuidadosamente antes de confirmar. Una vez confirmado, tu pedido será registrado y enviado a la pollería, y no podrás realizar cambios.</p>
        <ul>
            <li>Para confirmar tu pedido, escribe o haz clic en '<strong>confirmar pedido</strong>'.</li>
            <li>Si necesitas modificar algún dato, escribe '<strong>modificar</strong>'.</li>
        </ul>
    </div>
    """
    messages.append({"role": "assistant", "content": response_html})
    return response_html

def handle_collecting_pickup_phone(prompt, messages, conversation_state, order):
    order["details"]["phone"] = prompt
    conversation_state["status"] = "collecting_pickup_payment_method"
    response = "¿Cuál será el método de pago? Opciones disponibles: Tarjeta, Efectivo, Transferencia, Yape."
    messages.append({"role": "assistant", "content": response})

def handle_collecting_pickup_payment_method(prompt, messages, conversation_state, order):
    payment_method_info = parse_payment_method(prompt)
    if "method" in payment_method_info:
        order["details"].update(payment_method_info)
        conversation_state["status"] = "collecting_pickup_time"
        response = "¿En cuánto tiempo pasarás a recoger tu pedido? (Debe ser en al menos 15 minutos)."
    else:
        response = "No pude entender el método de pago. Por favor, indica nuevamente: Tarjeta, Efectivo, Transferencia, Yape."
    messages.append({"role": "assistant", "content": response})

def handle_collecting_pickup_time(prompt, messages, conversation_state, order):
    print("Entramos OK")
    try:
        # Extraer el primer número de la cadena usando una expresión regular
        pickup_time_match = re.search(r'\d+', prompt)
        if pickup_time_match:
            pickup_time = int(pickup_time_match.group())
            order["details"]["pickup_time"] = pickup_time
            conversation_state["status"] = "confirming_order"
            response = generate_pickup_order_preview(order["details"], order["items"])
        else:
            raise ValueError("No se encontró un número en el prompt")
    except ValueError as e:
        print("Ocurrió algo:", e)
        response = "No pude entender el tiempo de recogida. Por favor, proporciona un tiempo válido en minutos."
    messages.append({"role": "assistant", "content": response})

def handle_confirming_order(prompt, messages, conversation_state, order):
    prompt_lower = prompt.lower()
    if "confirmar" in prompt_lower:
        response = "Tu pedido ha sido confirmado y está siendo procesado. Gracias por tu compra."
        conversation_state["status"] = "order_confirmed"
        #conversation_state["is_modifying_order"] = False  # Resetear la bandera al confirmar el pedido
    elif "modificar" in prompt_lower:
        #response = handle_modification_request(prompt, messages, conversation_state, order)
        response = "Dinos qué quieres modificar."
        conversation_state["is_modifying_order"] = True
    else:
        response_html = """
        <p>Por favor revisa tu pedido y confirma o especifica qué deseas modificar. Aquí están las opciones disponibles:</p>
        <ul>
            <li>Modificar dirección: Proporciona la nueva dirección completa.</li>
            <li>Cambiar teléfono: Proporciona el nuevo número de teléfono.</li>
            <li>Modificar zona: Especifica la nueva zona de entrega. Zonas disponibles: Zona 1, Zona 2, Zona 3.</li>
            <li>Cambiar método de pago: Elige el nuevo método de pago. Opciones disponibles: Tarjeta, Efectivo, Transferencia, Yape.</li>
            <li>Modificar productos: Indica los productos que deseas ordenar junto con la cantidad de cada uno.</li>
        </ul>
        """
        response = response_html
    messages.append({"role": "assistant", "content": response})
    return response

def handle_unknown_state(messages):
    response = "Ha ocurrido un error inesperado. Por favor comienza de nuevo."
    messages.append({"role": "assistant", "content": response})

############ Handle General Conversation #############
def handle_general_conversation(prompt, messages):
    try:
        chat_completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        gpt_response = chat_completion.choices[0].message.content
        messages.append({"role": "assistant", "content": gpt_response})
        session['messages'] = messages
        return jsonify({"response": gpt_response})
    except Exception as e:
        session.pop('messages', None)  # Clear session on error
        session.pop('conversation_state', None)
        return jsonify({"error": str(e), "message": "Lo siento, no pude procesar tu solicitud debido a un error."}), 500

@app.route('/reset_session', methods=['GET'])
def reset_session():
    session.clear()
    return jsonify({"message": "Sesión reiniciada con éxito."})

@app.route('/', methods=['GET'])
def home():
    """Ruta de inicio con información de la API"""
    return jsonify({
        "service": "Pollería La Familia - AI Assistant",
        "status": "online",
        "version": "1.0.0",
        "endpoints": {
            "POST /ask": "Enviar mensaje al asistente de IA",
            "GET /reset_session": "Reiniciar sesión de conversación",
            "GET /test": "Health check del servicio"
        },
        "documentation": "https://github.com/atuctov-stack/POLLERIALAFAMILIA",
        "example_request": {
            "url": "/ask",
            "method": "POST",
            "body": {
                "prompt": "Quiero ver las promociones",
                "user_id": "user123",
                "user_name": "Juan Pérez"
            }
        }
    }), 200

@app.route('/test', methods=['GET'])
def test():
    return "Hola, todo OK", 200

if __name__ == "__main__":
    app.run(debug=True)
