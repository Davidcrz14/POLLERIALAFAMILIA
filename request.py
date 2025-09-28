import requests
from config import API_URL

def get_api_response(endpoint, data=None):
    """
    Realiza una petición POST al endpoint de la API especificado.
    Args:
        endpoint (str): El endpoint de la API a donde se hará la petición POST.
        data (dict, optional): Diccionario con los datos a enviar en la petición.
    Returns:
        dict or None: El JSON respuesta de la API convertido a diccionario si la
                      respuesta es exitosa (código 200), None en caso contrario.
    """
    url = f"{API_URL}/{endpoint}"
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_product_info(product_name=None):
    """
    Obtiene información de productos desde la API.
    Args:
        product_name (str, optional): Nombre del producto a buscar. Si no se proporciona, se devolverán todos los productos.
    Returns:
        dict or None: Detalles del producto si la consulta es exitosa, None si no se encuentra.
    """
    data = {'name': product_name} if product_name else {}
    return get_api_response('api/get-products', data=data)

def get_promotion_info(promotion_name=None):
    """
    Obtiene información de promociones desde la API.
    Args:
        promotion_name (str, optional): Nombre de la promoción a buscar. Si no se proporciona, se devolverán todas las promociones.
    Returns:
        dict or None: Detalles de la promoción si la consulta es exitosa, None si no se encuentra.
    """
    data = {'name': promotion_name} if promotion_name else {}
    return get_api_response('api/get-promotions', data=data)

def store_order(data):
    """
    Envía un pedido a la API para ser registrado.
    Args:
        data (dict): Diccionario con los datos del pedido, incluyendo el user_id encriptado,
                     el total, la nota, la referencia, el método de pago, el tipo de orden,
                     el tipo de compra y los productos con sus detalles.
    Returns:
        dict or None: Respuesta de la API convertida a diccionario si la respuesta es exitosa (código 200),
                      None en caso contrario.
    """
    data_= {'data': data}
    return get_api_response('api/store-order', data=data_)