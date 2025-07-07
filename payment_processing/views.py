import mercadopago
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from store.models import Order

# Initialize Mercado Pago SDK with your Access Token
sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

def create_payment(request):
    """
    Creates a Mercado Pago payment preference and renders a page
    with the payment button.
    """
    order_id = request.session.get('order_id')
    if not order_id:
        # Redirect if no order is found in the session
        return redirect('store:cart_detail')

    order = get_object_or_404(Order, id=order_id)

    # For safety, don't allow re-payment of an already paid order
    if order.paid:
        return redirect('store:profile')

    # Prepare a single item representing the entire order for simplicity
    # Mercado Pago works best when the sum of items matches the total amount
    preference_item = {
        "title": f"Pedido #{order.id} - India Oasis",
        "quantity": 1,
        "unit_price": float(order.total_price),
        "currency_id": "BRL",
    }

    # Define the URLs for redirection after payment
    back_urls = {
        "success": request.build_absolute_uri(reverse('payment_processing:payment_success')),
        "failure": request.build_absolute_uri(reverse('payment_processing:payment_failure')),
        "pending": request.build_absolute_uri(reverse('payment_processing:payment_pending')),
    }

    # The notification URL is our webhook endpoint
    notification_url = request.build_absolute_uri(reverse('payment_processing:webhook'))

    # Create the complete preference payload
    preference_data = {
        "items": [preference_item],
        "payer": {
            "name": order.first_name,
            "surname": order.last_name,
            "email": order.email,
        },
        "back_urls": back_urls,
        "auto_return": "approved", # Automatically redirect for approved payments
        "notification_url": notification_url,
        "external_reference": str(order.id), # Link the payment to our order ID
    }

    try:
        # Create the preference using the SDK
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        # Save the preference ID to our order model for reference
        order.preference_id = preference['id']
        order.save()

        # Render the payment page, passing the necessary data to the template
        context = {
            'preference_id': preference['id'],
            'MERCADO_PAGO_PUBLIC_KEY': settings.MERCADO_PAGO_PUBLIC_KEY,
            'order': order,
        }
        # This template should contain the Mercado Pago Brick script
        return render(request, 'payment_processing/create_payment.html', context)

    except Exception as e:
        # Handle exceptions from the Mercado Pago API (e.g., invalid data)
        # Log the error and show a user-friendly message
        print(f"Error creating payment preference: {e}")
        # You should have a specific error page
        return redirect('payment_processing:payment_failure')

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

def payment_failure(request):
    """
    Handles the user being redirected back after a failed or cancelled payment.
    """
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
