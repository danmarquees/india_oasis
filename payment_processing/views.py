import mercadopago
import json
import logging
import traceback
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from store.models import Order
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from .models import Notification
from store.olist_nfe_service import OlistNfeService

# Configurar logger
logger = logging.getLogger(__name__)

# Initialize Mercado Pago SDK with your Access Token
sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)

def create_payment(request):
    """
    Cria uma preferência de pagamento no Mercado Pago e redireciona automaticamente o usuário para o checkout.
    """
    logger = logging.getLogger(__name__)
    logger.info("Iniciando criação de pagamento no Mercado Pago")

    order_id = request.session.get('order_id')
    if not order_id:
        logger.error("Nenhum ID de pedido encontrado na sessão")
        return redirect('store:cart')

    order = get_object_or_404(Order, id=order_id)
    if order.paid:
        logger.info(f"Pedido {order_id} já está pago. Redirecionando para perfil.")
        return redirect('store:profile')

    logger.info(f"Criando preferência para o pedido {order_id} no valor de R$ {order.total_price}")

    preference_item = {
        "title": f"Pedido #{order.id} - India Oasis",
        "quantity": 1,
        "unit_price": float(order.total_price),
        "currency_id": "BRL",
    }
    # Definir URLs de retorno com validação
    try:
        success_url = request.build_absolute_uri(reverse('payment_processing:payment_success'))
        failure_url = request.build_absolute_uri(reverse('payment_processing:payment_failure'))
        pending_url = request.build_absolute_uri(reverse('payment_processing:payment_pending'))

        # Verificar se as URLs são válidas
        for url_name, url in [("success", success_url), ("failure", failure_url), ("pending", pending_url)]:
            if not url or not url.startswith('http'):
                logger.warning(f"URL de retorno inválida para {url_name}: {url}")
                # Usar URLs absolutas com domínio hardcoded para desenvolvimento se necessário
                if url_name == "success":
                    success_url = "https://www.indiaoasis.com.br/payment/success/"
                elif url_name == "failure":
                    failure_url = "https://www.indiaoasis.com.br/payment/failure/"
                elif url_name == "pending":
                    pending_url = "https://www.indiaoasis.com.br/payment/pending/"

        back_urls = {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url,
        }

        logger.info(f"URLs de retorno configuradas: {back_urls}")
    except Exception as e:
        logger.error(f"Erro ao configurar URLs de retorno: {str(e)}")
        # Usar URLs absolutas como fallback
        back_urls = {
            "success": "https://www.indiaoasis.com.br/payment/success/",
            "failure": "https://www.indiaoasis.com.br/payment/failure/",
            "pending": "https://www.indiaoasis.com.br/payment/pending/",
        }

    # URL de notificação (webhook)
    try:
        # Mercado Pago doesn't accept localhost or 127.0.0.1 URLs for notifications
        # Always use a production URL for notification_url
        notification_url = "https://www.indiaoasis.com.br/payment/webhook/"
        logger.info(f"Usando URL de notificação produção: {notification_url}")
    except Exception as e:
        logger.error(f"Erro ao configurar URL de notificação: {str(e)}")
        notification_url = "https://www.indiaoasis.com.br/payment/webhook/"

    # Remover completamente auto_return para evitar erros com a API
    preference_data = {
        "items": [preference_item],
        "payer": {
            "name": order.first_name,
            "surname": order.last_name,
            "email": order.email,
        },
        "back_urls": back_urls,
        # Removido auto_return para evitar o erro
        # Mercado Pago API rejects localhost URLs for notifications
        "notification_url": notification_url,
        "external_reference": str(order.id),
        "binary_mode": True,  # Modo binário para evitar estados pendentes em alguns casos
    }

    # Auto_return foi removido para evitar erros com a API
    try:
        logger.info("Enviando dados para API do Mercado Pago")
        logger.info(f"Payload: {json.dumps(preference_data, indent=2, ensure_ascii=False)}")
        preference_response = sdk.preference().create(preference_data)

        # Log detalhado da resposta
        logger.info(f"Resposta completa da API: {json.dumps(preference_response, indent=2, ensure_ascii=False)}")

        # Verificar se a resposta contém os dados esperados
        if preference_response["status"] in [200, 201] and "response" in preference_response:
            preference = preference_response["response"]

            # Verificar se os campos necessários existem
            if "id" not in preference or "init_point" not in preference:
                logger.error(f"Resposta do Mercado Pago incompleta: {preference}")
                return render(request, 'payment_processing/payment_failure.html', {
                    'order': order,
                    'error_message': "Resposta da API do Mercado Pago está incompleta. Não foi possível obter ID ou URL de pagamento.",
                })

            logger.info(f"Preferência criada com sucesso: {preference['id']}")

            order.preference_id = preference['id']
            order.save()

            # Redireciona diretamente para o Mercado Pago
            logger.info(f"Redirecionando para: {preference['init_point']}")
            return redirect(preference['init_point'])
        else:
            # Resposta inválida ou erro na API
            error_message = preference_response.get("response", {}).get("message", "Erro desconhecido na API do Mercado Pago")
            logger.error(f"Erro na resposta da API: {json.dumps(preference_response, indent=2, ensure_ascii=False)}")
            return render(request, 'payment_processing/payment_failure.html', {
                'order': order,
                'error_message': error_message,
            })
    except Exception as e:
        logger.error(f"Erro ao criar preferência no Mercado Pago: {str(e)}")
        logger.error(traceback.format_exc())

        # Se for KeyError, é provavelmente um problema na estrutura da resposta
        error_message = str(e)
        if isinstance(e, KeyError):
            error_message = f"Resposta da API não contém o campo esperado: {str(e)}. Verifique as credenciais do Mercado Pago."

            # Verificar se as credenciais estão corretas
            if not settings.MERCADO_PAGO_ACCESS_TOKEN or len(settings.MERCADO_PAGO_ACCESS_TOKEN) < 20:
                error_message += " O token de acesso (MERCADO_PAGO_ACCESS_TOKEN) parece estar incorreto ou ausente."

        # Mostra mensagem de erro detalhada na tela para depuração
        return render(request, 'payment_processing/payment_failure.html', {
            'order': order,
            'error_message': error_message,
            'traceback': traceback.format_exc() if settings.DEBUG else None,
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

        # Log da resposta para debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Mercado Pago preference created: {preference['id']}")

        return JsonResponse({
            "init_point": preference.get("init_point"),
            "id": preference.get("id"),
            "sandbox_init_point": preference.get("sandbox_init_point"),
            "response": preference,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e), "traceback": traceback.format_exc()}, status=400)

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
                    # Emissão de NF-e via Olist
                    try:
                        nfe_service = OlistNfeService()
                        resultado = nfe_service.emitir_nfe(order)
                        order.nfe_numero = resultado.get('numero')
                        order.nfe_status = resultado.get('status')
                        order.nfe_pdf_url = resultado.get('pdf_url')
                        order.nfe_xml_url = resultado.get('xml_url')
                    except Exception as nfe_exc:
                        print(f"Erro ao emitir NF-e: {nfe_exc}")
                    # Aqui você poderia disparar outras ações como envio de e-mail de confirmação
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

# A função custom_create_preference foi removida daqui pois estava duplicada

@staff_member_required
def painel_pagamentos(request):
    # Filtro de status
    status_filtro = request.GET.get('status', '')
    pedidos_qs = Order.objects.all()
    if status_filtro:
        pedidos_qs = pedidos_qs.filter(status=status_filtro)
    ultimos_pedidos = pedidos_qs.order_by('-created')[:10]
    # Contar pedidos por status
    status_counts = (
        Order.objects.values('status')
        .annotate(total=Count('id'))
        .order_by()
    )
    status_labels = [s['status'] for s in status_counts]
    status_data = [s['total'] for s in status_counts]
    # Alertas
    pedidos_pendentes = Order.objects.filter(status__icontains='pending').count()
    pedidos_erro = Order.objects.filter(status__icontains='erro').count()
    alertas = []
    if pedidos_pendentes > 0:
        alertas.append(f"Há {pedidos_pendentes} pagamento(s) pendente(s) aguardando ação.")
    if pedidos_erro > 0:
        alertas.append(f"Há {pedidos_erro} pagamento(s) com erro!")
    # Status únicos para filtro
    status_unicos = Order.objects.values_list('status', flat=True).distinct()
    return render(request, "admin/payment_processing/painel_pagamentos.html", {
        'ultimos_pedidos': ultimos_pedidos,
        'status_labels': status_labels,
        'status_data': status_data,
        'alertas': alertas,
        'status_filtro': status_filtro,
        'status_unicos': status_unicos,
    })

@staff_member_required
def notificacoes_recentes(request):
    notificacoes = Notification.objects.order_by('-created_at')[:10]
    data = [
        {
            'id': n.id,
            'event_type': n.get_event_type_display(),
            'message': n.message,
            'created_at': n.created_at.strftime('%d/%m/%Y %H:%M'),
            'is_read': n.is_read,
        }
        for n in notificacoes
    ]
    return JsonResponse({'notificacoes': data, 'nao_lidas': Notification.objects.filter(is_read=False).count()})

@staff_member_required
def reprocessar_pedido(request, pedido_id):
    pedido = get_object_or_404(Order, id=pedido_id)
    # Aqui você pode colocar a lógica real de reprocessamento
    pedido.status = 'processing'
    pedido.save()
    return JsonResponse({'success': True, 'msg': f'Pedido {pedido.id} reprocessado!'})

@staff_member_required
def cancelar_pedido(request, pedido_id):
    pedido = get_object_or_404(Order, id=pedido_id)
    pedido.status = 'cancelled'
    pedido.save()
    return JsonResponse({'success': True, 'msg': f'Pedido {pedido.id} cancelado!'})

@staff_member_required
def reprocessar_todos_pendentes(request):
    pendentes = Order.objects.filter(status__icontains='pending')
    for pedido in pendentes:
        pedido.status = 'processing'
        pedido.save()
    return JsonResponse({'success': True, 'msg': f'{pendentes.count()} pedidos reprocessados!'})
