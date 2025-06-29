from .models import Cart, Category
from django.conf import settings

def cart_processor(request):
    """
    Context processor to make cart data available to all templates.
    """
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('session_id')
        if session_id:
            try:
                cart = Cart.objects.get(session_id=session_id)
            except Cart.DoesNotExist:
                cart = None
        else:
            cart = None

    return {'cart': cart}

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
