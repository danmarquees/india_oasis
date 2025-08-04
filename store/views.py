from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import cache_page
from django.db.models import Q, Avg, Count, F
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.views.decorators.vary import vary_on_headers
from django.middleware.csrf import get_token
from decimal import Decimal
import json
import logging

# Services and utilities
from .services import calcular_frete_melhor_envio
from .constants import (
    PRODUCTS_PER_PAGE, MAX_CART_QUANTITY, MIN_CART_QUANTITY,
    CACHE_TIMEOUT, ERROR_MESSAGES, SUCCESS_MESSAGES
)
from .models import (
    Product, Category, Cart, CartItem, Order, OrderItem,
    Wishlist, Review, CustomerProfile, Banner
)
from .forms import (
    CustomUserCreationForm, ReviewForm, ContactForm,
    ProfileForm, LoginForm
)

# Configure logger
logger = logging.getLogger(__name__)




def get_cart(request):
    """
    Helper function to get or create cart for authenticated users or sessions.
    Optimized with caching and proper error handling.
    """
    try:
        if request.user.is_authenticated:
            # Get or create cart for authenticated user
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={'session_id': None}
            )

            # Merge session cart if exists
            session_cart_id = request.session.get('cart_id')
            if session_cart_id and created:
                try:
                    session_cart = Cart.objects.get(id=session_cart_id, user=None)
                    # Transfer items from session cart to user cart
                    for item in session_cart.items.select_related('product'):
                        existing_item, item_created = CartItem.objects.get_or_create(
                            cart=cart,
                            product=item.product,
                            defaults={'quantity': item.quantity}
                        )
                        if not item_created:
                            existing_item.quantity = min(
                                existing_item.quantity + item.quantity,
                                existing_item.product.stock if existing_item.product.track_stock else MAX_CART_QUANTITY
                            )
                            existing_item.save()

                    session_cart.delete()
                    del request.session['cart_id']
                except Cart.DoesNotExist:
                    pass

            return cart
        else:
            # Handle anonymous users with session-based cart
            cart_id = request.session.get('cart_id')
            if cart_id:
                try:
                    return Cart.objects.get(id=cart_id, user=None)
                except Cart.DoesNotExist:
                    pass

            # Create new cart for anonymous user
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
            return cart

    except Exception as e:
        logger.error(f"Error in get_cart: {str(e)}", exc_info=True)
        # Fallback: create new cart
        cart = Cart.objects.create()
        if not request.user.is_authenticated:
            request.session['cart_id'] = cart.id
        return cart


def restore_cart_from_session(request):
    """Restore cart items from session data (used after login)"""
    try:
        cart_items_data = request.session.pop('cart_backup', None)
        if cart_items_data and request.user.is_authenticated:
            cart = get_cart(request)
            for item_data in cart_items_data:
                try:
                    product = Product.objects.get(
                        id=item_data["product_id"],
                        available=True
                    )
                    if product.can_be_purchased(item_data["quantity"]):
                        cart_item, created = CartItem.objects.get_or_create(
                            cart=cart,
                            product=product,
                            defaults={'quantity': item_data["quantity"]}
                        )
                        if not created:
                            cart_item.quantity = min(
                                cart_item.quantity + item_data["quantity"],
                                product.stock if product.track_stock else MAX_CART_QUANTITY
                            )
                            cart_item.save()
                except (Product.DoesNotExist, KeyError, ValueError):
                    continue
    except Exception as e:
        logger.error(f"Error restoring cart from session: {str(e)}")


@cache_page(CACHE_TIMEOUT)
@vary_on_headers('User-Agent')
def home(request):
    """
    Home page with featured products and banners.
    Optimized with caching and prefetch.
    """
    try:
        # Get active banners for home carousel
        banners = Banner.objects.filter(
            ativo=True,
            posicao='home_carousel'
        ).order_by('ordem')[:5]  # Limit to 5 banners

        # Get featured products with optimized queries
        featured_products = Product.objects.select_related('category').filter(
            available=True,
            is_featured=True
        ).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).order_by('-created')[:8]

        # Get new products
        new_products = Product.objects.select_related('category').filter(
            available=True,
            is_new=True
        ).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).order_by('-created')[:4]

        # Get bestsellers
        bestsellers = Product.objects.select_related('category').filter(
            available=True,
            is_bestseller=True
        ).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).order_by('-view_count')[:4]

        # Increment banner view counts
        for banner in banners:
            banner.increment_views()

        context = {
            'banners': banners,
            'featured_products': featured_products,
            'new_products': new_products,
            'bestsellers': bestsellers,
        }

        return render(request, 'store/index.html', context)

    except Exception as e:
        logger.error(f"Error in home view: {str(e)}", exc_info=True)
        return render(request, 'store/index.html', {'error': True})


@cache_page(CACHE_TIMEOUT)
def about(request):
    """About page"""
    return render(request, 'store/about.html')


@cache_page(CACHE_TIMEOUT)
def terms(request):
    """Terms and conditions page"""
    return render(request, 'store/terms.html')


@cache_page(CACHE_TIMEOUT)
def privacy(request):
    """Privacy policy page"""
    return render(request, 'store/privacy.html')


def product_list(request, category_slug=None):
    """
    Product listing with filtering, sorting, and pagination.
    Optimized for performance.
    """
    try:
        # Base queryset with optimizations
        products = Product.objects.select_related('category').filter(
            available=True
        ).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )

        # Category filter
        category = None
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            products = products.filter(category=category)

        # Search filter
        query = request.GET.get('q', '').strip()
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query)
            )

        # Price range filter
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            try:
                products = products.filter(price__gte=Decimal(min_price))
            except (ValueError, TypeError):
                pass
        if max_price:
            try:
                products = products.filter(price__lte=Decimal(max_price))
            except (ValueError, TypeError):
                pass

        # Rating filter
        min_rating = request.GET.get('rating')
        if min_rating:
            try:
                min_rating = int(min_rating)
                if 1 <= min_rating <= 5:
                    products = products.filter(average_rating__gte=min_rating)
            except (ValueError, TypeError):
                pass

        # Sorting
        sort_option = request.GET.get('sort', 'name')
        sort_options = {
            'name': 'name',
            'price_asc': 'price',
            'price_desc': '-price',
            'newest': '-created',
            'rating': '-average_rating',
            'popular': '-view_count'
        }

        if sort_option in sort_options:
            products = products.order_by(sort_options[sort_option])
        else:
            products = products.order_by('name')

        # Pagination
        page = request.GET.get('page', 1)
        paginator = Paginator(products, PRODUCTS_PER_PAGE)

        try:
            products_page = paginator.page(page)
        except PageNotAnInteger:
            products_page = paginator.page(1)
        except EmptyPage:
            products_page = paginator.page(paginator.num_pages)

        # Get categories for sidebar
        categories = Category.objects.filter(
            is_active=True,
            parent=None
        ).annotate(
            product_count=Count('products', filter=Q(products__available=True))
        ).order_by('sort_order', 'name')

        context = {
            'products': products_page,
            'category': category,
            'categories': categories,
            'query': query,
            'sort_option': sort_option,
            'current_filters': {
                'min_price': min_price,
                'max_price': max_price,
                'rating': min_rating,
            },
            'paginator': paginator,
        }

        return render(request, 'store/products.html', context)

    except Exception as e:
        logger.error(f"Error in product_list view: {str(e)}", exc_info=True)
        return render(request, 'store/products.html', {'error': True})


def product_detail(request, slug):
    """
    Product detail page with reviews and related products.
    Optimized with prefetch and caching.
    """
    try:
        # Get product with optimized queries
        product = get_object_or_404(
            Product.objects.select_related('category').annotate(
                average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                review_count=Count('reviews', filter=Q(reviews__is_approved=True))
            ),
            slug=slug,
            available=True
        )

        # Increment view count
        Product.objects.filter(id=product.id).update(view_count=F('view_count') + 1)

        # Get approved reviews with user info
        reviews = Review.objects.select_related('user').filter(
            product=product,
            is_approved=True
        ).order_by('-created_at')[:20]  # Limit reviews for performance

        # Check if user already reviewed
        user_has_reviewed = False
        if request.user.is_authenticated:
            user_has_reviewed = Review.objects.filter(
                product=product,
                user=request.user
            ).exists()

        # Mark helpful reviews for authenticated users
        if request.user.is_authenticated and reviews:
            helpful_review_ids = set(
                request.user.helpful_reviews.filter(
                    id__in=[r.id for r in reviews]
                ).values_list('id', flat=True)
            )
            for review in reviews:
                review.user_marked_helpful = review.id in helpful_review_ids
        else:
            for review in reviews:
                review.user_marked_helpful = False

        # Get related products (same category)
        related_products = Product.objects.select_related('category').filter(
            category=product.category,
            available=True
        ).exclude(id=product.id).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        )[:4]

        # Calculate rating distribution
        rating_distribution = {}
        total_reviews = reviews.count() if reviews else 0

        if total_reviews > 0:
            for rating in range(1, 6):
                count = sum(1 for r in reviews if r.rating == rating)
                rating_distribution[rating] = {
                    'count': count,
                    'percentage': int((count / total_reviews) * 100) if total_reviews > 0 else 0
                }

        # Forms
        review_form = ReviewForm()

        # Check if product is in user's wishlist
        in_wishlist = False
        if request.user.is_authenticated:
            try:
                wishlist = request.user.wishlist
                in_wishlist = wishlist.has_product(product)
            except Wishlist.DoesNotExist:
                pass

        context = {
            'product': product,
            'reviews': reviews,
            'review_form': review_form,
            'user_has_reviewed': user_has_reviewed,
            'related_products': related_products,
            'rating_distribution': rating_distribution,
            'total_reviews': total_reviews,
            'in_wishlist': in_wishlist,
        }

        return render(request, 'store/product-detail.html', context)

    except Exception as e:
        logger.error(f"Error in product_detail view: {str(e)}", exc_info=True)
        raise Http404("Produto não encontrado")


@require_GET
def cart_detail(request):
    """Cart detail page with shipping calculation"""
    try:
        cart = get_cart(request)
        cart_items = cart.items.select_related('product').all()

        # Calculate shipping if items exist
        shipping_cost = Decimal('0.00')
        if cart_items:
            # Default shipping calculation
            total_weight = sum(item.total_weight for item in cart_items)
            if cart.total_price < Decimal('250.00'):
                shipping_cost = Decimal('25.00')

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'shipping_cost': shipping_cost,
            'total_with_shipping': cart.total_price + shipping_cost,
        }

        return render(request, 'store/cart.html', context)

    except Exception as e:
        logger.error(f"Error in cart_detail view: {str(e)}", exc_info=True)
        return render(request, 'store/cart.html', {'error': True})


@require_POST
@transaction.atomic
def cart_add(request, product_id):
    """Add product to cart with validation"""
    try:
        product = get_object_or_404(Product, id=product_id, available=True)
        cart = get_cart(request)

        # Get quantity from request
        quantity = int(request.POST.get('quantity', 1))

        # Validate quantity
        if quantity < MIN_CART_QUANTITY or quantity > MAX_CART_QUANTITY:
            raise ValidationError(ERROR_MESSAGES['invalid_quantity'].format(
                min=MIN_CART_QUANTITY, max=MAX_CART_QUANTITY
            ))

        # Check stock availability
        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        current_quantity = cart_item.quantity if cart_item else 0
        total_quantity = current_quantity + quantity

        if not product.can_be_purchased(total_quantity):
            message = f"Estoque insuficiente. Disponível: {product.stock}"
            success = False
        else:
            # Add or update cart item
            if cart_item:
                cart_item.quantity = total_quantity
                cart_item.save()
            else:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity
                )

            message = f"'{product.name}' adicionado ao carrinho"
            success = True

        # AJAX response
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'cart_count': cart.total_items,
                'cart_total': str(cart.total_price),
            })

        # Regular form submission
        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('store:product_detail', slug=product.slug)

    except (ValueError, Product.DoesNotExist, ValidationError) as e:
        error_message = str(e) if isinstance(e, ValidationError) else "Erro ao adicionar produto"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})

        messages.error(request, error_message)
        return redirect('store:home')

    except Exception as e:
        logger.error(f"Error in cart_add view: {str(e)}", exc_info=True)
        error_message = "Erro interno do servidor"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})

        messages.error(request, error_message)
        return redirect('store:home')


@require_POST
@transaction.atomic
def cart_remove(request, product_id):
    """Remove product from cart"""
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)

        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
        cart_item.delete()

        message = SUCCESS_MESSAGES['product_removed_cart']

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_count': cart.total_items,
                'cart_total': str(cart.total_price),
            })

        messages.success(request, message)
        return redirect('store:cart')

    except Exception as e:
        logger.error(f"Error in cart_remove view: {str(e)}", exc_info=True)
        error_message = "Erro ao remover produto"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})

        messages.error(request, error_message)
        return redirect('store:cart')


@login_required
def checkout(request):
    """Checkout page for authenticated users"""
    try:
        cart = get_cart(request)
        cart_items = cart.items.select_related('product').all()

        if not cart_items:
            messages.warning(request, "Seu carrinho está vazio")
            return redirect('store:cart')

        # Validate stock before checkout
        for item in cart_items:
            if not item.product.can_be_purchased(item.quantity):
                messages.error(
                    request,
                    f"Produto '{item.product.name}' não tem estoque suficiente"
                )
                return redirect('store:cart')

        # Get user profile for pre-filling form
        try:
            profile = request.user.profile
        except CustomerProfile.DoesNotExist:
            profile = None

        # Calculate shipping
        shipping_cost = Decimal('25.00')
        if cart.total_price >= Decimal('250.00'):
            shipping_cost = Decimal('0.00')

        total_with_shipping = cart.total_price + shipping_cost

        context = {
            'cart': cart,
            'cart_items': cart_items,
            'profile': profile,
            'shipping_cost': shipping_cost,
            'total_with_shipping': total_with_shipping,
            'csrf_token': get_token(request),
        }

        return render(request, 'store/checkout.html', context)

    except Exception as e:
        logger.error(f"Error in checkout view: {str(e)}", exc_info=True)
        messages.error(request, "Erro no checkout")
        return redirect('store:cart')


@login_required
@require_POST
@transaction.atomic
def create_order_and_redirect_to_payment(request):
    """Create order and redirect to payment"""
    try:
        cart = get_cart(request)
        cart_items = cart.items.select_related('product').all()

        if not cart_items:
            messages.error(request, "Carrinho vazio")
            return redirect('store:cart')

        # Validate all items stock
        for item in cart_items:
            if not item.product.can_be_purchased(item.quantity):
                messages.error(
                    request,
                    f"Produto '{item.product.name}' não tem estoque suficiente"
                )
                return redirect('store:cart')

        # Get form data
        form_data = {
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name': request.POST.get('last_name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'address': request.POST.get('address', '').strip(),
            'number': request.POST.get('number', '').strip(),
            'complement': request.POST.get('complement', '').strip(),
            'neighborhood': request.POST.get('neighborhood', '').strip(),
            'postal_code': request.POST.get('postal_code', '').strip(),
            'city': request.POST.get('city', '').strip(),
            'state': request.POST.get('state', '').strip(),
        }

        # Validate required fields
        required_fields = [
            'first_name', 'last_name', 'email', 'address',
            'number', 'neighborhood', 'postal_code', 'city', 'state'
        ]

        missing_fields = [field for field in required_fields if not form_data[field]]
        if missing_fields:
            messages.error(request, "Todos os campos obrigatórios devem ser preenchidos")
            return redirect('store:checkout')

        # Calculate totals
        shipping_cost = Decimal('25.00')
        if cart.total_price >= Decimal('250.00'):
            shipping_cost = Decimal('0.00')

        total_price = cart.total_price + shipping_cost

        # Create order
        order = Order.objects.create(
            user=request.user,
            first_name=form_data['first_name'],
            last_name=form_data['last_name'],
            email=form_data['email'],
            phone=form_data['phone'],
            address=form_data['address'],
            number=form_data['number'],
            complement=form_data['complement'],
            neighborhood=form_data['neighborhood'],
            postal_code=form_data['postal_code'],
            city=form_data['city'],
            state=form_data['state'],
            total_price=total_price,
            shipping_cost=shipping_cost,
        )

        # Create order items and reserve stock
        for item in cart_items:
            if not item.product.reserve_stock(item.quantity):
                # Rollback if can't reserve stock
                order.delete()
                messages.error(
                    request,
                    f"Erro ao reservar estoque para '{item.product.name}'"
                )
                return redirect('store:cart')

            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_sku=item.product.sku,
                price=item.product.final_price,
                quantity=item.quantity,
            )

        # Clear cart
        cart.clear()

        # Store order ID in session for payment
        request.session['order_id'] = order.id

        # Redirect to payment
        return redirect('payment_processing:create_payment')

    except Exception as e:
        logger.error(f"Error creating order: {str(e)}", exc_info=True)
        messages.error(request, "Erro ao criar pedido")
        return redirect('store:checkout')


@login_required
def profile(request):
    """User profile page with orders and profile management"""
    try:
        # Get or create user profile
        profile, created = CustomerProfile.objects.get_or_create(user=request.user)

        # Get user orders
        orders = Order.objects.filter(user=request.user).prefetch_related(
            'items__product'
        ).order_by('-created')[:10]

        # Handle profile form submission
        if request.method == 'POST':
            form = ProfileForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Perfil atualizado com sucesso")
                return redirect('store:profile')
            else:
                messages.error(request, "Erro ao atualizar perfil")
        else:
            form = ProfileForm(instance=profile)

        context = {
            'profile': profile,
            'orders': orders,
            'form': form,
        }

        return render(request, 'store/profile.html', context)

    except Exception as e:
        logger.error(f"Error in profile view: {str(e)}", exc_info=True)
        messages.error(request, "Erro ao carregar perfil")
        return redirect('store:home')


def signup(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    # Auto login after registration
                    login(request, user)

                    # Restore cart from session
                    restore_cart_from_session(request)

                    messages.success(request, "Conta criada com sucesso!")
                    return redirect('store:home')
            except Exception as e:
                logger.error(f"Error in signup: {str(e)}", exc_info=True)
                messages.error(request, "Erro ao criar conta")
        else:
            messages.error(request, "Erro no formulário de cadastro")
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


def user_login(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('store:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            try:
                user = form.get_user()
                login(request, user)

                # Restore cart from session
                restore_cart_from_session(request)

                messages.success(request, f"Bem-vindo, {user.first_name or user.username}!")

                # Redirect to next page or home
                next_page = request.GET.get('next', 'store:home')
                return redirect(next_page)
            except Exception as e:
                logger.error(f"Error in login: {str(e)}", exc_info=True)
                messages.error(request, "Erro no login")
        else:
            messages.error(request, "Credenciais inválidas")
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout"""
    logout(request)
    messages.success(request, "Logout realizado com sucesso")
    return redirect('store:home')


@login_required
@require_POST
@transaction.atomic
def add_review(request, product_id):
    """Add product review"""
    try:
        product = get_object_or_404(Product, id=product_id, available=True)

        # Check if user already reviewed this product
        if Review.objects.filter(user=request.user, product=product).exists():
            messages.error(request, "Você já avaliou este produto")
            return redirect('store:product_detail', slug=product.slug)

        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.product = product

            # Check if user bought this product (verified purchase)
            has_purchased = OrderItem.objects.filter(
                order__user=request.user,
                product=product,
                order__status__in=['payment_approved', 'processing', 'shipped', 'delivered']
            ).exists()

            review.is_verified_purchase = has_purchased
            review.save()

            messages.success(request, SUCCESS_MESSAGES['review_submitted'])
        else:
            messages.error(request, "Erro ao adicionar avaliação")

        return redirect('store:product_detail', slug=product.slug)

    except Exception as e:
        logger.error(f"Error adding review: {str(e)}", exc_info=True)
        messages.error(request, "Erro ao adicionar avaliação")
        return redirect('store:home')


@login_required
@require_POST
def mark_review_helpful(request, review_id):
    """Mark review as helpful"""
    try:
        review = get_object_or_404(Review, id=review_id, is_approved=True)

        if review.user == request.user:
            return JsonResponse({
                'success': False,
                'message': 'Você não pode marcar sua própria avaliação como útil'
            })

        # Toggle helpful mark
        if review.is_marked_helpful_by(request.user):
            review.unmark_helpful(request.user)
            is_helpful = False
            message = "Marcação removida"
        else:
            review.mark_helpful(request.user)
            is_helpful = True
            message = "Marcado como útil"

        return JsonResponse({
            'success': True,
            'message': message,
            'helpful_count': review.helpful_count,
            'is_helpful': is_helpful
        })

    except Exception as e:
        logger.error(f"Error marking review helpful: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Erro ao processar solicitação'
        })


def contact(request):
    """Contact form page"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                contact_message = form.save()

                # TODO: Send notification email to admin
                # send_contact_notification.delay(contact_message.id)

                messages.success(
                    request,
                    "Mensagem enviada com sucesso! Responderemos em breve."
                )
                return redirect('store:contact')
            except Exception as e:
                logger.error(f"Error saving contact message: {str(e)}", exc_info=True)
                messages.error(request, "Erro ao enviar mensagem")
        else:
            messages.error(request, "Por favor, corrija os erros no formulário")
    else:
        form = ContactForm()

    return render(request, 'store/contact.html', {'form': form})


@login_required
def wishlist(request):
    """User wishlist page"""
    try:
        wishlist_obj, created = Wishlist.objects.get_or_create(user=request.user)

        # Get wishlist products with annotations
        products = wishlist_obj.products.filter(available=True).annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True))
        ).select_related('category')

        context = {
            'wishlist': wishlist_obj,
            'products': products,
        }

        return render(request, 'store/wishlist.html', context)

    except Exception as e:
        logger.error(f"Error in wishlist view: {str(e)}", exc_info=True)
        messages.error(request, "Erro ao carregar lista de desejos")
        return redirect('store:home')


@login_required
@require_POST
def wishlist_add(request, product_id):
    """Add product to wishlist"""
    try:
        product = get_object_or_404(Product, id=product_id, available=True)
        wishlist_obj, created = Wishlist.objects.get_or_create(user=request.user)

        if not wishlist_obj.has_product(product):
            wishlist_obj.add_product(product)
            message = f"'{product.name}' adicionado à lista de desejos"
            success = True
        else:
            message = f"'{product.name}' já está na sua lista de desejos"
            success = True

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'in_wishlist': True
            })

        messages.success(request, message)
        return redirect(request.META.get('HTTP_REFERER', 'store:product_list'))

    except Exception as e:
        logger.error(f"Error adding to wishlist: {str(e)}", exc_info=True)
        error_message = "Erro ao adicionar à lista de desejos"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})

        messages.error(request, error_message)
        return redirect('store:home')


@login_required
@require_POST
def wishlist_remove(request, product_id):
    """Remove product from wishlist"""
    try:
        product = get_object_or_404(Product, id=product_id)

        try:
            wishlist_obj = request.user.wishlist
            wishlist_obj.remove_product(product)
            message = f"'{product.name}' removido da lista de desejos"
            success = True
        except Wishlist.DoesNotExist:
            message = "Lista de desejos não encontrada"
            success = False

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': success,
                'message': message,
                'in_wishlist': False
            })

        if success:
            messages.success(request, message)
        else:
            messages.error(request, message)

        return redirect('store:wishlist')

    except Exception as e:
        logger.error(f"Error removing from wishlist: {str(e)}", exc_info=True)
        error_message = "Erro ao remover da lista de desejos"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_message})

        messages.error(request, error_message)
        return redirect('store:wishlist')


@login_required
@require_POST
def toggle_wishlist(request):
    """Toggle product in wishlist (AJAX)"""
    try:
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({
                'success': False,
                'message': 'ID do produto não fornecido'
            })

        product = get_object_or_404(Product, id=product_id, available=True)
        wishlist_obj, created = Wishlist.objects.get_or_create(user=request.user)

        if wishlist_obj.has_product(product):
            wishlist_obj.remove_product(product)
            in_wishlist = False
            message = f"'{product.name}' removido da lista de desejos"
        else:
            wishlist_obj.add_product(product)
            in_wishlist = True
            message = f"'{product.name}' adicionado à lista de desejos"

        return JsonResponse({
            'success': True,
            'message': message,
            'in_wishlist': in_wishlist
        })

    except Exception as e:
        logger.error(f"Error toggling wishlist: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Erro ao processar solicitação'
        })


@require_POST
def calculate_shipping_ajax(request):
    """Calculate shipping cost via AJAX"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        cep_destino = data.get('cep', '').strip()

        if not cep_destino:
            return JsonResponse({
                'success': False,
                'message': 'CEP de destino é obrigatório'
            })

        cart = get_cart(request)
        cart_items = cart.items.select_related('product').all()

        if not cart_items:
            return JsonResponse({
                'success': False,
                'message': 'Carrinho vazio'
            })

        # Calculate cart dimensions and weight
        total_weight = sum(item.total_weight for item in cart_items)
        total_length = sum(item.product.comprimento * item.quantity for item in cart_items)
        max_height = max(item.product.altura for item in cart_items)
        max_width = max(item.product.largura for item in cart_items)

        # Use shipping service
        cep_origem = getattr(settings, 'MELHOR_ENVIO_CEP_ORIGEM', '01034-001')

        resultado = calcular_frete_melhor_envio(
            cep_origem=cep_origem,
            cep_destino=cep_destino,
            peso_kg=total_weight,
            valor_produtos=float(cart.total_price),
            altura_cm=float(max_height),
            largura_cm=float(max_width),
            comprimento_cm=float(total_length),
            servicos=["1", "2"]  # PAC, SEDEX
        )

        if isinstance(resultado, list) and resultado:
            return JsonResponse({
                'success': True,
                'options': resultado
            })
        else:
            error_msg = resultado.get('erro', 'Erro ao calcular frete') if isinstance(resultado, dict) else 'Serviço indisponível'
            return JsonResponse({
                'success': False,
                'message': error_msg
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dados inválidos'
        })
    except Exception as e:
        logger.error(f"Error calculating shipping: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Erro no servidor'
        })


@require_GET
def cart_count(request):
    """Get cart count (AJAX)"""
    try:
        cart = get_cart(request)
        return JsonResponse({
            'cart_count': cart.total_items,
            'cart_total': str(cart.total_price)
        })
    except Exception as e:
        logger.error(f"Error getting cart count: {str(e)}", exc_info=True)
        return JsonResponse({
            'cart_count': 0,
            'cart_total': '0.00'
        })
