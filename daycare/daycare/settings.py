import os
from pathlib import Path

from apps import accounts

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-7$&t6$ud9tx@!r5$s(m$1v+!+i_vyk)^d$1enlvj$h+oyj^dd-"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'mathfilters',


    # APPS
    'apps.accounts',
    'apps.common',
    'apps.meal_service',
    'apps.meals',
    'apps.notifications',
    'apps.reports',
    'apps.inventory',

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

ROOT_URLCONF = 'daycare.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(BASE_DIR / 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'daycare.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
from decouple import config
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config('POSTGRES_DB', default='daycare_db'),
        "USER": config('POSTGRES_USER', default='postgres'),
        "PASSWORD": config('POSTGRES_PASSWORD', default='salomdunyo'),
        "HOST": config('POSTGRES_HOST', default='db'),
        "PORT": config('POSTGRES_PORT', default='5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# from common______________________________
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.CustomUser'


# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Messages framework
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',  # Bootstrap uses 'danger' instead of 'error'
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'admin@daycare.com'


# Security settings for production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_REDIRECT_EXEMPT = []
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

# from common______________________________


# ___________REst framework___________________________
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# Email sozlamalari (signallar uchun)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'





#
#
# # JAZZMIN SETTINGS _____________________________________________________________________________
# # daycare/settings.py ichidagi JAZZMIN_SETTINGS ni yangilang
# JAZZMIN_SETTINGS = {
#     # Basic Info
#     "site_title": "Daycare Admin",
#     "site_header": "Daycare System",
#     "site_brand": "Daycare",
#     "site_logo": "admin/img/daycare.jpg",
#     "login_logo": "daycare.jpg",
#     "site_logo_classes": "img-circle",
#     "site_icon": "admin/img/favicon.ico",
#
#     # Welcome & Copyright
#     "welcome_sign": "Daycare Boshqaruv Tizimiga Xush Kelibsiz",
#     "copyright": "Daycare Management System 2025",
#
#     # Search Models
#     "search_model": [
#         "accounts.CustomUser",
#         "accounts.Role",
#         "inventory.Ingredient",
#         "inventory.IngredientCategory",
#         "auth.Group"
#     ],
#
#     ############
#     # Top Menu #
#     ############
#     "topmenu_links": [
#         {"name": "Asosiy Sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
#         {"name": "Sayt", "url": "/", "new_window": True},
#         {"name": "Dashboard", "url": "/common/dashboard/", "permissions": ["auth.view_user"]},
#         {"name": "Inventarizatsiya", "url": "/inventory/", "permissions": ["inventory.view_ingredient"]},
#         {"model": "accounts.CustomUser"},
#         {"app": "accounts"},
#     ],
#
#     #############
#     # User Menu #
#     #############
#     "usermenu_links": [
#         {"name": "Profil", "url": "/common/dashboard/", "new_window": False},
#         {"name": "Inventarizatsiya", "url": "/inventory/", "new_window": False},
#         {"name": "Yordam", "url": "mailto:support@daycare.com", "new_window": True},
#         {"model": "accounts.customuser"}
#     ],
#
#     #############
#     # Side Menu #
#     #############
#     "show_sidebar": True,
#     "navigation_expanded": True,
#     "hide_apps": [],
#     "hide_models": [],
#
#     # Menu ordering
#     "order_with_respect_to": [
#         "accounts",
#         "accounts.customuser",
#         "accounts.role",
#         "accounts.userprofile",
#         "inventory",
#         "inventory.ingredientcategory",
#         "inventory.ingredient",
#         "inventory.stock",
#         "inventory.stocktransaction",
#         "auth"
#     ],
#
#     # Custom links for apps
#     "custom_links": {
#         "accounts": [
#             {
#                 "name": "Foydalanuvchi Statistikasi",
#                 "url": "/admin/accounts/user-stats/",
#                 "icon": "fas fa-chart-bar",
#                 "permissions": ["accounts.view_customuser"]
#             },
#             {
#                 "name": "Email Yuborish",
#                 "url": "/admin/accounts/send-emails/",
#                 "icon": "fas fa-envelope",
#                 "permissions": ["accounts.change_customuser"]
#             }
#         ],
#         "inventory": [
#             {
#                 "name": "Zaxira ko'rinishi",
#                 "url": "/inventory/",
#                 "icon": "fas fa-tachometer-alt",
#                 "permissions": ["inventory.view_stock"]
#             },
#             {
#                 "name": "Kirim qilish",
#                 "url": "/inventory/stock/in/",
#                 "icon": "fas fa-arrow-down",
#                 "permissions": ["inventory.add_stocktransaction"]
#             },
#             {
#                 "name": "Chiqim qilish",
#                 "url": "/inventory/stock/out/",
#                 "icon": "fas fa-arrow-up",
#                 "permissions": ["inventory.add_stocktransaction"]
#             },
#             {
#                 "name": "Tartibga solish",
#                 "url": "/inventory/stock/adjustment/",
#                 "icon": "fas fa-balance-scale",
#                 "permissions": ["inventory.add_stocktransaction"]
#             },
#             {
#                 "name": "Tranzaksiyalar",
#                 "url": "/inventory/transactions/",
#                 "icon": "fas fa-history",
#                 "permissions": ["inventory.view_stocktransaction"]
#             },
#             {
#                 "name": "Zaxira hisoboti",
#                 "url": "/inventory/reports/stock/",
#                 "icon": "fas fa-file-alt",
#                 "permissions": ["inventory.view_stock"]
#             }
#         ]
#     },
#
#     # Custom icons for apps and models
#     "icons": {
#         "auth": "fas fa-users-cog",
#         "auth.user": "fas fa-user",
#         "auth.Group": "fas fa-users",
#
#         # Accounts app icons
#         "accounts": "fas fa-user-friends",
#         "accounts.CustomUser": "fas fa-user",
#         "accounts.Role": "fas fa-user-tag",
#         "accounts.UserProfile": "fas fa-id-card",
#
#         # Inventory app icons
#         "inventory": "fas fa-boxes",
#         "inventory.IngredientCategory": "fas fa-tags",
#         "inventory.Ingredient": "fas fa-carrot",
#         "inventory.Stock": "fas fa-cubes",
#         "inventory.StockTransaction": "fas fa-exchange-alt",
#
#         # Other apps
#         "common": "fas fa-cogs",
#         "meals": "fas fa-utensils",
#         "meal_service": "fas fa-concierge-bell",
#         "notifications": "fas fa-bell",
#         "reports": "fas fa-chart-line",
#         "children": "fas fa-baby",
#     },
#
#     "default_icon_parents": "fas fa-chevron-circle-right",
#     "default_icon_children": "fas fa-circle",
#
#     #################
#     # Related Modal #
#     #################
#     "related_modal_active": False,
#
#     #############
#     # UI Tweaks #
#     #############
#     "custom_css": "admin/css/custom.css",
#     "custom_js": "admin/js/custom.js",
#     "use_google_fonts_cdn": True,
#     "show_ui_builder": True,
#
#     ###############
#     # Change view #
#     ###############
#     "changeform_format": "horizontal_tabs",
#     "changeform_format_overrides": {
#         "accounts.customuser": "vertical_tabs",
#         "accounts.userprofile": "collapsible",
#         "inventory.ingredient": "horizontal_tabs",
#         "inventory.stocktransaction": "vertical_tabs",
#         "auth.user": "horizontal_tabs"
#     },
#
#     # Language chooser
#     "language_chooser": False,
# }


# JAZZMIN_SETTINGS = {
#     # Basic Info
#     "site_title": "Daycare Admin",
#     "site_header": "Daycare System",
#     "site_brand": "Daycare",
#     "site_logo": "admin/img/daycare.jpg",
#     "login_logo": "daycare.jpg",
#     "site_logo_classes": "img-circle",
#     "site_icon": "admin/img/favicon.ico",
#
#     # Welcome & Copyright
#     "welcome_sign": "Daycare Boshqaruv Tizimiga Xush Kelibsiz",
#     "copyright": "Daycare Management System 2025",
#
#     # Search Models
#     "search_model": [
#         "accounts.CustomUser",
#         "accounts.Role",
#         "auth.Group"
#     ],
#
#     # User Avatar ni o'chirib tashlang yoki to'g'ri field qo'ying
#     # "user_avatar": None,  # Yoki butunlay o'chiring
#
#     ############
#     # Top Menu #
#     ############
#     "topmenu_links": [
#         {"name": "Asosiy Sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
#         {"name": "Sayt", "url": "/", "new_window": True},
#         {"name": "Dashboard", "url": "/common/dashboard/", "permissions": ["auth.view_user"]},
#         {"model": "accounts.CustomUser"},
#         {"app": "accounts"},
#     ],
#
#     #############
#     # User Menu #
#     #############
#     "usermenu_links": [
#         {"name": "Profil", "url": "/common/dashboard/", "new_window": False},
#         {"name": "Yordam", "url": "mailto:support@daycare.com", "new_window": True},
#         {"model": "accounts.customuser"}
#     ],
#
#     #############
#     # Side Menu #
#     #############
#     "show_sidebar": True,
#     "navigation_expanded": True,
#     "hide_apps": [],
#     "hide_models": [],
#
#     # Menu ordering
#     "order_with_respect_to": [
#         "accounts",
#         "accounts.customuser",
#         "accounts.role",
#         "accounts.userprofile",
#         "auth"
#     ],
#
#     # Custom links for apps
#     "custom_links": {
#         "accounts": [
#             {
#                 "name": "Foydalanuvchi Statistikasi",
#                 "url": "/admin/accounts/user-stats/",
#                 "icon": "fas fa-chart-bar",
#                 "permissions": ["accounts.view_customuser"]
#             },
#             {
#                 "name": "Email Yuborish",
#                 "url": "/admin/accounts/send-emails/",
#                 "icon": "fas fa-envelope",
#                 "permissions": ["accounts.change_customuser"]
#             }
#         ]
#     },
#
#     # Custom icons for apps and models
#     "icons": {
#         "auth": "fas fa-users-cog",
#         "auth.user": "fas fa-user",
#         "auth.Group": "fas fa-users",
#
#         # Accounts app icons
#         "accounts": "fas fa-user-friends",
#         "accounts.CustomUser": "fas fa-user",
#         "accounts.Role": "fas fa-user-tag",
#         "accounts.UserProfile": "fas fa-id-card",
#
#         # Add icons for other apps
#         "common": "fas fa-cogs",
#         "inventory": "fas fa-boxes",
#         "meals": "fas fa-utensils",
#         "children": "fas fa-baby",
#     },
#
#     "default_icon_parents": "fas fa-chevron-circle-right",
#     "default_icon_children": "fas fa-circle",
#
#     #################
#     # Related Modal #
#     #################
#     "related_modal_active": False,
#
#     #############
#     # UI Tweaks #
#     #############
#     "custom_css": "admin/css/custom.css",
#     "custom_js": "admin/js/custom.js",
#     "use_google_fonts_cdn": True,
#     "show_ui_builder": True,
#
#     ###############
#     # Change view #
#     ###############
#     "changeform_format": "horizontal_tabs",
#     "changeform_format_overrides": {
#         "accounts.customuser": "vertical_tabs",
#         "accounts.userprofile": "collapsible",
#         "auth.user": "horizontal_tabs"
#     },
#
#     # Language chooser
#     "language_chooser": False,
# }