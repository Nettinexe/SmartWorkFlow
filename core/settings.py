import os
from pathlib import Path

# Caminho base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURANÇA: Mantenha a chave secreta em segurança!
SECRET_KEY = 'django-insecure-&c@pw#kqu%c_bw&4_wc@v)zzuiewx-bp4l(^)^ngpksy82dx1$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# ==============================================================================
# 1. APLICATIVOS INSTALADOS
# ==============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Seu App Pedagógico
    'academic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ==============================================================================
# 2. CONFIGURAÇÃO DE TEMPLATES
# ==============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Busca a pasta templates na raiz
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug', # Adicionado
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ==============================================================================
# 3. BANCO DE DADOS
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ==============================================================================
# 4. MODELO DE USUÁRIO PERSONALIZADO (CRIAR/EDITAR PROFESSORES)
# ==============================================================================
# Essencial para as views de salvamento de professor funcionarem
AUTH_USER_MODEL = 'academic.CustomUser'

# ==============================================================================
# 5. VALIDAÇÃO DE SENHAS (Opcional em desenvolvimento)
# ==============================================================================
AUTH_PASSWORD_VALIDATORS = []

# ==============================================================================
# 6. INTERNACIONALIZAÇÃO (BRASIL)
# ==============================================================================
# Ajustado para que datas e mensagens do Django apareçam em Português
LANGUAGE_CODE = 'pt-br' # Corrigido de 'en-us'
TIME_ZONE = 'America/Sao_Paulo' # Corrigido de 'UTC' para horário de Brasília
USE_I18N = True
USE_TZ = True

# ==============================================================================
# 7. ARQUIVOS ESTÁTICOS
# ==============================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# 8. CONFIGURAÇÕES DE LOGIN E ACESSO
# ==============================================================================
# Define para onde o usuário vai ao tentar acessar algo restrito ou logar
LOGIN_URL = '/accounts/login/' # Rota padrão do Django ou sua rota customizada
LOGIN_REDIRECT_URL = 'dashboard' # Redireciona para sua View dashboard após logar
LOGOUT_REDIRECT_URL = '/accounts/login/'