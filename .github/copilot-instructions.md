# Instrucciones de Copiloto para el Asistente de IA de Pollería La Familia

## Resumen del Proyecto

Este sistema de IA conversacional basado en Flask se utiliza para un restaurante peruano de pollos rostizados y gestiona los pedidos de los clientes mediante procesamiento de lenguaje natural. El sistema utiliza modelos GPT de OpenAI para procesar conversaciones, clasificar las intenciones de los usuarios y gestionar flujos de trabajo complejos de pedidos mediante sesiones con estado.

## Arquitectura y componentes principales

### Patrón de máquina de estados
El sistema opera con una sofisticada máquina de estados de conversación almacenada en sesiones de Flask:
- **`conversation_state`**: Rastrea el contexto del pedido, el estado del usuario y las banderas de conversación
- **`messages`**: Mantiene el historial completo de conversaciones de OpenAI para el contexto
- Estados clave: `listening`, `collecting_items`, `choosing_type`, `collecting_address`, `confirming_order`

### Diseño modular
- **`app.py`**: Aplicación principal de Flask con lógica de máquina de estados y manejadores de rutas
- **`helpers.py`**: Funciones de integración con OpenAI (`openai_request`, `preprocess_and_classify`)
- **`request.py`**: Cliente API para datos de productos/promociones y almacenamiento de pedidos
- **`response.py`**: Generación de HTML para la visualización de productos/promociones
- **`keywords.py`**: Palabra clave de clasificación de intenciones Conjuntos
- **`utilities.py`**: Utilidades de análisis y formato de datos

## Patrones de desarrollo críticos

### Sistema de clasificación de intenciones
Utiliza OpenAI para clasificar los mensajes de los usuarios en categorías:
```python
# Categorías clave: "Hacer un pedido", "Confirmar pedido", "Promociones", "Productos en la carta", "Otro tema"
result = preprocess_and_classify(raw_prompt, conversation_state)
```

### Indicadores de conversación
Dos indicadores importantes controlan el comportamiento de la IA:
- **`is_modifying_order`**: Cuando es verdadero, enruta los mensajes relacionados con el pedido a la conversación general.
- **`in_conversation_mode`**: Se activa para consultas de productos/promociones; afecta a la lógica de clasificación.

### Patrones de integración de OpenAI
- **`openai_request(instruction, prompt)`**: Solicitudes únicas con instrucciones del sistema.
- **`openai_request_context(instruction, prompt, mensajes)`**: Solicitudes contextuales que utilizan el historial de conversaciones
- Utilice siempre GPT-4-turbo para tareas de análisis complejas (confirmación de pedidos, análisis de artículos)

### Gestión de sesiones
**Local vs. Producción**: Bloques de configuración comentados para sesiones de sistema de archivos (locales) vs. Redis (producción). CORS configurado para la lista blanca de dominios específicos en producción.

### Flujo de trabajo de procesamiento de pedidos
1. **Recolección de artículos**: Utiliza `smart_parse_order_items()` con IA para analizar el lenguaje natural y convertirlo en artículos estructurados.
2. **Selección de tipo**: La entrega frente a la recogida se ramifica en diferentes flujos de recopilación de datos.
3. **Recolección de datos**: Solicitudes secuenciales de dirección, teléfono y pago según el tipo de pedido.
4. **Confirmación**: La IA genera JSON para la integración con el backend de Laravel.

## Puntos de integración de la API

### Dependencias externas
- **API de producto**: `get_product_info()` - obtiene los artículos del menú y sus precios.
- **API de promociones**: `get_promotion_info()` - obtiene las promociones actuales.
- **API de pedidos**: `store_order()` - envía los pedidos completados al backend de Laravel.
- **API de OpenAI**: GPT-4-turbo para el procesamiento del lenguaje natural.

### Estructuras de datos
Los pedidos utilizan un formato estructurado para la integración con Laravel:
```json
{
"name": "product_name",
"quantity": 2,
"unit_price": 15.50,
"order_type": "ai_assistant",
"delivery_zone": "Zona 1",
"encrypted_user_id": "user_id"
}
```

## Configuración del entorno

### Desarrollo vs. Producción
- **Local**: Utiliza sesiones del sistema de archivos, CORS abierto, API localhost
- **Producción**: Sesiones de Redis, CORS restringido por dominio, URL de API activa
- Los bloques de configuración se comentan o descomentan según el entorno

### Variables de entorno obligatorias
- `OPENAI_API_KEY`: Clave de API de OpenAI en `config.py`
- `API_URL`: Punto final de la API de backend (localhost vs. producción)
- Detalles de la conexión de Redis para sesiones de producción

## Pruebas y depuración

### Puntos finales clave
- **`/ask`**: Punto final de la conversación principal (POST con JSON: `{prompt, user_id, user_name}`)
- **`/reset_session`**: Borra el estado de la conversación (GET)
- **`/test`**: Punto final de comprobación de estado (GET)

### Patrones de depuración
Las extensas sentencias `print()` rastrean las transiciones de estado:
```python
print("status: " + status) # Estado del procesamiento del pedido
print("category") # Resultados de la clasificación de intenciones
```

## Flujos de trabajo de desarrollo

### Añadir nuevas categorías de intenciones
1. Añadir palabras clave a `keywords.py`
2. Actualizar la lógica de clasificación en `preprocess_and_classify()`
3. Añadir un controlador de ruta en `route_message_based_on_category()`
4. Crear una función de controlador específica siguiendo el patrón de nomenclatura: `handle_{category}_queries()`

### Modificar el flujo de pedidos
Las transiciones de estado están en `handle_order_process()` con controladores específicos de estado:
- Seguir el patrón de nombres: `handle_collecting_{field}()`
- Actualizar el estado de la conversación y añadir un mensaje de respuesta
- Añadir siempre a la lista de mensajes antes de devolver

### Generación de respuestas HTML
Utilice `generate_html_response()` para listas de productos/promociones con un estilo uniforme en toda la aplicación. CSS en línea con el color de marca `#de3210` para los encabezados.


## Herramientas MCP disponibles

- **filesystem** (`npx @modelcontextprotocol/server-filesystem@latest`): permite acceder a carpetas complementarias fuera del workspace si necesitas revisar archivos compartidos. Úsalo solo cuando falte referencia dentro del repositorio.
- **microsoft-docs**: consulta documentación oficial de Microsoft. Recurre a ella para confirmar configuraciones de Windows/Redis o patrones de despliegue cuando la base de código no cubra esos detalles.
- **deepwiki**: ofrece búsquedas semánticas en wikis de GitHub. Útil para investigar repositorios externos relacionados con integraciones (por ejemplo, si el API Laravel cambia y necesitas rastrear documentación pública).
- **context7** y **upstash/context7**: sirven para recuperar documentación actualizada de librerías. Actívalas cuando debas validar firmas o ejemplos de uso de Flask, Redis, OpenAI u otras dependencias listadas en `requirements.txt`.
- **playwright** (`@playwright/mcp`): automatiza navegadores. Generalmente innecesario aquí, salvo que quieras generar capturas o flujos manuales contra la API web pública.
- **sequentialthinking**: ayuda a desglosar tareas ambiguas en pasos ordenados. Empléala si el flujo de trabajo requiere un plan más profundo antes de modificar estados de conversación o integraciones.
- **makenotion/notion-mcp-server**: permite actualizar documentación operativa en Notion. Úsalo solo si te piden sincronizar cambios de procesos o menús con el espacio de la pollería.
- **wallhaven-mcp** y **wallhaven-notion**: orientadas a colecciones de wallpapers; no aplican al flujo de pedidos, por lo que puedes ignorarlas salvo que surja una tarea explícita.


