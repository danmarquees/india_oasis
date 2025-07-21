from .models import Cart, Category, Wishlist
from django.conf import settings
from .views import get_cart  # Importa o helper correto


def cart_processor(request):
    """
    Context processor para disponibilizar o contador do carrinho e wishlist em todos os templates.
    """
    cart_count = 0
    wishlist_count = 0

    # Sempre usa o helper para garantir consistência
    cart = get_cart(request)
    if cart:
        cart_count = cart.total_items

    if request.user.is_authenticated:
        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        wishlist_count = wishlist.products.count() if wishlist else 0

    return {
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }


def static_files_processor(request):
    """
    Context processor to make static URL available to all templates.
    """
    return {
        'STATIC_URL': settings.STATIC_URL,
    }

def categories_processor(request):
    """
    Context processor to make categories available to all templates.
    """
    categories = Category.objects.all()
    return {'categories': categories}
