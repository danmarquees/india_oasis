import mercadopago
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from store.models import Order

# Initialize Mercado Pago SDK with your Access Token
sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

def create_payment(request):
    """
    Cria uma preferência de pagamento no Mercado Pago e redireciona automaticamente o usuário para o checkout.
    """
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('store:cart')

    order = get_object_or_404(Order, id=order_id)
    if order.paid:
        return redirect('store:profile')

    preference_item = {
        "title": f"Pedido #{order.id} - India Oasis",
        "quantity": 1,
        "unit_price": float(order.total_price),
        "currency_id": "BRL",
    }
    back_urls = {
        "success": request.build_absolute_uri(reverse('payment_processing:payment_success')),
        "failure": request.build_absolute_uri(reverse('payment_processing:payment_failure')),
        "pending": request.build_absolute_uri(reverse('payment_processing:payment_pending')),
    }
    notification_url = request.build_absolute_uri(reverse('payment_processing:webhook'))
    preference_data = {
        "items": [preference_item],
        "payer": {
            "name": order.first_name,
            "surname": order.last_name,
            "email": order.email,
        },
        "back_urls": back_urls,
        "auto_return": "approved",
        "notification_url": notification_url,
        "external_reference": str(order.id),
    }
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        order.preference_id = preference['id']
        order.save()
        # Redireciona diretamente para o Mercado Pago
        return redirect(preference['init_point'])
    except Exception as e:
        import traceback
        print("Erro Mercado Pago:", e)
        traceback.print_exc()
        # Mostra mensagem de erro detalhada na tela para depuração
        return render(request, 'payment_processing/payment_failure.html', {
            'order': order,
            'error_message': str(e),
        })

@csrf_exempt
@require_POST
def custom_create_preference(request):
    """
    Cria uma preferência Mercado Pago customizada a partir de dados recebidos via POST (JSON)
    e retorna a URL de pagamento (init_point) no formato JSON.
    Espera um payload semelhante ao exemplo fornecido pelo usuário.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        access_token = data.get("access_token") or settings.MERCADO_PAGO_ACCESS_TOKEN
        sdk = mercadopago.SDK(access_token)

        # Monta o dicionário de requisição conforme o modelo do usuário
        preference_request = {
            "items": data.get("items", []),
            "marketplace_fee": data.get("marketplace_fee", 0),
            "payer": data.get("payer", {}),
            "back_urls": data.get("back_urls", {}),
            "differential_pricing": data.get("differential_pricing"),
            "expires": data.get("expires", False),
            "additional_info": data.get("additional_info"),
            "auto_return": data.get("auto_return", "all"),
            "binary_mode": data.get("binary_mode", True),
            "external_reference": data.get("external_reference"),
            "marketplace": data.get("marketplace"),
            "notification_url": data.get("notification_url"),
            "operation_type": data.get("operation_type", "regular_payment"),
            "payment_methods": data.get("payment_methods"),
            "shipments": data.get("shipments"),
            "statement_descriptor": data.get("statement_descriptor"),
        }
        # Remove chaves com valor None (opcional)
        preference_request = {k: v for k, v in preference_request.items() if v is not None}

        preference_response = sdk.preference().create(preference_request)
        preference = preference_response["response"]
        return JsonResponse({
            "init_point": preference.get("init_point"),
            "id": preference.get("id"),
            "sandbox_init_point": preference.get("sandbox_init_point"),
            "response": preference,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def payment_success(request):
    """
    Handles the user being redirected back after a successful payment.
    The webhook is the source of truth, this page is for user feedback.
    """
    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None

    # Clean up the session regardless
    if 'order_id' in request.session:
        del request.session['order_id']

    return render(request, 'payment_processing/payment_success.html', {'order': order})

from store.views import restore_cart_from_session

def payment_failure(request):
    """
    Handles the user being redirected back after a failed or cancelled payment.
    """
    # Restaura o carrinho salvo na sessão, se houver
    restore_cart_from_session(request)

    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None

    if order:
        order.status = 'payment_rejected'
        order.save()

    if 'order_id' in request.session:
        del request.session['order_id']

    return render(request, 'payment_processing/payment_failure.html', {'order': order})

def payment_pending(request):
    """
    Handles the user being redirected back when a payment is pending (e.g., Boleto).
    """
    # Restaura o carrinho salvo na sessão, se houver
    restore_cart_from_session(request)

    order_id = request.session.get('order_id')
    order = get_object_or_404(Order, id=order_id) if order_id else None

    if 'order_id' in request.session:
        del request.session['order_id']

    return render(request, 'payment_processing/payment_pending.html', {'order': order})

@csrf_exempt
def webhook(request):
    """
    Receives and processes payment notifications (webhooks) from Mercado Pago.
    This is the definitive way to update order status.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            if data.get("type") == "payment":
                payment_id = data["data"]["id"]

                # Fetch the full payment information from Mercado Pago
                payment_info_response = sdk.payment().get(payment_id)
                payment_info = payment_info_response["response"]

                # Find our order using the external_reference we set
                order_id = payment_info.get("external_reference")
                if not order_id:
                    return HttpResponse("External reference not found.", status=400)

                order = get_object_or_404(Order, id=order_id)

                # Avoid processing updates for already finalized orders
                if order.status in ['shipped', 'delivered', 'cancelled']:
                    return HttpResponse("Order already finalized.", status=200)

                # Update order with payment ID for reference
                order.payment_id = payment_info['id']

                # Update order status based on payment status
                payment_status = payment_info.get("status")
                if payment_status == "approved":
                    order.status = "payment_approved"
                    order.paid = True
                    # Here you could trigger other actions like sending a confirmation email
                elif payment_status == "rejected":
                    order.status = "payment_rejected"
                    order.paid = False
                    # Here you might restock items if the payment fails
                elif payment_status in ["in_process", "pending"]:
                    order.status = "pending"
                elif payment_status == "cancelled":
                     order.status = "cancelled"
                     order.paid = False

                order.save()

        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON.", status=400)
        except Exception as e:
            # Log the error for debugging, but return 200 to Mercado Pago
            # to prevent it from sending the same webhook repeatedly.
            print(f"Error processing webhook: {e}")

    # Acknowledge the notification to Mercado Pago
    return HttpResponse(status=200)

@csrf_exempt
@require_POST
def custom_create_preference(request):
    """
    Cria uma preferência Mercado Pago customizada a partir de dados recebidos via POST (JSON)
    e retorna a URL de pagamento (init_point) no formato JSON.
    Espera um payload semelhante ao exemplo fornecido pelo usuário.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        # Use access token from request data if provided, otherwise use Django settings
        access_token = data.get("access_token") or settings.MERCADO_PAGO_ACCESS_TOKEN
        sdk = mercadopago.SDK(access_token)

        # Monta o dicionário de requisição conforme o modelo do usuário
        preference_request = {
            "items": data.get("items", []),
            "marketplace_fee": data.get("marketplace_fee", 0),
            "payer": data.get("payer", {}),
            "back_urls": data.get("back_urls", {}),
            "differential_pricing": data.get("differential_pricing"),
            "expires": data.get("expires", False),
            "additional_info": data.get("additional_info"),
            "auto_return": data.get("auto_return", "all"),
            "binary_mode": data.get("binary_mode", True),
            "external_reference": data.get("external_reference"),
            "marketplace": data.get("marketplace"),
            "notification_url": data.get("notification_url"),
            "operation_type": data.get("operation_type", "regular_payment"),
            "payment_methods": data.get("payment_methods"),
            "shipments": data.get("shipments"),
            "statement_descriptor": data.get("statement_descriptor"),
        }
        # Remove chaves com valor None (opcional)
        preference_request = {k: v for k, v in preference_request.items() if v is not None}

        preference_response = sdk.preference().create(preference_request)
        preference = preference_response["response"]
        return JsonResponse({
            "init_point": preference.get("init_point"),
            "id": preference.get("id"),
            "sandbox_init_point": preference.get("sandbox_init_point"),
            "response": preference,
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
