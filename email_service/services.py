import logging
import smtplib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template import Template, Context
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from store.models import Order
from .models import EmailTemplate, EmailLog, EmailConfig, EmailQueue

logger = logging.getLogger(__name__)

class EmailService:
    """
    Serviço principal para envio de e-mails
    """

    def __init__(self):
        self.default_from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@indiaoasis.com.br')
        self.email_enabled = getattr(settings, 'ORDER_EMAIL_ENABLED', True)

    def send_email(self,
                   recipient_email: str,
                   template_type: str,
                   context: Dict[str, Any],
                   recipient_name: str = None,
                   user: User = None,
                   order: Order = None,
                   priority: int = 2,
                   scheduled_at: datetime = None) -> bool:
        """
        Envia e-mail usando template específico

        Args:
            recipient_email: E-mail do destinatário
            template_type: Tipo do template (ex: 'order_confirmation')
            context: Dados para renderizar o template
            recipient_name: Nome do destinatário
            user: Usuário relacionado
            order: Pedido relacionado
            priority: Prioridade do e-mail (1=alta, 2=média, 3=baixa)
            scheduled_at: Data para envio agendado

        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        if not self.email_enabled:
            logger.info("Envio de e-mail desabilitado nas configurações")
            return False

        try:
            # Buscar template
            template = EmailTemplate.objects.get(
                email_type=template_type,
                is_active=True
            )

            # Se agendado, adicionar à fila
            if scheduled_at:
                return self._add_to_queue(
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    user=user,
                    order=order,
                    template=template,
                    context=context,
                    priority=priority,
                    scheduled_at=scheduled_at
                )

            # Enviar imediatamente
            return self._send_immediate(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                user=user,
                order=order,
                template=template,
                context=context
            )

        except EmailTemplate.DoesNotExist:
            logger.error(f"Template '{template_type}' não encontrado")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {str(e)}")
            return False

    def _add_to_queue(self, **kwargs) -> bool:
        """
        Adiciona e-mail à fila de envio
        """
        try:
            EmailQueue.objects.create(
                recipient_email=kwargs['recipient_email'],
                recipient_name=kwargs.get('recipient_name'),
                user=kwargs.get('user'),
                order=kwargs.get('order'),
                email_template=kwargs['template'],
                context_data=kwargs['context'],
                priority=kwargs.get('priority', 2),
                scheduled_at=kwargs.get('scheduled_at'),
            )
            logger.info(f"E-mail adicionado à fila: {kwargs['recipient_email']}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar e-mail à fila: {str(e)}")
            return False

    def _send_immediate(self,
                       recipient_email: str,
                       recipient_name: str,
                       user: User,
                       order: Order,
                       template: EmailTemplate,
                       context: Dict[str, Any]) -> bool:
        """
        Envia e-mail imediatamente
        """
        email_log = EmailLog.objects.create(
            recipient_email=recipient_email,
            recipient_name=recipient_name,
            user=user,
            order=order,
            email_template=template,
            subject=template.subject,
            status='pending'
        )

        try:
            # Renderizar template
            rendered_subject = self._render_template(template.subject, context)
            rendered_html = self._render_template(template.html_content, context)
            rendered_text = None

            if template.text_content:
                rendered_text = self._render_template(template.text_content, context)

            # Criar e-mail
            email = EmailMultiAlternatives(
                subject=rendered_subject,
                body=rendered_text or rendered_html,
                from_email=self.default_from_email,
                to=[recipient_email]
            )

            # Adicionar versão HTML se disponível
            if rendered_html:
                email.attach_alternative(rendered_html, "text/html")

            # Enviar
            email.send()

            # Atualizar log
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.attempts = 1
            email_log.save()

            logger.info(f"E-mail enviado com sucesso para {recipient_email}")
            return True

        except Exception as e:
            # Atualizar log com erro
            email_log.status = 'failed'
            email_log.error_message = str(e)
            email_log.attempts = 1
            email_log.save()

            logger.error(f"Erro ao enviar e-mail para {recipient_email}: {str(e)}")
            return False

    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """
        Renderiza template Django com contexto
        """
        try:
            template = Template(template_content)
            return template.render(Context(context))
        except Exception as e:
            logger.error(f"Erro ao renderizar template: {str(e)}")
            return template_content

    def process_email_queue(self, max_emails: int = 50) -> int:
        """
        Processa fila de e-mails

        Args:
            max_emails: Máximo de e-mails para processar

        Returns:
            int: Número de e-mails processados
        """
        processed = 0

        # Buscar e-mails pendentes
        pending_emails = EmailQueue.objects.filter(
            is_processed=False,
            attempts__lt=models.F('max_attempts'),
            scheduled_at__lte=timezone.now()
        ).order_by('priority', 'created_at')[:max_emails]

        for email_queue in pending_emails:
            try:
                success = self._send_immediate(
                    recipient_email=email_queue.recipient_email,
                    recipient_name=email_queue.recipient_name,
                    user=email_queue.user,
                    order=email_queue.order,
                    template=email_queue.email_template,
                    context=email_queue.context_data
                )

                email_queue.attempts += 1

                if success:
                    email_queue.is_processed = True
                    processed += 1

                email_queue.save()

            except Exception as e:
                logger.error(f"Erro ao processar e-mail da fila {email_queue.id}: {str(e)}")
                email_queue.attempts += 1
                email_queue.save()

        return processed

class OrderEmailService(EmailService):
    """
    Serviço específico para e-mails de pedidos
    """

    def send_order_confirmation(self, order: Order) -> bool:
        """
        Envia e-mail de confirmação de pedido
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Confirmado',
            'message': 'Seu pedido foi confirmado com sucesso!'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_confirmation',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def send_payment_approved(self, order: Order) -> bool:
        """
        Envia e-mail de pagamento aprovado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Pagamento Aprovado',
            'message': 'Seu pagamento foi aprovado! Seu pedido está sendo processado.'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='payment_approved',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def send_payment_rejected(self, order: Order) -> bool:
        """
        Envia e-mail de pagamento rejeitado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Pagamento Rejeitado',
            'message': 'Houve um problema com seu pagamento. Tente novamente ou entre em contato conosco.'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='payment_rejected',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def send_order_shipped(self, order: Order, tracking_code: str = None) -> bool:
        """
        Envia e-mail de pedido enviado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Enviado',
            'message': 'Seu pedido foi enviado!',
            'tracking_code': tracking_code
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_shipped',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=2  # Média prioridade
        )

    def send_order_delivered(self, order: Order) -> bool:
        """
        Envia e-mail de pedido entregue
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Entregue',
            'message': 'Seu pedido foi entregue com sucesso! Esperamos que goste dos produtos.'
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_delivered',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=2  # Média prioridade
        )

    def send_order_cancelled(self, order: Order, reason: str = None) -> bool:
        """
        Envia e-mail de pedido cancelado
        """
        context = self._get_order_context(order)
        context.update({
            'order_status': 'Cancelado',
            'message': 'Seu pedido foi cancelado.',
            'cancellation_reason': reason
        })

        return self.send_email(
            recipient_email=order.email,
            template_type='order_cancelled',
            context=context,
            recipient_name=f"{order.first_name} {order.last_name}",
            user=order.user,
            order=order,
            priority=1  # Alta prioridade
        )

    def _get_order_context(self, order: Order) -> Dict[str, Any]:
        """
        Cria contexto padrão para e-mails de pedido
        """
        return {
            'order': order,
            'order_number': order.id,
            'customer_name': f"{order.first_name} {order.last_name}",
            'customer_email': order.email,
            'order_total': order.total_price,
            'order_date': order.created.strftime('%d/%m/%Y %H:%M'),
            'order_status': order.get_status_display(),
            'order_items': order.items.all(),
            'shipping_address': {
                'address': order.address,
                'city': order.city,
                'state': order.state,
                'postal_code': order.postal_code,
            },
            'store_name': 'India Oasis',
            'store_url': 'https://www.indiaoasis.com.br',
            'support_email': getattr(settings, 'ORDER_EMAIL_ADMIN', 'suporte@indiaoasis.com.br'),
            'current_year': timezone.now().year,
        }

class UserEmailService(EmailService):
    """
    Serviço específico para e-mails de usuários
    """

    def send_welcome_email(self, user: User) -> bool:
        """
        Envia e-mail de boas-vindas
        """
        context = {
            'user': user,
            'user_name': user.first_name or user.username,
            'store_name': 'India Oasis',
            'store_url': 'https://www.indiaoasis.com.br',
            'support_email': getattr(settings, 'ORDER_EMAIL_ADMIN', 'suporte@indiaoasis.com.br'),
            'current_year': timezone.now().year,
        }

        return self.send_email(
            recipient_email=user.email,
            template_type='welcome',
            context=context,
            recipient_name=user.first_name or user.username,
            user=user,
            priority=3  # Baixa prioridade
        )

class EmailTemplateService:
    """
    Serviço para gerenciar templates de e-mail
    """

    @staticmethod
    def create_default_templates():
        """
        Cria templates padrão do sistema
        """
        default_templates = [
            {
                'name': 'Confirmação de Pedido',
                'email_type': 'order_confirmation',
                'subject': 'Pedido #{{ order_number }} Confirmado - India Oasis',
                'html_content': EmailTemplateService._get_order_confirmation_html(),
                'text_content': EmailTemplateService._get_order_confirmation_text(),
            },
            {
                'name': 'Pagamento Aprovado',
                'email_type': 'payment_approved',
                'subject': 'Pagamento Aprovado - Pedido #{{ order_number }} - India Oasis',
                'html_content': EmailTemplateService._get_payment_approved_html(),
                'text_content': EmailTemplateService._get_payment_approved_text(),
            },
            {
                'name': 'Pagamento Rejeitado',
                'email_type': 'payment_rejected',
                'subject': 'Problema com Pagamento - Pedido #{{ order_number }} - India Oasis',
                'html_content': EmailTemplateService._get_payment_rejected_html(),
                'text_content': EmailTemplateService._get_payment_rejected_text(),
            },
            {
                'name': 'Pedido Enviado',
                'email_type': 'order_shipped',
                'subject': 'Pedido #{{ order_number }} Enviado - India Oasis',
                'html_content': EmailTemplateService._get_order_shipped_html(),
                'text_content': EmailTemplateService._get_order_shipped_text(),
            },
            {
                'name': 'Pedido Entregue',
                'email_type': 'order_delivered',
                'subject': 'Pedido #{{ order_number }} Entregue - India Oasis',
                'html_content': EmailTemplateService._get_order_delivered_html(),
                'text_content': EmailTemplateService._get_order_delivered_text(),
            },
            {
                'name': 'Pedido Cancelado',
                'email_type': 'order_cancelled',
                'subject': 'Pedido #{{ order_number }} Cancelado - India Oasis',
                'html_content': EmailTemplateService._get_order_cancelled_html(),
                'text_content': EmailTemplateService._get_order_cancelled_text(),
            },
            {
                'name': 'Boas-vindas',
                'email_type': 'welcome',
                'subject': 'Bem-vindo à India Oasis!',
                'html_content': EmailTemplateService._get_welcome_html(),
                'text_content': EmailTemplateService._get_welcome_text(),
            },
        ]

        for template_data in default_templates:
            EmailTemplate.objects.update_or_create(
                email_type=template_data['email_type'],
                defaults=template_data
            )

    @staticmethod
    def _get_order_confirmation_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #fff8dc; border-radius: 12px; box-shadow: 0 2px 12px #f6e1c5; padding: 32px;">
          <h1 style="color: #d2691e; font-family: 'Teko', Arial, sans-serif;">Pedido Confirmado!</h1>
          <p>Olá {{ customer_name }},</p>
          <p>Seu pedido <strong>#{{ order_number }}</strong> foi confirmado com sucesso.</p>
          <div style="background: #f9e7c3; border-left: 4px solid #d2691e; padding: 16px; margin: 24px 0;">
            <strong>Status:</strong> {{ order_status }}<br>
            <strong>Data:</strong> {{ order_date }}<br>
            <strong>Total:</strong> R$ {{ order_total }}
          </div>
          <p>Confira os detalhes do seu pedido em sua conta ou entre em contato conosco se precisar de ajuda.</p>
          <p style="color: #a0522d;">Obrigado por escolher a India Oasis!</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_order_confirmation_text():
        return '''
Pedido Confirmado!

Olá {{ customer_name }},

Seu pedido #{{ order_number }} foi confirmado com sucesso.

Status: {{ order_status }}
Data: {{ order_date }}
Total: R$ {{ order_total }}

Confira os detalhes do seu pedido em sua conta ou entre em contato conosco se precisar de ajuda.

Obrigado por escolher a India Oasis!
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''

    @staticmethod
    def _get_payment_approved_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #e6ffe6; border-radius: 12px; box-shadow: 0 2px 12px #c3f9c9; padding: 32px;">
          <h1 style="color: #4a6741; font-family: 'Teko', Arial, sans-serif;">Pagamento Aprovado!</h1>
          <p>Olá {{ customer_name }},</p>
          <p>Recebemos o pagamento do seu pedido <strong>#{{ order_number }}</strong>. Agora é só aguardar, pois logo ele será enviado!</p>
          <div style="background: #d4f5dd; border-left: 4px solid #4a6741; padding: 16px; margin: 24px 0;">
            <strong>Status:</strong> {{ order_status }}<br>
            <strong>Data:</strong> {{ order_date }}<br>
            <strong>Total:</strong> R$ {{ order_total }}
          </div>
          <p>Você receberá um novo e-mail assim que seu pedido for despachado.</p>
          <p style="color: #4a6741;">Agradecemos a confiança!</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_payment_approved_text():
        return '''
Pagamento Aprovado!

Olá {{ customer_name }},

Recebemos o pagamento do seu pedido #{{ order_number }}. Agora é só aguardar, pois logo ele será enviado!

Status: {{ order_status }}
Data: {{ order_date }}
Total: R$ {{ order_total }}

Você receberá um novo e-mail assim que seu pedido for despachado.

Agradecemos a confiança!
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''

    @staticmethod
    def _get_payment_rejected_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #fff0f0; border-radius: 12px; box-shadow: 0 2px 12px #f9c3c3; padding: 32px;">
          <h1 style="color: #cc2936; font-family: 'Teko', Arial, sans-serif;">Pagamento Rejeitado</h1>
          <p>Olá {{ customer_name }},</p>
          <p>Houve um problema com o pagamento do seu pedido <strong>#{{ order_number }}</strong>.</p>
          <div style="background: #fbeaea; border-left: 4px solid #cc2936; padding: 16px; margin: 24px 0;">
            <strong>Status:</strong> {{ order_status }}<br>
            <strong>Data:</strong> {{ order_date }}<br>
            <strong>Total:</strong> R$ {{ order_total }}
          </div>
          <p>Por favor, tente novamente ou entre em contato conosco para mais informações.</p>
          <p style="color: #cc2936;">Estamos à disposição para ajudar!</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_payment_rejected_text():
        return '''
Pagamento Rejeitado

Olá {{ customer_name }},

Houve um problema com o pagamento do seu pedido #{{ order_number }}.

Status: {{ order_status }}
Data: {{ order_date }}
Total: R$ {{ order_total }}

Por favor, tente novamente ou entre em contato conosco para mais informações.

Estamos à disposição para ajudar!
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''

    @staticmethod
    def _get_order_shipped_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #e6f7ff; border-radius: 12px; box-shadow: 0 2px 12px #c3e6f9; padding: 32px;">
          <h1 style="color: #007bff; font-family: 'Teko', Arial, sans-serif;">Pedido Enviado!</h1>
          <p>Olá {{ customer_name }},</p>
          <p>Seu pedido <strong>#{{ order_number }}</strong> foi enviado!</p>
          <div style="background: #cce5ff; border-left: 4px solid #007bff; padding: 16px; margin: 24px 0;">
            <strong>Status:</strong> {{ order_status }}<br>
            {% if tracking_code %}
            <strong>Código de Rastreamento:</strong> {{ tracking_code }}<br>
            {% endif %}
            <strong>Data:</strong> {{ order_date }}
          </div>
          <p>Você pode acompanhar o envio usando o código de rastreamento acima.</p>
          <p style="color: #007bff;">Obrigado por escolher a India Oasis!</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_order_shipped_text():
        return '''
Pedido Enviado!

Olá {{ customer_name }},

Seu pedido #{{ order_number }} foi enviado!

Status: {{ order_status }}
{% if tracking_code %}
Código de Rastreamento: {{ tracking_code }}
{% endif %}
Data: {{ order_date }}

Você pode acompanhar o envio usando o código de rastreamento acima.

Obrigado por escolher a India Oasis!
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''

    @staticmethod
    def _get_order_delivered_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f6fff6; border-radius: 12px; box-shadow: 0 2px 12px #c3f9c3; padding: 32px;">
          <h1 style="color: #10b981; font-family: 'Teko', Arial, sans-serif;">Pedido Entregue!</h1>
          <p>Olá {{ customer_name }},</p>
          <p>Seu pedido <strong>#{{ order_number }}</strong> foi entregue com sucesso!</p>
          <div style="background: #e0ffe0; border-left: 4px solid #10b981; padding: 16px; margin: 24px 0;">
            <strong>Status:</strong> {{ order_status }}<br>
            <strong>Data:</strong> {{ order_date }}
          </div>
          <p>Esperamos que você aproveite muito seus produtos. Qualquer dúvida, estamos à disposição!</p>
          <p style="color: #10b981;">Agradecemos a preferência!</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_order_delivered_text():
        return '''
Pedido Entregue!

Olá {{ customer_name }},

Seu pedido #{{ order_number }} foi entregue com sucesso!

Status: {{ order_status }}
Data: {{ order_date }}

Esperamos que você aproveite muito seus produtos. Qualquer dúvida, estamos à disposição!

Agradecemos a preferência!
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''

    @staticmethod
    def _get_order_cancelled_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #fff0e6; border-radius: 12px; box-shadow: 0 2px 12px #f9dcc3; padding: 32px;">
          <h1 style="color: #cc2936; font-family: 'Teko', Arial, sans-serif;">Pedido Cancelado</h1>
          <p>Olá {{ customer_name }},</p>
          <p>Seu pedido <strong>#{{ order_number }}</strong> foi cancelado.</p>
          {% if cancellation_reason %}
          <div style="background: #ffe6e6; border-left: 4px solid #cc2936; padding: 16px; margin: 24px 0;">
            <strong>Motivo:</strong> {{ cancellation_reason }}
          </div>
          {% endif %}
          <p>Se tiver dúvidas ou desejar refazer seu pedido, estamos à disposição para ajudar.</p>
          <p style="color: #cc2936;">Conte sempre conosco!</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_order_cancelled_text():
        return '''
Pedido Cancelado

Olá {{ customer_name }},

Seu pedido #{{ order_number }} foi cancelado.

{% if cancellation_reason %}
Motivo: {{ cancellation_reason }}
{% endif %}

Se tiver dúvidas ou desejar refazer seu pedido, estamos à disposição para ajudar.

Conte sempre conosco!
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''

    @staticmethod
    def _get_welcome_html():
        return '''
        <div style="font-family: 'Poppins', 'Rajdhani', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #fffbe6; border-radius: 12px; box-shadow: 0 2px 12px #f9f6c3; padding: 32px;">
          <h1 style="color: #f7931e; font-family: 'Teko', Arial, sans-serif;">Bem-vindo(a) à India Oasis!</h1>
          <p>Olá {{ user_name }},</p>
          <p>É um prazer ter você conosco. Prepare-se para uma jornada pelos sabores autênticos da Índia!</p>
          <div style="background: #fff3cd; border-left: 4px solid #f7931e; padding: 16px; margin: 24px 0;">
            <strong>Dica:</strong> Explore nossos temperos, chás e receitas exclusivas em nosso site.
          </div>
          <p>Qualquer dúvida, conte com nosso suporte: <a href="mailto:{{ support_email }}" style="color: #f7931e;">{{ support_email }}</a></p>
          <p style="color: #f7931e;">Namastê! 🙏</p>
          <hr style="margin: 32px 0;">
          <p style="font-size: 12px; color: #888;">© {{ current_year }} India Oasis. Todos os direitos reservados.</p>
        </div>
        '''

    @staticmethod
    def _get_welcome_text():
        return '''
Bem-vindo(a) à India Oasis!

Olá {{ user_name }},

É um prazer ter você conosco. Prepare-se para uma jornada pelos sabores autênticos da Índia!

Dica: Explore nossos temperos, chás e receitas exclusivas em nosso site.

Qualquer dúvida, conte com nosso suporte: {{ support_email }}

Namastê! 🙏
© {{ current_year }} India Oasis. Todos os direitos reservados.
'''
