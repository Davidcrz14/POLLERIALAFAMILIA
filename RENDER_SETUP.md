# 🚀 Configuración en Render

## Variables de Entorno Requeridas

Para que la aplicación funcione correctamente en Render, debes configurar las siguientes variables de entorno:

### 1. Ir a tu servicio en Render
- Accede a [Render Dashboard](https://dashboard.render.com/)
- Selecciona tu servicio: `pollerialafamilia`
- Ve a la pestaña **Environment**

### 2. Agregar Variables de Entorno

Configura las siguientes variables:

```bash
# OpenAI API Key (REQUERIDO)
OPENAI_API_KEY=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

# Base de datos (si usas MySQL remoto)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=polleria

# API URL de Laravel
API_URL=https://pollerialafamilia.com
```

### 3. Guardar y Re-deployar

Después de agregar las variables:
1. Haz clic en **Save Changes**
2. Render automáticamente re-deploiará tu aplicación
3. Espera 2-3 minutos para que el servicio esté activo

### 4. Verificar que funciona

Visita estos endpoints para confirmar:
- ✅ Health Check: https://pollerialafamilia.onrender.com/test
- ✅ API Info: https://pollerialafamilia.onrender.com/

## 📝 Configuración CORS

El archivo `app.py` está configurado para aceptar peticiones desde:
- `https://pollerialafamilia.com`
- `https://www.pollerialafamilia.com`
- `http://pollerialafamilia.com`
- `http://www.pollerialafamilia.com`

Si necesitas agregar más dominios, edita la línea de `origins` en `app.py`.

## 🔒 Seguridad

**IMPORTANTE:**
- Nunca subas `config.py` al repositorio
- Mantén tu `OPENAI_API_KEY` en secreto
- Usa variables de entorno en producción

## 🐛 Troubleshooting

### Error 500 en /ask
1. Verifica que `OPENAI_API_KEY` esté configurada en Render
2. Revisa los logs en Render Dashboard → Logs
3. Confirma que la API de Laravel esté respondiendo

### Error CORS
1. Verifica que tu dominio esté en la lista de `origins` en `app.py`
2. Confirma que las cookies estén habilitadas

### Sesiones no persisten
- Render usa sistema de archivos efímero
- Considera usar Redis para sesiones persistentes en producción
