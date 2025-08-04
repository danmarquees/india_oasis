"""
Central constants for the India Oasis Store application.
This file contains all constants used across the application to ensure consistency.
"""

# Product and Catalog Constants
PRODUCTS_PER_PAGE = 12
MAX_PRODUCTS_PER_CATEGORY = 1000
DEFAULT_PRODUCT_IMAGE = 'products/default.jpg'

# Cart and Shopping Constants
MAX_CART_QUANTITY = 99
MIN_CART_QUANTITY = 1
MAX_CART_ITEMS = 50
CART_SESSION_TIMEOUT = 3600  # 1 hour in seconds

# Order Constants
ORDER_TIMEOUT_MINUTES = 30
MAX_ORDER_ITEMS = 50
ORDER_NUMBER_PREFIX = 'IO'

# Cache Timeouts (in seconds)
CACHE_TIMEOUT = 60 * 15  # 15 minutes
SHORT_CACHE_TIMEOUT = 60 * 5  # 5 minutes
LONG_CACHE_TIMEOUT = 60 * 60  # 1 hour
BANNER_CACHE_TIMEOUT = 60 * 30  # 30 minutes

# Pagination Constants
DEFAULT_PAGE_SIZE = 12
MAX_PAGE_SIZE = 48
REVIEWS_PER_PAGE = 10
ORDERS_PER_PAGE = 20

# Rating and Review Constants
MIN_RATING = 1
MAX_RATING = 5
MIN_REVIEW_LENGTH = 10
MAX_REVIEW_LENGTH = 1000

# Shipping Constants
DEFAULT_SHIPPING_WEIGHT = 0.5  # kg
MAX_SHIPPING_WEIGHT = 30.0  # kg
FREE_SHIPPING_THRESHOLD = 150.00  # R$

# Image and File Constants
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'WEBP']
THUMBNAIL_SIZE = (300, 300)
LARGE_IMAGE_SIZE = (800, 800)

# Contact and Communication
MAX_CONTACT_MESSAGE_LENGTH = 2000
CONTACT_SUBJECTS = [
    ('duvidas', 'Dúvidas sobre produtos'),
    ('pedido', 'Problemas com pedido'),
    ('entrega', 'Questões de entrega'),
    ('pagamento', 'Problemas de pagamento'),
    ('troca', 'Trocas e devoluções'),
    ('sugestao', 'Sugestões'),
    ('outro', 'Outros assuntos'),
]

# User and Authentication
MIN_PASSWORD_LENGTH = 8
SESSION_COOKIE_AGE = 3600  # 1 hour
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour

# SEO and URLs
MAX_SLUG_LENGTH = 100
MAX_META_DESCRIPTION_LENGTH = 160
MAX_TITLE_LENGTH = 60

# Banner and Marketing
MAX_BANNERS_PER_POSITION = 10
BANNER_POSITIONS = [
    ('home_carousel', 'Carrossel da Home'),
    ('home_sidebar', 'Sidebar da Home'),
    ('category_top', 'Topo da Categoria'),
    ('product_detail', 'Página do Produto'),
]

# Stock and Inventory
LOW_STOCK_THRESHOLD = 5
OUT_OF_STOCK_THRESHOLD = 0
STOCK_RESERVE_TIMEOUT = 900  # 15 minutes

# Search and Filtering
MAX_SEARCH_RESULTS = 100
SEARCH_MIN_LENGTH = 2
MAX_SEARCH_HISTORY = 10

# Email Configuration
EMAIL_TIMEOUT = 30  # seconds
MAX_EMAILS_PER_HOUR = 50

# File Upload Limits
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.pdf']

# API Rate Limiting
API_RATE_LIMIT = '100/hour'
WEBHOOK_RATE_LIMIT = '1000/hour'

# Monitoring and Logging
LOG_RETENTION_DAYS = 30
MAX_LOG_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Business Rules
MIN_ORDER_VALUE = 10.00  # R$
MAX_ORDER_VALUE = 5000.00  # R$
TAX_RATE = 0.0  # No tax for now
SHIPPING_TAX_RATE = 0.0

# Currency and Localization
DEFAULT_CURRENCY = 'BRL'
CURRENCY_SYMBOL = 'R$'
DECIMAL_PLACES = 2

# Social Media and External Links
SOCIAL_LINKS = {
    'facebook': 'https://facebook.com/indiaoasis',
    'instagram': 'https://instagram.com/indiaoasis',
    'whatsapp': 'https://wa.me/5511999999999',
}

# Error Messages
ERROR_MESSAGES = {
    'invalid_quantity': 'Quantidade inválida. Deve estar entre {min} e {max}.',
    'out_of_stock': 'Produto fora de estoque.',
    'cart_limit_exceeded': 'Limite máximo de itens no carrinho excedido.',
    'invalid_product': 'Produto não encontrado ou indisponível.',
    'login_required': 'Você precisa estar logado para realizar esta ação.',
    'permission_denied': 'Você não tem permissão para realizar esta ação.',
    'invalid_email': 'Email inválido.',
    'weak_password': 'Senha muito fraca. Use pelo menos 8 caracteres.',
}

# Success Messages
SUCCESS_MESSAGES = {
    'product_added_cart': 'Produto adicionado ao carrinho com sucesso!',
    'product_removed_cart': 'Produto removido do carrinho.',
    'wishlist_added': 'Produto adicionado à lista de desejos.',
    'wishlist_removed': 'Produto removido da lista de desejos.',
    'review_submitted': 'Avaliação enviada com sucesso!',
    'order_placed': 'Pedido realizado com sucesso!',
    'profile_updated': 'Perfil atualizado com sucesso!',
    'contact_sent': 'Mensagem enviada com sucesso!',
}

# Status Choices
ORDER_STATUS_CHOICES = [
    ('pending', 'Pendente'),
    ('processing', 'Processando'),
    ('shipped', 'Enviado'),
    ('delivered', 'Entregue'),
    ('cancelled', 'Cancelado'),
    ('refunded', 'Reembolsado'),
]

PAYMENT_STATUS_CHOICES = [
    ('pending', 'Pendente'),
    ('approved', 'Aprovado'),
    ('rejected', 'Rejeitado'),
    ('cancelled', 'Cancelado'),
    ('refunded', 'Reembolsado'),
]

# Development and Testing
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    'SHOW_COLLAPSED': True,
}

# Performance Settings
DATABASE_QUERY_TIMEOUT = 30  # seconds
REQUEST_TIMEOUT = 300  # 5 minutes
CELERY_TASK_TIMEOUT = 600  # 10 minutes
