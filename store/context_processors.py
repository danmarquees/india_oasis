from .models import Cart, Category, Wishlist
from django.conf import settings

def cart_processor(request):
    """
    Context processor to make cart and wishlist counts available to all templates.
    """
    cart_count = 0
    wishlist_count = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_count = cart.total_items if cart else 0

        wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
        wishlist_count = wishlist.products.count() if wishlist else 0
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, user=None)
                cart_count = cart.total_items
            except Cart.DoesNotExist:
                cart_count = 0

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
