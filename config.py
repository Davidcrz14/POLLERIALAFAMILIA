import os

# Configuraciones de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "polleria")

# URL de la API Backend
API_URL = os.getenv("API_URL", "https://pollerialafamilia.com")

# Configuración de OpenAI
# En producción (Render), esta clave debe estar en las variables de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")
