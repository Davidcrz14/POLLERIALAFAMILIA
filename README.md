# 🐔 Pollería La Familia - Sistema de IA Conversacional### Paso 2: Crear Web Service en Render

1. Ve a tu dashboard de Render: [https://dashboard.render.com](https://dashboard.render.com)
2. Haz clic en el botón **"New +"** (arriba a la derecha)
3. Selecciona **"Web Service"** de las opciones disponibles
4. Conecta tu repositorio de GitHub:
   - Si es primera vez, autoriza a Render a acceder a GitHub
   - Selecciona el repositorio `POLLERIALAFAMILIA`

5. Configura el servicio con los siguientes datos:

   **Información Básica:**
   - **Name**: `polleria-ai-assistant` (o el nombre que prefieras)
   - **Region**: `Oregon (US West)` o la más cercana a tus usuarios
   - **Branch**: `main`
   - **Root Directory**: (dejar vacío)

   **Build & Deploy:**
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

   **Plan:**
   - Selecciona **"Free"** ($0/mes)
   - ⚠️ **Nota**: El servicio dormirá después de 15 minutos de inactividad
   - La primera request después del sleep tardará ~30-50 segundoseligencia artificial basado en Flask y OpenAI GPT para gestión automatizada de pedidos en restaurante de pollos a la brasa.

## 📋 Descripción

Este asistente virtual procesa pedidos mediante lenguaje natural, clasificando intenciones del usuario y manejando flujos completos de compra con una máquina de estados conversacional.

### Características Principales

- 🤖 **Procesamiento de Lenguaje Natural** con GPT-4-turbo
- 🛒 **Gestión Completa de Pedidos** (delivery y recogida)
- 💬 **Máquina de Estados Conversacional** con contexto persistente
- 📦 **Integración con API Laravel** para registro de pedidos
- 🎯 **Clasificación Inteligente de Intenciones** (productos, promociones, pedidos)
- 🔄 **Sesiones Persistentes** con Redis en producción
- 🌐 **CORS Configurado** para integración web

---

## 🚀 Deploy en Render (Plan Free)

### Prerrequisitos

1. Cuenta en [Render](https://render.com)
2. Cuenta en [OpenAI](https://platform.openai.com) con API Key activa
3. Repositorio de GitHub con el código
4. API backend de Laravel desplegada (para endpoints de productos/pedidos)

### Paso 1: Preparar el Código para Plan Free

**IMPORTANTE**: El plan Free de Render **NO incluye Redis**. Vamos a usar sesiones basadas en archivos (filesystem) que funcionan perfectamente para este caso.

En `app.py`, asegúrate de que el bloque de **configuración de producción** esté así:

```python
####################### producción (Free Plan) ######################
CORS(app, supports_credentials=True, origins=["http://www.pollerialafamilia.com", "https://www.pollerialafamilia.com",
                                              "http://pollerialafamilia.com", "https://pollerialafamilia.com"],
     allow_headers=["Content-Type", "Authorization", "X-Session-Id"],
     expose_headers=["X-Session-Id"])

# Configuración para sesiones con filesystem (compatible con Free Plan)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='None',
    SESSION_REFRESH_EACH_REQUEST=True,
    SECRET_KEY=os.environ.get("SECRET_KEY", "una_clave_secreta_muy_segura"),
    SESSION_TYPE="filesystem",  # Cambiado de redis a filesystem
    SESSION_PERMANENT=False,
    SESSION_USE_SIGNER=True
)
Session(app)
```

### Paso 2: Crear Web Service

1. En el dashboard de Render, haz clic en **"New +"** → **"Web Service"**
2. Conecta tu repositorio de GitHub
3. Configura el servicio:

   **Build & Deploy**
   - **Name**: `polleria-ai-assistant`
   - **Region**: Misma región que Redis
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

   **Instance Type**
   - Free (para desarrollo)
   - Starter o superior (para producción con más tráfico)

### Paso 3: Configurar Variables de Entorno

Antes de hacer clic en "Create Web Service", desplázate hasta la sección **"Environment Variables"** y agrega las siguientes:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | `sk-proj-tu-api-key-aqui` |
| `SECRET_KEY` | `genera-una-clave-secreta-aleatoria` |
| `API_URL` | `https://pollerialafamilia.com` |
| `FLASK_ENV` | `production` |

**⚠️ IMPORTANTE - Generar SECRET_KEY segura:**

Abre una terminal y ejecuta:
```bash
# Windows PowerShell
python -c "import secrets; print(secrets.token_hex(32))"

# Linux/Mac
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y úsalo como valor de `SECRET_KEY`.

**📝 Ejemplo de configuración:**
```
OPENAI_API_KEY=sk-proj-ABC123...
SECRET_KEY=a1b2c3d4e5f6789...
API_URL=https://pollerialafamilia.com
FLASK_ENV=production
```

### Paso 4: Crear el Servicio

1. Revisa que toda la configuración esté correcta
2. Haz clic en **"Create Web Service"** (botón azul al final)

### Paso 5: Esperar el Deploy

1. Haz clic en **"Create Web Service"**
2. Render automáticamente:
   - Clonará tu repositorio
   - Instalará las dependencias
   - Iniciará el servicio con Gunicorn
3. Espera a que el deploy termine (verás logs en tiempo real)
4. Una vez completado, obtendrás una URL tipo: `https://polleria-ai-assistant.onrender.com`

### Paso 6: Obtener la URL de tu Servicio

Una vez que el deploy termine (verás "Live" en verde):

1. Copia la URL que aparece arriba (formato: `https://polleria-ai-assistant.onrender.com`)
2. Esta es la URL que usarás en tu página web

### Paso 7: Verificar que Funciona

Abre tu navegador y visita:
```
https://tu-app.onrender.com/test
```

Deberías ver: **"Hola, todo OK"**

También puedes probar el endpoint principal desde la terminal:

```bash
curl -X POST https://tu-app.onrender.com/ask \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hola","user_id":"test123","user_name":"Test"}'
```

---

## 🔗 Integración con tu Página Web

### Opción 1: Fetch API (JavaScript Vanilla)

```javascript
async function enviarMensaje(mensaje, userId, userName) {
  const response = await fetch('https://tu-app.onrender.com/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Importante para sesiones
    body: JSON.stringify({
      prompt: mensaje,
      user_id: userId,
      user_name: userName
    })
  });

  const data = await response.json();
  return data.response;
}

// Uso
const respuesta = await enviarMensaje(
  "Quiero ver las promociones",
  "user123",
  "Juan Pérez"
);
console.log(respuesta);
```

### Opción 2: Axios

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://tu-app.onrender.com',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
});

async function enviarMensaje(mensaje, userId, userName) {
  const { data } = await api.post('/ask', {
    prompt: mensaje,
    user_id: userId,
    user_name: userName
  });
  return data.response;
}
```

### Ejemplo de Componente Chat Completo

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Chat IA - Pollería La Familia</title>
  <style>
    #chat-container {
      max-width: 600px;
      margin: 0 auto;
      border: 1px solid #ccc;
      border-radius: 10px;
      overflow: hidden;
    }
    #messages {
      height: 400px;
      overflow-y: auto;
      padding: 20px;
      background: #f5f5f5;
    }
    .message {
      margin: 10px 0;
      padding: 10px;
      border-radius: 5px;
    }
    .user { background: #e3f2fd; text-align: right; }
    .bot { background: #fff; }
    #input-container {
      display: flex;
      padding: 10px;
      background: #fff;
    }
    #message-input {
      flex: 1;
      padding: 10px;
      border: 1px solid #ccc;
      border-radius: 5px;
    }
    #send-btn {
      margin-left: 10px;
      padding: 10px 20px;
      background: #de3210;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <div id="chat-container">
    <div id="messages"></div>
    <div id="input-container">
      <input type="text" id="message-input" placeholder="Escribe tu mensaje...">
      <button id="send-btn">Enviar</button>
    </div>
  </div>

  <script>
    const API_URL = 'https://tu-app.onrender.com';
    const userId = 'user_' + Math.random().toString(36).substr(2, 9);
    const userName = 'Cliente'; // Puedes obtenerlo del sistema de autenticación

    const messagesDiv = document.getElementById('messages');
    const input = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');

    function addMessage(text, isUser) {
      const div = document.createElement('div');
      div.className = `message ${isUser ? 'user' : 'bot'}`;
      div.innerHTML = text;
      messagesDiv.appendChild(div);
      messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    async function enviarMensaje() {
      const mensaje = input.value.trim();
      if (!mensaje) return;

      addMessage(mensaje, true);
      input.value = '';

      try {
        const response = await fetch(`${API_URL}/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({
            prompt: mensaje,
            user_id: userId,
            user_name: userName
          })
        });

        const data = await response.json();
        addMessage(data.response, false);
      } catch (error) {
        addMessage('Error al conectar con el servidor', false);
        console.error(error);
      }
    }

    sendBtn.addEventListener('click', enviarMensaje);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') enviarMensaje();
    });
  </script>
</body>
</html>
```

---

## 📡 Endpoints Disponibles

### POST `/ask`
Endpoint principal para conversación con la IA.

**Request Body:**
```json
{
  "prompt": "Quiero hacer un pedido",
  "user_id": "encrypted_user_id",
  "user_name": "Juan Pérez"
}
```

**Response:**
```json
{
  "response": "¡Claro! Por favor, indica los productos que deseas ordenar..."
}
```

### GET `/reset_session`
Reinicia la sesión de conversación del usuario.

**Response:**
```json
{
  "message": "Sesión reiniciada con éxito."
}
```

### GET `/test`
Health check del servicio.

**Response:**
```
Hola, todo OK
```

---

## 🛠️ Desarrollo Local

### 1. Clonar el Repositorio

```bash
git clone https://github.com/atuctov-stack/POLLERIALAFAMILIA.git
cd POLLERIALAFAMILIA
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `config.py` copiando el ejemplo:

```bash
# Windows
copy config.example.py config.py

# Linux/Mac
cp config.example.py config.py
```

Luego edita `config.py` y agrega tus valores reales:

```python
# config.py
OPENAI_API_KEY = "sk-proj-TU_API_KEY_REAL_AQUI"
API_URL = "http://127.0.0.1:8000"  # Para desarrollo local
```

**⚠️ NUNCA subas `config.py` a Git** - Ya está en `.gitignore`

### 5. Configurar para Desarrollo Local

En `app.py`, descomenta el bloque de configuración local:

```python
####################### local ##########################
CORS(app, supports_credentials=True)
app.config["SECRET_KEY"] = "una_clave_secreta_muy_segura"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
Session(app)
```

Y comenta el bloque de producción.

### 6. Ejecutar

```bash
python app.py
```

El servidor estará disponible en `http://127.0.0.1:5000`

---

## 🔧 Mantenimiento en Render

### Ver Logs en Tiempo Real

1. Ve a tu Web Service en el dashboard de Render
2. Haz clic en la pestaña **"Logs"** (menú izquierdo)
3. Verás todos los logs del servidor en tiempo real
4. Útil para debugging y monitoreo

### Redesplegar Manualmente

**Deploy Automático**: Render hace deploy automático cada vez que haces `git push` a la rama `main`.

**Deploy Manual**:
1. Ve a tu Web Service en Render
2. En la parte superior derecha, haz clic en **"Manual Deploy"**
3. Selecciona **"Deploy latest commit"**
4. Espera a que termine (verás "Live" cuando esté listo)

### Actualizar Variables de Entorno

1. Ve a tu Web Service en Render
2. Haz clic en **"Environment"** en el menú izquierdo
3. Modifica o agrega variables
4. Haz clic en **"Save Changes"**
5. Render reiniciará automáticamente el servicio (tarda ~2-3 minutos)

### Monitorear Uso del Servicio

En el dashboard de tu Web Service verás:
- **Status**: Si está "Live", "Building", o "Suspended"
- **Uptime**: Tiempo activo del servicio
- **Requests**: Número de requests recientes
- **Disk**: Uso del disco (importante para sesiones filesystem)

---

## ⚠️ Consideraciones del Plan Free

### ✅ Ventajas del Plan Free

- 💰 **100% Gratis** - Sin costo mensual
- 🔒 **HTTPS Automático** - SSL/TLS incluido
- 🔄 **Deploy Automático** - Con git push
- 📊 **Logs en Tiempo Real** - Para debugging
- 🌐 **URL Personalizada** - Tu propio subdominio

### ⚠️ Limitaciones del Plan Free

1. **Sleep Automático**:
   - El servicio duerme después de **15 minutos de inactividad**
   - La primera request después del sleep tarda **30-50 segundos** en responder
   - Requests subsecuentes son normales (~2 segundos)

2. **Recursos Limitados**:
   - **512 MB RAM** - Suficiente para Flask + OpenAI
   - **Disk**: Limitado para sesiones filesystem
   - **CPU**: Compartido con otros servicios

3. **Sin Redis**:
   - Usamos sesiones filesystem en su lugar
   - Las sesiones se pierden si el servicio se reinicia
   - No afecta la funcionalidad, solo la persistencia entre reinicios

### 💡 Soluciones para el Sleep

**Opción 1: Ping Automático (Gratis)**

Usa un servicio como [UptimeRobot](https://uptimerobot.com) (gratis):
1. Crea una cuenta
2. Agrega un monitor HTTP
3. URL: `https://tu-app.onrender.com/test`
4. Intervalo: Cada 5 minutos
5. Tu app nunca dormirá 🎉

**Opción 2: Cron Job en Render (Gratis)**

1. En Render, crea un **"Cron Job"**
2. Command: `curl https://tu-app.onrender.com/test`
3. Schedule: `*/5 * * * *` (cada 5 minutos)

**Opción 3: Upgrade a Starter ($7/mes)**
- Sin sleep automático
- 512 MB RAM garantizados
- Mejor para producción seria

### 💰 Costos Estimados

**Plan Free (Recomendado para empezar):**
- Render Web Service: **$0/mes**
- OpenAI API: **~$5-20/mes** (según uso)
- **Total: $5-20/mes** ✅

**Plan Starter (Para producción):**
- Render Web Service: **$7/mes**
- OpenAI API: **~$10-30/mes**
- **Total: $17-37/mes**

### 🔒 Seguridad (Importantes para Free Plan)

- ✅ **HTTPS Incluido** - Render lo hace automático
- ✅ **Variables de Entorno** - Nunca subas API keys al repo
- ✅ **CORS Configurado** - Solo dominios permitidos
- ✅ **SECRET_KEY Aleatoria** - Genera una única
- ⚠️ **Sesiones Filesystem** - Se borran al reiniciar el servicio

---

## 📚 Estructura del Proyecto

```
polleria-la-familia-python/
├── app.py                 # Aplicación Flask principal
├── config.py              # Configuraciones (API keys, URLs)
├── helpers.py             # Funciones OpenAI y clasificación
├── keywords.py            # Keywords para clasificación de intenciones
├── request.py             # Cliente API para backend Laravel
├── response.py            # Generación de respuestas HTML
├── utilities.py           # Utilidades de parsing y formato
├── requirements.txt       # Dependencias Python
└── README.md             # Este archivo
```

---

## 🐛 Solución de Problemas

### 🔴 Build Failed en Render

**Síntoma**: El deploy falla con "Build failed"

**Solución**:
```bash
# 1. Verifica que requirements.txt tenga todas las dependencias
# 2. Verifica que no haya typos en los nombres de paquetes
# 3. Mira los logs de Render para ver el error exacto
```

**Dependencias correctas** (requirements.txt):
```
Flask
Flask-Session
Flask-CORS
openai
requests
gunicorn
redis>=3.5.3
```

### 🟡 El Servicio Está "Building" por Mucho Tiempo

**Síntoma**: El deploy tarda más de 5 minutos

**Soluciones**:
1. Cancela el deploy actual (botón rojo "Cancel Deploy")
2. Ve a "Manual Deploy" → "Clear build cache & deploy"
3. Si persiste, verifica que tu repo no tenga archivos muy grandes

### 🟠 Error: "CORS policy" en la Página Web

**Síntoma**: En la consola del navegador ves: "Access to fetch has been blocked by CORS policy"

**Solución**:
1. Ve a tu archivo `app.py`
2. Verifica que los orígenes CORS incluyan tu dominio:

```python
CORS(app, supports_credentials=True,
     origins=["https://www.pollerialafamilia.com",
              "https://pollerialafamilia.com"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["X-Session-Id"])
```

3. Si estás probando en localhost, agrega temporalmente:
```python
origins=["http://localhost:3000", "https://tudominio.com"]
```

### 🔵 El Servicio Responde Muy Lento (Primera Request)

**Síntoma**: La primera llamada tarda 30-50 segundos

**Causa**: Plan Free - El servicio estaba dormido

**Soluciones**:
1. **Opción 1**: Usa UptimeRobot para mantenerlo despierto (gratis)
2. **Opción 2**: Advierte a los usuarios: "Primera carga puede tardar un momento"
3. **Opción 3**: Upgrade a plan Starter ($7/mes)

### 🟢 Error: "Application failed to respond"

**Síntoma**: El endpoint no responde o timeout

**Soluciones**:
1. Verifica los logs en Render
2. Asegúrate que el comando de inicio sea: `gunicorn app:app`
3. Verifica que el puerto sea el correcto (Render usa $PORT automáticamente)

### 🟣 Las Sesiones No Persisten

**Síntoma**: El bot no recuerda la conversación anterior

**Causa Normal en Free Plan**:
- Con filesystem, las sesiones se borran cuando el servicio reinicia
- Render puede reiniciar servicios Free cada 24-48 horas

**No es un error, es una limitación del plan Free**. Si necesitas persistencia:
- Considera almacenar estado en tu backend Laravel
- O upgrade a plan con Redis

### 🟤 Error al Confirmar Pedidos

**Síntoma**: "Hubo un problema al registrar tu pedido"

**Soluciones**:
1. Verifica que `API_URL` en variables de entorno sea correcta
2. Prueba tu API Laravel manualmente:
```bash
curl https://pollerialafamilia.com/api/get-products
```
3. Verifica los logs de Render para ver el error exacto
4. Asegúrate que tu API Laravel acepte requests desde Render

### 🔑 Error: OpenAI API Key Invalid

**Síntoma**: "Incorrect API key provided"

**Soluciones**:
1. Ve a [OpenAI Platform](https://platform.openai.com/api-keys)
2. Verifica que tu API key sea válida
3. Asegúrate de copiar la key completa (empieza con `sk-proj-`)
4. Actualiza la variable `OPENAI_API_KEY` en Render
5. Guarda cambios y espera el redeploy automático

---

## 👥 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es privado y pertenece a Pollería La Familia.

---

## 📞 Soporte

Para preguntas o soporte, contacta al equipo de desarrollo.

**Desarrollado con ❤️ para Pollería La Familia**
