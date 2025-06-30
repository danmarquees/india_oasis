# store/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.db import IntegrityError, models # Import IntegrityError for handling duplicate reviews, and models for Avg
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from decimal import Decimal # Import Decimal
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, CustomerProfile, Review
from django.conf import settings
import uuid
from .forms import CustomUserCreationForm, ReviewForm # <<< IMPORTAÇÃO CORRETA

# ... (home, about, contact, etc. não mudam) ...
def home(request):
    products = Product.objects.filter(available=True)[:8]
    categories = Category.objects.all()
    return render(request, 'store/index.html', {'products': products,'categories': categories,'STATIC_URL': settings.STATIC_URL,})

def about(request):
    return render(request, 'store/about.html', {'STATIC_URL': settings.STATIC_URL,})

def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Sua mensagem foi enviada com sucesso!')
        return redirect('store:contact')
    return render(request, 'store/contact.html', {'STATIC_URL': settings.STATIC_URL,})

def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'store/products.html', {'category': category, 'categories': categories, 'products': products, 'STATIC_URL': settings.STATIC_URL,})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    reviews = product.reviews.all() # Get all reviews for this product
    user_has_reviewed = reviews.filter(user=request.user).exists() if request.user.is_authenticated else False
    form = ReviewForm() # Instantiate the review form

    # Calculate average rating
    average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    if average_rating is None:
        average_rating = 0

    return render(request, 'store/product-detail.html', {
        'product': product,
        'related_products': related_products,
        'reviews': reviews,
        'form': form,
        'user_has_reviewed': user_has_reviewed,
        'average_rating': average_rating,
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
    return render(request, 'store/cart.html', {'cart': cart, 'STATIC_URL': settings.STATIC_URL,})

def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    try:
        cart_item = CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product=product)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_total': cart.total_price, 'cart_count': cart.total_items, 'product_name': product.name, 'message': f'{product.name} foi adicionado ao carrinho'})
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
        return JsonResponse({'success': True, 'cart_total': cart.total_price, 'cart_count': cart.total_items, 'product_name': product_name, 'removed_completely': removed_completely, 'message': f'{product_name} foi removido do carrinho' if removed_completely else f'Quantidade de {product_name} foi atualizada'})
    return redirect('store:cart')

# Placeholder function for shipping calculation
def calculate_shipping_cost(total_cart_price, cep=None):
    # This is a simplified placeholder.
    # In a real application, you would integrate with a shipping API (e.g., Correios, FedEx, etc.)
    # and calculate based on weight, dimensions, destination (CEP), and service type.
    if total_cart_price > 200:
        return Decimal('0.00')  # Frete grátis para compras acima de R$200
    return Decimal('25.00') # Custo fixo de frete

@login_required
def checkout(request):
    cart = get_cart(request)
    customer_profile = None
    if request.user.is_authenticated:
        try:
            customer_profile = CustomerProfile.objects.get(user=request.user)
        except CustomerProfile.DoesNotExist:
            customer_profile = None

    shipping_cost = calculate_shipping_cost(cart.total_price, customer_profile.cep if customer_profile else None)
    total_with_shipping = cart.total_price + shipping_cost

    if request.method == 'POST':
        # Retrieve form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        address = request.POST.get('address')
        postal_code = request.POST.get('postal_code')
        city = request.POST.get('city')
        state = request.POST.get('state')

        # Create the order with updated total price including shipping
        order = Order.objects.create(
            user=request.user,
            first_name=first_name,
            last_name=last_name,
            email=email,
            address=address,
            postal_code=postal_code,
            city=city,
            state=state,
            total_price=total_with_shipping  # Use the total price with shipping
        )

        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)
        cart.items.all().delete()
        return JsonResponse({'success': True, 'redirect_url': reverse('store:order_success')})

    context = {
        'cart': cart,
        'STATIC_URL': settings.STATIC_URL,
        'customer_profile': customer_profile,
        'shipping_cost': shipping_cost,
        'total_with_shipping': total_with_shipping,
    }
    return render(request, 'store/checkout.html', context)

def order_success(request):
    return render(request, 'store/order-success.html', {'STATIC_URL': settings.STATIC_URL,})

@login_required
def wishlist(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist, 'STATIC_URL': settings.STATIC_URL,})

@login_required
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    was_in_wishlist = product in wishlist.products.all()
    if not was_in_wishlist:
        wishlist.products.add(product)
        message = f'{product.name} foi adicionado aos favoritos'
    else:
        message = f'{product.name} já está nos favoritos'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'in_wishlist': True, 'product_name': product.name, 'message': message})
    return redirect('store:wishlist')

@login_required
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    wishlist.products.remove(product)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'in_wishlist': False, 'product_name': product.name, 'message': f'{product.name} foi removido dos favoritos'})
    return redirect('store:wishlist')

@login_required
def profile(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'store/profile.html', {'orders': orders, 'STATIC_URL': settings.STATIC_URL,})

@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            try:
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                messages.success(request, 'Sua avaliação foi enviada com sucesso!')

                # Recalculate average rating for immediate update on frontend
                reviews = product.reviews.all()
                average_rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
                if average_rating is None:
                    average_rating = 0

                return JsonResponse({
                    'success': True,
                    'message': 'Avaliação enviada com sucesso!',
                    'rating': review.rating,
                    'comment': review.comment,
                    'username': request.user.username,
                    'created_at': review.created_at.strftime('%Y-%m-%d %H:%M'), # Format datetime for JSON
                    'average_rating': round(average_rating, 1), # Round for display
                    'total_reviews': reviews.count(),
                })
            except IntegrityError:
                messages.error(request, 'Você já avaliou este produto.')
                return JsonResponse({'success': False, 'message': 'Você já avaliou este produto.'}, status=400)
        else:
            errors = form.errors.as_json()
            messages.error(request, 'Por favor, corrija os erros no formulário.')
            return JsonResponse({'success': False, 'errors': errors}, status=400)
    return JsonResponse({'success': False, 'message': 'Método não permitido.'}, status=405)


# --- VIEW SIGNUP CORRIGIDA ---
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        # --- INÍCIO DO CÓDIGO DE DEBUG ---
        print("\n" + "="*50)
        print("----- DEBUGANDO A VIEW SIGNUP -----")
        print("Formulário que está sendo usado:", type(form))
        print("Dados recebidos (request.POST):", request.POST.keys())

        if form.is_valid():
            user = form.save()
            login(request, user)
            print("Formulário VÁLIDO. Usuário criado.")
            print("="*50 + "\n")
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('store:home')
            })
        else:
            # --- INÍCIO DO CÓDIGO DE DEBUG PARA ERROS ---
            print("Formulário INVÁLIDO.")
            print("Erros do formulário:", form.errors.as_json())
            print("="*50 + "\n")
            # --- FIM DO CÓDIGO DE DEBUG PARA ERROS ---
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    return render(request, 'store/signup.html')



# ... (user_login, user_logout, etc. não mudam)
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
    return render(request, 'store/signup.html', {'form': form, 'is_login': True, 'STATIC_URL': settings.STATIC_URL,})

def user_logout(request):
    logout(request)
    messages.success(request, 'Você saiu com sucesso!')
    return redirect('store:home')


def terms(request):
    return render(request, 'store/terms.html', {'STATIC_URL': settings.STATIC_URL,})

def privacy(request):
    return render(request, 'store/privacy.html', {'STATIC_URL': settings.STATIC_URL,})
