from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
from decimal import Decimal
import json
import mercadopago

# Models
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Wishlist, Review, ContactMessage, CustomerProfile

def restore_cart_from_session(request):
    cart_items_data = request.session.pop('cart_backup', None)
    if cart_items_data:
        cart = get_cart(request)
        for item_data in cart_items_data:
            product = Product.objects.filter(id=item_data["product_id"]).first()
            if product:
                cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
                cart_item.quantity = item_data["quantity"]
                cart_item.save()

# Forms
from .forms import CustomUserCreationForm, ReviewForm, ContactForm, LoginForm, ProfileForm

# --- Helper Functions ---

def get_cart(request):
    """Helper function to get cart for a logged-in user or a session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Check for a session cart and merge it if it exists
        session_cart_id = request.session.get('cart_id')
        if session_cart_id:
            try:
                old_cart = Cart.objects.get(id=session_cart_id, user=None)
                for item in old_cart.items.all():
                    # Transfer items to the user's permanent cart
                    existing_item, item_created = CartItem.objects.get_or_create(cart=cart, product=item.product, defaults={'quantity': 0})
                    existing_item.quantity += item.quantity
                    existing_item.save()
                old_cart.delete()
                del request.session['cart_id']
            except Cart.DoesNotExist:
                pass # No session cart to merge
        return cart
    else:
        # Handle anonymous users
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                return Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                pass # Invalid session cart_id, create a new one
        cart = Cart.objects.create() # user=None
        request.session['cart_id'] = cart.id
        return cart

def calculate_shipping_cost(total_cart_price):
    """Placeholder for shipping calculation logic."""
    if total_cart_price >= Decimal('250.00'):
        return Decimal('0.00')
    return Decimal('25.00')


# --- Core Store Views ---

def home(request):
    products = Product.objects.filter(available=True).annotate(
        average_rating=Avg('reviews__rating'),
        review_count=Count('reviews')
    ).order_by('-created')[:8]
    return render(request, 'store/index.html', {'products': products})

def about(request):
    return render(request, 'store/about.html')

def terms(request):
    return render(request, 'store/terms.html')

def privacy(request):
    return render(request, 'store/privacy.html')

# --- Product Views ---

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    sort_option = request.GET.get('sort')
    if sort_option in ['name', 'price', '-price', '-created']:
        products = products.order_by(sort_option)
    else:
        products = products.order_by('name')

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    return render(request, 'store/products.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    reviews = product.reviews.all()
    review_form = ReviewForm()
    return render(request, 'store/product-detail.html', {
        'product': product,
        'reviews': reviews,
        'review_form': review_form
    })


# --- Cart Views ---

def cart_detail(request):
    cart_instance = get_cart(request)
    return render(request, 'store/cart.html', {'cart': cart_instance})

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_instance = get_cart(request)
    # Use defaults to prevent race conditions
    cart_item, created = CartItem.objects.get_or_create(cart=cart_instance, product=product, defaults={'quantity': 0})

    if cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()
        message = f"'{product.name}' foi adicionado ao carrinho."
        success = True
    else:
        message = f"Desculpe, não há mais estoque disponível para '{product.name}'."
        success = False

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': success,
            'message': message,
            'cart_count': cart_instance.total_items,
        })

    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    return redirect('store:product_list')

def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_instance = get_cart(request)
    removed_completely = False
    try:
        cart_item = CartItem.objects.get(cart=cart_instance, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            removed_completely = True
    except CartItem.DoesNotExist:
        pass

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'cart_total': cart_instance.total_price,
            'cart_count': cart_instance.total_items,
            'removed_completely': removed_completely,
        })
    return redirect('store:cart_detail')


# --- Checkout and Payment Views ---

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("store:product_list")

    # This view now only displays the checkout page.
    # The actual order creation and payment initiation happens in a separate view.
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)
    shipping_cost = calculate_shipping_cost(cart.total_price)
    total_with_shipping = cart.total_price + shipping_cost

    context = {
        'cart': cart,
        'customer_profile': customer_profile,
        'shipping_cost': shipping_cost,
        'total_with_shipping': total_with_shipping,
    }
    return render(request, 'store/checkout.html', context)

@login_required
@transaction.atomic # Ensures that stock updates and order creation are all-or-nothing
def create_order_and_redirect_to_payment(request):
    if request.method != 'POST':
        return redirect('store:checkout')

    cart = get_cart(request)
    if not cart.items.exists():
        messages.error(request, "Seu carrinho está vazio.")
        return redirect('store:product_list')

    # 1. Validate stock before creating the order
    for item in cart.items.all():
        if item.quantity > item.product.stock:
            messages.error(request, f'Estoque insuficiente para {item.product.name}. Disponível: {item.product.stock}')
            return redirect('store:cart_detail')

    # 2. Create the Order
    shipping_cost = calculate_shipping_cost(cart.total_price)
    total_price = cart.total_price + shipping_cost
    user_profile = get_object_or_404(CustomerProfile, user=request.user)

    order = Order.objects.create(
        user=request.user,
        first_name=request.user.first_name or user_profile.nome.split(' ')[0],
        last_name=request.user.last_name or ' '.join(user_profile.nome.split(' ')[1:]),
        email=request.user.email,
        address=f"{user_profile.endereco}, {user_profile.numero}",
        postal_code=user_profile.cep,
        city=user_profile.cidade,
        state=user_profile.estado,
        total_price=total_price,
        status='awaiting_payment', # New status
        paid=False
    )

    # 3. Create OrderItems and decrease stock
    for item in cart.items.all():
        OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
        # Decrease stock
        product = item.product
        product.stock -= item.quantity
        product.save()

    # 4. Salva o carrinho na sessão antes de limpar
    cart_items_data = []
    for item in cart.items.all():
        cart_items_data.append({
            "product_id": item.product.id,
            "quantity": item.quantity,
        })
    request.session['cart_backup'] = cart_items_data

    # Agora limpa o carrinho
    cart.items.all().delete()

    # 5. Store order_id in session to be used by payment views
    request.session['order_id'] = order.id

    # 6. Redirect to the payment processing page
    # This page will handle the interaction with Mercado Pago's SDK
    return redirect('payment_processing:create_payment')


# --- User Account Views ---

@login_required
def profile(request):
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created')

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=customer_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seu perfil foi atualizado com sucesso!')
            return redirect('store:profile')
    else:
        form = ProfileForm(instance=customer_profile)

    context = {
        'form': form,
        'orders': orders,
        'profile': customer_profile
    }
    return render(request, 'store/profile.html', context)

def signup(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a customer profile automatically
            CustomerProfile.objects.create(user=user, nome=user.get_full_name())
            login(request, user)
            messages.success(request, "Cadastro realizado com sucesso!")
            return redirect('store:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'store/signup.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('store:profile')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next')
            return redirect(next_url or 'store:home')
    else:
        form = LoginForm()
    return render(request, 'store/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect('store:home')


# --- Other Views ---

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if Review.objects.filter(product=product, user=request.user).exists():
                messages.error(request, "Você já avaliou este produto.")
            else:
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, "Obrigado pela sua avaliação!")
    return redirect('store:product_detail', slug=product.slug)

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Sua mensagem foi enviada. Entraremos em contato em breve.")
            return redirect('store:contact')
    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})

@login_required
def wishlist(request):
    wishlist_instance, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist_instance})

@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_instance, created = Wishlist.objects.get_or_create(user=request.user)
    if product not in wishlist_instance.products.all():
        wishlist_instance.products.add(product)
        messages.success(request, f"'{product.name}' foi adicionado à sua lista de desejos.")
    else:
        messages.info(request, f"'{product.name}' já está na sua lista de desejos.")
    return redirect(request.META.get('HTTP_REFERER', 'store:product_list'))

@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        wishlist_instance = Wishlist.objects.get(user=request.user)
        wishlist_instance.products.remove(product)
        messages.success(request, f"'{product.name}' foi removido da sua lista de desejos.")
    except Wishlist.DoesNotExist:
        pass
    return redirect('store:wishlist')
