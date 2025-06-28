from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist
#from .forms import OrderCreateForm  # Importando o novo formulário
import uuid
from django.views.decorators.http import require_POST

# NOTA: Com o 'context_processor', não é mais necessário passar 'STATIC_URL' em cada view.

def home(request):
    products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    return render(request, 'store/index.html', {
        'products': products,
        'categories': categories,
    })

def about(request):
    return render(request, 'store/about.html')

def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Sua mensagem foi enviada com sucesso!')
        return redirect('store:contact')
    return render(request, 'store/contact.html')

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
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    return render(request, 'store/product-detail.html', {
        'product': product,
        'related_products': related_products,
    })

def cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.get('session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['session_id'] = session_id
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    return cart

def cart_detail(request):
    cart = get_cart(request)
    return render(request, 'store/cart.html', {'cart': cart})

@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_price,
            'cart_count': cart.total_items,
            'message': f'{product.name} foi adicionado ao carrinho'
        })
    return redirect('store:cart')

@require_POST
def cart_remove(request, product_id):
    cart = get_cart(request)
    product = get_object_or_404(Product, id=product_id)
    removed_completely = False

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            message = f'Quantidade de {product.name} foi atualizada'
        else:
            cart_item.delete()
            removed_completely = True
            message = f'{product.name} foi removido do carrinho'
    except CartItem.DoesNotExist:
        message = 'Item não encontrado no carrinho.'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_total': cart.total_price,
            'cart_count': cart.total_items,
            'removed_completely': removed_completely,
            'message': message
        })
    return redirect('store:cart')

@login_required
def checkout(request):
    cart = get_cart(request)
    if cart.items.count() == 0:
        messages.warning(request, 'Seu carrinho está vazio.')
        return redirect('store:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_price = cart.total_price
            order.save()

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
            # Limpar o carrinho
            cart.items.all().delete()
            # Armazenar o ID do pedido na sessão para a página de sucesso
            request.session['order_id'] = order.id
            return redirect('store:order_success')
    else:
        form = OrderCreateForm()

    return render(request, 'store/checkout.html', {'cart': cart, 'form': form})

def order_success(request):
    order_id = request.session.get('order_id')
    if order_id:
        # Limpar o ID da sessão para não mostrar novamente
        del request.session['order_id']
    return render(request, 'store/order-success.html', {'order_id': order_id})

@login_required
def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist})

@login_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)

    # CORREÇÃO: Usar .exists() é muito mais eficiente
    if not wishlist.products.filter(id=product.id).exists():
        wishlist.products.add(product)
        message = f'{product.name} foi adicionado aos favoritos.'
    else:
        message = f'{product.name} já está nos favoritos.'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': message})
    return redirect('store:wishlist')

@login_required
@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    message = f'{product.name} foi removido dos favoritos.'

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': message})
    return redirect('store:wishlist')

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/profile.html', {'orders': orders})

from .forms import CustomUserCreationForm, CustomerProfileForm

def signup(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        profile_form = CustomerProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            return redirect('store:home')
    else:
        user_form = CustomUserCreationForm()
        profile_form = CustomerProfileForm()

    return render(request, 'store/signup.html', {
        'form': user_form,
        'profile_form': profile_form,
        'STATIC_URL': settings.STATIC_URL,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirecionar para a próxima página ou para a home
            next_url = request.GET.get('next', 'store:home')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    # É melhor ter um template separado para login (ex: 'store/login.html')
    return render(request, 'store/login.html', {'form': form})

@require_POST
def user_logout(request):
    logout(request)
    messages.success(request, 'Você saiu com sucesso!')
    return redirect('store:home')

def terms(request):
    return render(request, 'store/terms.html')

def privacy(request):
    return render(request, 'store/privacy.html')
