from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist
from django.conf import settings
import uuid
from django.templatetags.static import static
from django.views.decorators.http import require_POST

def home(request):
    products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    return render(request, 'store/index.html', {
        'products': products,
        'categories': categories,
        'STATIC_URL': settings.STATIC_URL,
    })

def about(request):
    return render(request, 'store/about.html', {
        'STATIC_URL': settings.STATIC_URL,
    })

def contact(request):
    if request.method == 'POST':
        # Processo para enviar e-mail ou salvar contato
        messages.success(request, 'Sua mensagem foi enviada com sucesso!')
        return redirect('store:contact')
    return render(request, 'store/contact.html', {
        'STATIC_URL': settings.STATIC_URL,
    })

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'store/products.html', {
        'category': category,
        'categories': categories,
        'products': products,
        'STATIC_URL': settings.STATIC_URL,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    return render(request, 'store/product-detail.html', {
        'product': product,
        'related_products': related_products,
        'STATIC_URL': settings.STATIC_URL,
    })

def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id

        cart, created = Cart.objects.get_or_create(session_id=session_id)

    return cart

def cart(request):
    cart = get_cart(request)
    return render(request, 'store/cart.html', {
        'cart': cart,
        'STATIC_URL': settings.STATIC_URL,
    })

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product)

    # Check if it's an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_price,
            'cart_count': cart.total_items,
            'product_name': product.name,
            'message': f'{product.name} foi adicionado ao carrinho'
        })
    return redirect('store:cart')

def cart_remove(request, product_id):
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    product_name = product.name

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            removed_completely = False
        else:
            cart_item.delete()
            removed_completely = True
    except CartItem.DoesNotExist:
        pass
        removed_completely = False

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_price,
            'cart_count': cart.total_items,
            'product_name': product_name,
            'removed_completely': removed_completely,
            'message': f'{product_name} foi removido do carrinho' if removed_completely else f'Quantidade de {product_name} foi atualizada'
        })
    return redirect('store:cart')

@login_required
def checkout(request):
    cart = get_cart(request)

    if request.method == 'POST':
        # Processo de finalização do pedido
        order = Order.objects.create(
            user=request.user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            postal_code=request.POST.get('postal_code'),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            total_price=cart.total_price
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )

        # Limpar o carrinho
        cart.items.all().delete()

        return redirect('store:order_success')

    return render(request, 'store/checkout.html', {
        'cart': cart,
        'STATIC_URL': settings.STATIC_URL,
    })

def order_success(request):
    return render(request, 'store/order-success.html', {
        'STATIC_URL': settings.STATIC_URL,
    })

@login_required
def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {
        'wishlist': wishlist,
        'STATIC_URL': settings.STATIC_URL,
    })

@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    # Check if product is already in wishlist
    was_in_wishlist = product in wishlist.products.all()

    if not was_in_wishlist:
        wishlist.products.add(product)
        message = f'{product.name} foi adicionado aos favoritos'
    else:
        message = f'{product.name} já está nos favoritos'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'in_wishlist': True,
            'product_name': product.name,
            'message': message
        })
    return redirect('store:wishlist')

@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'in_wishlist': False,
            'product_name': product.name,
            'message': f'{product.name} foi removido dos favoritos'
        })
    return redirect('store:wishlist')

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/profile.html', {
        'orders': orders,
        'STATIC_URL': settings.STATIC_URL,
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('store:home')
    else:
        form = UserCreationForm()

    return render(request, 'store/signup.html', {
        'form': form,
        'STATIC_URL': settings.STATIC_URL,
    })

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('store:home')
    else:
        form = AuthenticationForm()

    return render(request, 'store/signup.html', {
        'form': form,
        'is_login': True,
        'STATIC_URL': settings.STATIC_URL,
    })

def user_logout(request):
    logout(request)
    messages.success(request, 'Você saiu com sucesso!')
    return redirect('store:home')

def terms(request):
    return render(request, 'store/terms.html', {
        'STATIC_URL': settings.STATIC_URL,
    })

def privacy(request):
    return render(request, 'store/privacy.html', {
        'STATIC_URL': settings.STATIC_URL,
    })
