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
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import mercadopago
import json
from decimal import Decimal # Import Decimal
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, CustomerProfile, Review, ContactMessage
from django.conf import settings
import uuid
from .forms import CustomUserCreationForm, ReviewForm
from django.views.decorators.http import require_POST


# ... (home, about, contact, etc. não mudam) ...
def home(request):
    products = Product.objects.filter(available=True).annotate(
        average_rating=models.Avg('reviews__rating'),
        review_count=models.Count('reviews')
    )[:8]
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


@require_POST
@csrf_exempt
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
    # This is a placeholder for Correios shipping calculation.
    # In a real application, you would integrate with the Correios API
    # using libraries like 'python-correios' or by making direct HTTP requests.
    # This example uses a simplified logic and does not call the actual API.

    # Placeholder for shipping parameters (replace with actual data from your products)
    # For simplicity, we'll assume a default weight and dimensions.
    product_weight_grams = 500  # Example weight in grams
    product_dimensions_cm = {'length': 20, 'width': 15, 'height': 10} # Example dimensions

    # Default shipping parameters from Correios' default services
    # You'd typically fetch these or have them configured.
    # These are illustrative values for PAC and SEDEX.
    # Refer to Correios' API documentation for accurate service codes and pricing.
    correios_services = {
        'PAC': {'code': '41106', 'base_price': Decimal('30.00'), 'free_threshold': Decimal('200.00')},
        'SEDEX': {'code': '40010', 'base_price': Decimal('50.00'), 'free_threshold': Decimal('200.00')},
    }

    if total_cart_price >= correios_services['PAC']['free_threshold']:
        return Decimal('0.00') # Frete grátis

    # This is a highly simplified simulation. A real implementation would:
    # 1. Calculate total weight and dimensions of all items in the cart.
    # 2. Package these into a format accepted by the Correios API.
    # 3. Make an HTTP request to the Correios API.
    # 4. Parse the API response to get the shipping cost for requested services (e.g., PAC, SEDEX).

    # For this example, we'll just return the base price for PAC if not free shipping.
    # The 'cep' parameter is present for future integration but not used in this placeholder.
    return correios_services['PAC']['base_price']

@login_required
def checkout(request):
    cart = get_cart(request)
    if cart.items.count() == 0:
        messages.info(request, "Seu carrinho está vazio.")
        return redirect("store:home")

    customer_profile = None
    if request.user.is_authenticated:
        try:
            customer_profile = CustomerProfile.objects.get(user=request.user)
        except CustomerProfile.DoesNotExist:
            customer_profile = None

    shipping_cost = calculate_shipping_cost(cart.total_price, customer_profile.cep if customer_profile else None)
    total_with_shipping = cart.total_price + shipping_cost

    context = {
        'cart': cart,
        'STATIC_URL': settings.STATIC_URL,
        'customer_profile': customer_profile,
        'shipping_cost': shipping_cost,
        'total_with_shipping': total_with_shipping,
        'MERCADO_PAGO_PUBLIC_KEY': settings.MERCADO_PAGO_PUBLIC_KEY,
    }
    return render(request, 'store/checkout.html', context)


@login_required
def process_payment(request):
    if request.method == 'POST':
        cart = get_cart(request)
        if not cart.items.exists():
            return JsonResponse({'error': 'Adicione itens ao carrinho antes de finalizar a compra.'}, status=400)

        user_profile = request.user.profile

        shipping_cost = calculate_shipping_cost(cart.total_price)
        total_with_shipping = cart.total_price + shipping_cost

        # Create Order first
        try:
            order = Order.objects.create(
                user=request.user,
                first_name=request.user.first_name,
                last_name=request.user.last_name,
                email=request.user.email,
                address=f"{user_profile.endereco}, {user_profile.numero}",
                postal_code=user_profile.cep,
                city=user_profile.cidade,
                state=user_profile.estado,
                total_price=total_with_shipping
            )
        except AttributeError:
             return JsonResponse({'error': 'Perfil incompleto. Por favor, preencha seu endereço.'}, status=400)

        for item in cart.items.all():
            OrderItem.objects.create(order=order, product=item.product, price=item.product.price, quantity=item.quantity)

        # Now create payment preference
        sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

        items = []
        for item in order.items.all():
            items.append({
                "title": item.product.name,
                "quantity": item.quantity,
                "unit_price": float(item.price),
                "currency_id": "BRL",
            })

        if shipping_cost > 0:
            items.append({
                "title": "Frete",
                "quantity": 1,
                "unit_price": float(shipping_cost),
                "currency_id": "BRL",
            })

        back_urls = {
            "success": request.build_absolute_uri(reverse('store:payment_success')),
            "failure": request.build_absolute_uri(reverse('store:payment_failure')),
            "pending": request.build_absolute_uri(reverse('store:payment_pending'))
        }

        preference_data = {
            "items": items,
            "payer": {
                "email": request.user.email,
            },
            "back_urls": back_urls,
            "auto_return": "approved",
            "notification_url": request.build_absolute_uri(reverse('store:mp_webhook')),
            "external_reference": str(order.id) # MP requires external_reference to be a string
        }

        try:
            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]
            request.session['cart_id'] = None # Clear cart
            return JsonResponse({'redirect_url': preference['init_point']})
        except Exception as e:
            order.delete() # Rollback
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def mp_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get("type") == "payment":
            payment_id = data["data"]["id"]
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)["response"]

            if payment_info and payment_info.get("status") == "approved":
                order_id = payment_info.get("external_reference")
                try:
                    order = Order.objects.get(id=order_id)
                    if order.user:
                        try:
                            cart = Cart.objects.get(user=order.user)
                            cart.items.all().delete()
                        except Cart.DoesNotExist:
                            pass

                    print(f"Payment for order {order_id} approved.")

                except Order.DoesNotExist:
                    print(f"Webhook error: Order with id {order_id} not found.")
    return HttpResponse(status=200)

def payment_success(request):
    cart = get_cart(request)
    if cart.items.count() > 0:
        cart.items.all().delete()
    messages.success(request, "Seu pagamento foi aprovado! Obrigado pela sua compra.")
    return redirect('store:order_success')

def payment_failure(request):
    messages.error(request, "Ocorreu uma falha no pagamento. Por favor, tente novamente.")
    return redirect('store:checkout')

def payment_pending(request):
    cart = get_cart(request)
    if cart.items.count() > 0:
        cart.items.all().delete()
    messages.info(request, "Seu pagamento está pendente. Você será notificado por e-mail quando for aprovado.")
    return redirect('store:profile')

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


@csrf_exempt
def mp_webhook(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if data.get("type") == "payment":
            payment_id = data["data"]["id"]
            sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
            payment_info = sdk.payment().get(payment_id)["response"]

            if payment_info and payment_info.get("status") == "approved":
                order_id = payment_info.get("external_reference")
                try:
                    order = Order.objects.get(id=order_id)
                    # Opcional: Adicione um campo 'paid' ao seu modelo Order
                    # e descomente as linhas abaixo para marcar o pedido como pago.
                    order.paid = True
                    order.save()

                    # Limpa o carrinho do usuário após o pagamento ser confirmado.
                    if order.user:
                        try:
                            cart = Cart.objects.get(user=order.user)
                            cart.items.all().delete()
                        except Cart.DoesNotExist:
                            pass # O carrinho pode já ter sido limpo ou não existir.

                    print(f"Pagamento para o pedido {order_id} foi aprovado via webhook.")

                except Order.DoesNotExist:
                    print(f"ERRO no Webhook: Pedido com id {order_id} não foi encontrado.")

    return HttpResponse(status=200)


def payment_success(request):
    cart = get_cart(request)
    if cart.items.count() > 0:
        cart.items.all().delete()
    messages.success(request, "Seu pagamento foi aprovado! Obrigado pela sua compra.")
    return redirect('store:order_success')


def payment_failure(request):
    messages.error(request, "Ocorreu uma falha no pagamento. Por favor, tente novamente.")
    return redirect('store:checkout')


def payment_pending(request):
    cart = get_cart(request)
    if cart.items.count() > 0:
        cart.items.all().delete()
    messages.info(request, "Seu pagamento está pendente. Você será notificado por e-mail quando for aprovado.")
    return redirect('store:profile')

def contact(request):
    if request.method == 'POST':
        # Import ContactForm and send_mail here, or ensure they are imported at the top of the file.
        # Assuming ContactForm is imported and send_mail is imported from django.core.mail
        from .forms import ContactForm
        from django.core.mail import send_mail

        form = ContactForm(request.POST)
        if form.is_valid():
            # Processar os dados do formulário
            name = form.cleaned_data['nome']
            email = form.cleaned_data['email']
            phone = form.cleaned_data.get('telefone') # Opcional
            subject = form.cleaned_data['assunto']
            message = form.cleaned_data['mensagem']
            newsletter_opt_in = form.cleaned_data['newsletter']

            # Salvar a mensagem no banco de dados
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                newsletter_opt_in=newsletter_opt_in
            )

            # --- Aqui você pode adicionar a lógica de envio de e-mail ---
            # Por exemplo, enviar um e-mail para o administrador do site
            try:
                subject_email_admin = f"Nova Mensagem de Contato: {subject} - {name}"
                message_email_admin = f"De: {name} <{email}>\n"
                if phone:
                    message_email_admin += f"Telefone: {phone}\n"
                message_email_admin += f"Assunto: {subject}\n"
                message_email_admin += f"Mensagem:\n{message}\n\n"
                if newsletter_opt_in:
                    message_email_admin += "O cliente optou por receber novidades.\n"
                else:
                    message_email_admin += "O cliente NÃO optou por receber novidades.\n"

                # Configurar o remetente (use um e-mail configurado no settings.py)
                # O 'DEFAULT_FROM_EMAIL' deve estar definido em settings.py
                send_mail(
                    subject_email_admin,
                    message_email_admin,
                    settings.DEFAULT_FROM_EMAIL, # Remetente
                    [settings.ADMIN_EMAIL],     # Destinatário (coloque o e-mail do admin em settings.py)
                    fail_silently=False,
                )
                # Você também pode querer enviar um e-mail de confirmação para o usuário
                # send_mail(...) aqui para o email do usuário.

            except Exception as e:
                print(f"Erro ao enviar e-mail: {e}") # Logar o erro para depuração


            # Redirecionar para uma página de sucesso ou mostrar uma mensagem
            # return redirect('store:contact_success') # Exemplo: criar uma URL de sucesso
            # Ou apenas renderizar a mesma página com uma mensagem de sucesso
            context = {
                'form': ContactForm(), # Limpa o formulário após o envio
                'success_message': 'Sua mensagem foi enviada com sucesso! Entraremos em contato em breve.'
            }
            return render(request, 'store/contact.html', context)

    else:
        # Se o método for GET, apenas renderiza o formulário
        # Import ContactForm here as well for the GET request
        from .forms import ContactForm
        form = ContactForm()

    context = {'form': form}
    return render(request, 'store/contact.html', context)
