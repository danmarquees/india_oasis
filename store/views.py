from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
import json
# Note: You need to have the 'mercadopago' library installed
import mercadopago

# Models
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Wishlist, Review, ContactMessage, CustomerProfile

# Forms
from .forms import CustomUserCreationForm, ReviewForm, ContactForm, LoginForm
from django.contrib.auth.forms import AuthenticationForm


# Basic Views
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

# Product Views
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    # Search logic
    query = request.GET.get('q')
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))

    # Sorting logic
    sort_option = request.GET.get('sort')
    allowed_sort_options = ['name', 'price', '-price', '-created_at']
    if sort_option in allowed_sort_options:
        products = products.order_by(sort_option)
    else:
        products = products.order_by('name')  # Default sort by name

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

# Cart Views
def get_cart(request):
    """Helper function to get cart for user or session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        session_cart_id = request.session.get('cart_id')
        if session_cart_id:
            try:
                old_cart = Cart.objects.get(id=session_cart_id, user=None)
                for item in old_cart.items.all():
                    # Transfer items to user's cart
                    existing_item, item_created = CartItem.objects.get_or_create(cart=cart, product=item.product)
                    if not item_created:
                        existing_item.quantity += item.quantity
                    existing_item.save()
                old_cart.delete()
                del request.session['cart_id']
            except Cart.DoesNotExist:
                pass
        return cart
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                return Cart.objects.get(id=cart_id)
            except Cart.DoesNotExist:
                pass  # Fall through to create a new one
        cart = Cart.objects.create(user=None)
        request.session['cart_id'] = cart.id
        return cart

def cart(request):
    cart_instance = get_cart(request)
    return render(request, 'store/cart.html', {'cart': cart_instance})

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    # Check stock before adding
    if cart_item.quantity < product.stock:
        if not created:
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
            'cart_count': cart.total_items,
        })

    # Fallback for non-AJAX requests
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)

    return redirect('store:product_list')

def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_instance = get_cart(request)
    try:
        cart_item = CartItem.objects.get(cart=cart_instance, product=product)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except CartItem.DoesNotExist:
        pass
    return redirect('store:cart')


# Checkout and Payment Views
def calculate_shipping_cost(total_cart_price):
    """Placeholder for shipping calculation."""
    # Free shipping above a certain threshold
    if total_cart_price >= Decimal('250.00'):
        return Decimal('0.00')
    # Fixed shipping cost otherwise
    return Decimal('25.00')

@login_required
def checkout(request):
    cart = get_cart(request)
    if cart.items.count() == 0:
        messages.info(request, "Seu carrinho está vazio. Adicione produtos para continuar.")
        return redirect("store:product_list")

    customer_profile = get_object_or_404(CustomerProfile, user=request.user)

    # Recalculate totals on server side
    shipping_cost = calculate_shipping_cost(cart.total_price)
    total_with_shipping = cart.total_price + shipping_cost

    context = {
        'cart': cart,
        'customer_profile': customer_profile,
        'shipping_cost': shipping_cost,
        'total_with_shipping': total_with_shipping,
        'MERCADO_PAGO_PUBLIC_KEY': settings.MERCADO_PAGO_PUBLIC_KEY,
    }
    return render(request, 'store/checkout.html', context)

@login_required
def process_payment(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método de requisição inválido'}, status=405)

    cart = get_cart(request)
    if not cart.items.exists():
        return JsonResponse({'error': 'Seu carrinho está vazio.'}, status=400)

    # Stock validation
    for item in cart.items.all():
        if item.quantity > item.product.stock:
            return JsonResponse({
                'error': f'Estoque insuficiente para o produto: {item.product.name}. Disponível: {item.product.stock}'
            }, status=400)

    # Recalculate totals on the server to ensure data integrity
    shipping_cost = calculate_shipping_cost(cart.total_price)
    total_price = cart.total_price + shipping_cost

    user_profile = get_object_or_404(CustomerProfile, user=request.user)

    # Create the Order object
    order = Order.objects.create(
        user=request.user,
        first_name=request.user.first_name,
        last_name=request.user.last_name,
        email=request.user.email,
        address=f"{user_profile.endereco}, {user_profile.numero}",
        postal_code=user_profile.cep,
        city=user_profile.cidade,
        state=user_profile.estado,
        total_price=total_price
    )

    # Create OrderItems and decrease stock
    for item in cart.items.all():
        OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
        item.product.stock -= item.quantity
        item.product.save()

    # Mercado Pago SDK initialization
    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

    # Create payment preference items
    preference_items = []
    for item in order.items.all():
        preference_items.append({
            "title": item.product.name,
            "quantity": item.quantity,
            "unit_price": float(item.price),
            "currency_id": "BRL",
        })

    if shipping_cost > 0:
        preference_items.append({
            "title": "Frete",
            "quantity": 1,
            "unit_price": float(shipping_cost),
            "currency_id": "BRL",
        })

    # Set up back URLs for redirection
    back_urls = {
        "success": request.build_absolute_uri(reverse('store:payment_success')),
        "failure": request.build_absolute_uri(reverse('store:payment_failure')),
        "pending": request.build_absolute_uri(reverse('store:payment_pending'))
    }

    preference_data = {
        "items": preference_items,
        "payer": {
            "email": request.user.email,
        },
        "back_urls": back_urls,
        "auto_return": "approved",
        "notification_url": request.build_absolute_uri(reverse('store:mp_webhook')),
        "external_reference": str(order.id)
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        # Clear the cart and save order_id to session
        cart.items.all().delete()
        request.session['order_id'] = order.id

        return JsonResponse({'redirect_url': preference['init_point']})
    except Exception as e:
        # If payment preference fails, roll back the order creation
        order.delete()
        # Note: Stock was already decreased. A more robust solution would use transactions.
        return JsonResponse({'error': str(e)}, status=500)

def order_success(request):
    return render(request, 'store/order-success.html')

def payment_success(request):
    order_id = request.session.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        order.paid = True
        order.save()
        del request.session['order_id']
        return render(request, 'store/payment-success.html', {'order': order})
    return redirect('store:home')

def payment_failure(request):
    return render(request, 'store/payment-failure.html')

def payment_pending(request):
    order_id = request.session.get('order_id')
    if order_id:
        order = get_object_or_404(Order, id=order_id)
        return render(request, 'store/payment-pending.html', {'order': order})
    return redirect('store:home')


@csrf_exempt
def mp_webhook(request):
    if request.method == 'POST':
        # Logic to handle Mercado Pago notifications
        pass
    return HttpResponse(status=200)

# Wishlist Views
@login_required
def wishlist(request):
    wishlist_instance, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist_instance})

@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_instance, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist_instance.products.add(product)
    return redirect('store:wishlist')

@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        wishlist_instance = Wishlist.objects.get(user=request.user)
        wishlist_instance.products.remove(product)
    except Wishlist.DoesNotExist:
        pass
    return redirect('store:wishlist')

# User Account Views
@login_required
def profile(request):
    # Pass user's orders and profile to the template
    orders = Order.objects.filter(user=request.user)
    customer_profile = get_object_or_404(CustomerProfile, user=request.user)
    return render(request, 'store/profile.html', {'orders': orders, 'profile': customer_profile})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            if not Review.objects.filter(product=product, user=request.user).exists():
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
    return redirect('store:product_detail', slug=product.slug)

def signup(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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

def user_logout(request):
    logout(request)
    return redirect('store:home')

# Contact Form View
def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            ContactMessage.objects.create(
                name=form.cleaned_data['nome'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['telefone'],
                subject=form.cleaned_data['assunto'],
                message=form.cleaned_data['mensagem'],
                newsletter_opt_in=form.cleaned_data['newsletter']
            )
            # You can add a success message using Django's messages framework
            return redirect('store:contact')
    else:
        form = ContactForm()
    return render(request, 'store/contact.html', {'form': form})
