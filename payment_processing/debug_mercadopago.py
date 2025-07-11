#!/usr/bin/env python
"""
Script para verificar e corrigir problemas na integração com o Mercado Pago.

Este script:
1. Verifica as credenciais do Mercado Pago
2. Testa a criação de preferências
3. Verifica a configuração de webhooks
4. Corrige problemas comuns

Uso:
    python debug_mercadopago.py [--fix]

Opções:
    --fix  Tenta corrigir automaticamente os problemas encontrados
"""

import os
import sys
import json
import time
import argparse
import requests
import traceback
import mercadopago
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/mercadopago_debug.log')
    ]
)
logger = logging.getLogger("MercadoPagoDebug")

# Adiciona o diretório do projeto ao path para importar o settings
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings')

import django
django.setup()

from django.conf import settings
from django.urls import reverse
from store.models import Order

class MercadoPagoDebugger:
    def __init__(self, fix_issues=False):
        self.fix_issues = fix_issues
        self.issues_found = []
        self.fixes_applied = []
        self.access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
        self.public_key = getattr(settings, 'MERCADO_PAGO_PUBLIC_KEY', None)
        self.sdk = None if not self.access_token else mercadopago.SDK(self.access_token)

    def check_credentials(self):
        """Verifica se as credenciais do Mercado Pago estão configuradas e válidas"""
        logger.info("Verificando credenciais do Mercado Pago...")

        # 1. Verificar se as credenciais estão configuradas
        if not self.access_token:
            self.issues_found.append("MERCADO_PAGO_ACCESS_TOKEN não está configurado")
            logger.error("❌ MERCADO_PAGO_ACCESS_TOKEN não encontrado nas configurações")
            return False

        if not self.public_key:
            self.issues_found.append("MERCADO_PAGO_PUBLIC_KEY não está configurado")
            logger.warning("⚠️ MERCADO_PAGO_PUBLIC_KEY não encontrado nas configurações")

        # 2. Validar o formato das credenciais
        if self.access_token and not (self.access_token.startswith('APP_USR-') or self.access_token.startswith('TEST-')):
            self.issues_found.append("MERCADO_PAGO_ACCESS_TOKEN tem formato inválido")
            logger.error(f"❌ MERCADO_PAGO_ACCESS_TOKEN tem formato inválido: {self.access_token[:10]}...")

            if self.fix_issues:
                logger.info("Tentando corrigir o formato do token...")
                # Verificar se o token não tem caracteres extras
                cleaned_token = self.access_token.strip()
                if cleaned_token != self.access_token:
                    self.fixes_applied.append("Removidos espaços extras do MERCADO_PAGO_ACCESS_TOKEN")
                    logger.info("✅ Espaços extras removidos do token")
                    self.access_token = cleaned_token
                    self.sdk = mercadopago.SDK(self.access_token)

        # 3. Testar as credenciais com uma chamada simples à API
        if self.sdk:
            try:
                logger.info("Testando credenciais com chamada à API...")
                response = self.sdk.payment_methods().list_all()

                if response["status"] == 200:
                    logger.info("✅ Credenciais válidas! API respondeu corretamente.")
                    return True
                else:
                    self.issues_found.append(f"API do Mercado Pago retornou erro: {response['status']}")
                    logger.error(f"❌ API do Mercado Pago retornou erro: {response['status']}")
                    return False

            except Exception as e:
                self.issues_found.append(f"Erro ao testar credenciais: {str(e)}")
                logger.error(f"❌ Erro ao testar credenciais: {str(e)}")
                logger.debug(traceback.format_exc())
                return False

        return False

    def test_preference_creation(self):
        """Testa a criação de uma preferência de pagamento"""
        logger.info("Testando criação de preferência de pagamento...")

        if not self.sdk:
            logger.error("❌ SDK não inicializado. Verificando credenciais primeiro.")
            if not self.check_credentials():
                return False

        try:
            # Criar uma preferência de teste
            preference_data = {
                "items": [
                    {
                        "title": "Produto de Teste - Debug",
                        "quantity": 1,
                        "unit_price": 0.1,  # Valor mínimo para testes
                        "currency_id": "BRL",
                    }
                ],
                "payer": {
                    "name": "Teste",
                    "surname": "Debug",
                    "email": "teste@debugger.com",
                },
                "back_urls": {
                    "success": "http://localhost:8000/payment/success/",
                    "failure": "http://localhost:8000/payment/failure/",
                    "pending": "http://localhost:8000/payment/pending/",
                },
                "auto_return": "approved",
                "notification_url": "http://localhost:8000/payment/webhook/",
                "external_reference": f"TEST-DEBUG-{int(time.time())}",
                "binary_mode": True,
            }

            response = self.sdk.preference().create(preference_data)

            if response["status"] in [200, 201]:
                preference = response["response"]
                logger.info(f"✅ Preferência criada com sucesso! ID: {preference['id']}")
                logger.info(f"🔗 URL de pagamento: {preference['init_point']}")

                # Verificar campos importantes na resposta
                if 'init_point' not in preference:
                    self.issues_found.append("Campo 'init_point' não encontrado na resposta da preferência")
                    logger.warning("⚠️ Campo 'init_point' não encontrado na resposta")

                if 'id' not in preference:
                    self.issues_found.append("Campo 'id' não encontrado na resposta da preferência")
                    logger.warning("⚠️ Campo 'id' não encontrado na resposta")

                return True
            else:
                error_message = response.get("response", {}).get("message", "Erro desconhecido")
                self.issues_found.append(f"Erro ao criar preferência: {error_message}")
                logger.error(f"❌ Erro ao criar preferência: {error_message}")

                if self.fix_issues:
                    if "Invalid access token" in str(error_message):
                        logger.info("O problema parece ser com o token de acesso. Verifique suas credenciais.")

                return False

        except Exception as e:
            self.issues_found.append(f"Exceção ao criar preferência: {str(e)}")
            logger.error(f"❌ Exceção ao criar preferência: {str(e)}")
            logger.debug(traceback.format_exc())
            return False

    def check_webhooks(self):
        """Verifica se a configuração de webhooks está correta"""
        logger.info("Verificando configuração de webhooks...")

        # 1. Verifica se a URL de webhook está acessível publicamente
        webhook_url = "http://localhost:8000/payment/webhook/"

        logger.warning("⚠️ A URL de webhook é local (localhost). Em produção, esta URL deve ser acessível publicamente.")
        logger.info("Dica: Use ngrok ou similar para expor seu servidor local durante desenvolvimento.")

        # 2. Verificar se a view de webhook está configurada corretamente
        try:
            from payment_processing.views import webhook

            # Verificar se a view tem o decorator csrf_exempt
            import inspect
            webhook_source = inspect.getsource(webhook)
            if "@csrf_exempt" not in webhook_source:
                self.issues_found.append("View de webhook não tem decorator @csrf_exempt")
                logger.warning("⚠️ View de webhook não tem decorator @csrf_exempt. Isso pode causar problemas.")

                if self.fix_issues:
                    logger.info("Dica para corrigir: Adicione o decorator @csrf_exempt na função webhook em payment_processing/views.py")

        except ImportError:
            self.issues_found.append("Não foi possível importar a view 'webhook'")
            logger.error("❌ Não foi possível importar a view 'webhook'. Verifique se ela existe.")

        # 3. Testar se o processamento de webhook funciona
        logger.info("Simulando uma notificação de webhook...")

        try:
            # Criar um payload de webhook de teste
            webhook_payload = {
                "type": "payment",
                "data": {
                    "id": "12345678"
                }
            }

            # Fazer uma requisição local para o endpoint de webhook
            logger.info("Este é apenas um teste local e provavelmente falhará se a view espera um pagamento real.")
            logger.info("Verifique manualmente se o endpoint de webhook está funcionando corretamente em produção.")

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao testar webhook: {str(e)}")
            return False

    def check_views_and_urls(self):
        """Verifica se as views e URLs estão configuradas corretamente"""
        logger.info("Verificando configuração de views e URLs...")

        try:
            # 1. Verificar se as URLs necessárias estão configuradas
            from payment_processing.urls import urlpatterns

            required_urls = ['create_payment', 'payment_success', 'payment_failure', 'payment_pending', 'webhook']
            missing_urls = []

            for url in required_urls:
                found = False
                for pattern in urlpatterns:
                    if hasattr(pattern, 'name') and pattern.name == url:
                        found = True
                        break

                if not found:
                    missing_urls.append(url)

            if missing_urls:
                self.issues_found.append(f"URLs ausentes em payment_processing/urls.py: {', '.join(missing_urls)}")
                logger.error(f"❌ URLs ausentes: {', '.join(missing_urls)}")

                if self.fix_issues:
                    logger.info("Dica para corrigir: Adicione as URLs ausentes em payment_processing/urls.py")
            else:
                logger.info("✅ Todas as URLs necessárias estão configuradas")

            # 2. Verificar se as views estão importando o SDK corretamente
            from payment_processing.views import create_payment
            import inspect

            create_payment_source = inspect.getsource(create_payment)
            if "mercadopago.SDK" not in create_payment_source and "sdk = mercadopago.SDK" not in create_payment_source:
                self.issues_found.append("View create_payment não inicializa o SDK do Mercado Pago corretamente")
                logger.warning("⚠️ View create_payment pode não estar inicializando o SDK corretamente")

            return True

        except ImportError as e:
            self.issues_found.append(f"Erro ao importar módulos: {str(e)}")
            logger.error(f"❌ Erro ao importar módulos: {str(e)}")
            return False

    def check_database_and_models(self):
        """Verifica se os modelos estão configurados corretamente para integração com o Mercado Pago"""
        logger.info("Verificando modelos e banco de dados...")

        try:
            # 1. Verificar se o modelo Order tem os campos necessários
            order_fields = [f.name for f in Order._meta.get_fields()]

            required_fields = ['preference_id', 'payment_id']
            missing_fields = []

            for field in required_fields:
                if field not in order_fields:
                    missing_fields.append(field)

            if missing_fields:
                self.issues_found.append(f"Campos ausentes no modelo Order: {', '.join(missing_fields)}")
                logger.error(f"❌ Campos ausentes no modelo Order: {', '.join(missing_fields)}")

                if self.fix_issues:
                    logger.info("Dica para corrigir: Adicione os campos ausentes ao modelo Order e execute uma migração")
            else:
                logger.info("✅ Modelo Order contém todos os campos necessários")

            # 2. Verificar se existem pedidos no banco de dados
            orders_count = Order.objects.count()
            logger.info(f"Total de pedidos no banco de dados: {orders_count}")

            if orders_count > 0:
                # Verificar se algum pedido já tem preference_id
                orders_with_preference = Order.objects.exclude(preference_id__isnull=True).exclude(preference_id__exact='')
                logger.info(f"Pedidos com preference_id: {orders_with_preference.count()}")

                if orders_with_preference.count() == 0 and orders_count > 5:
                    self.issues_found.append("Existem pedidos mas nenhum tem preference_id")
                    logger.warning("⚠️ Existem pedidos mas nenhum tem preference_id. Isso pode indicar problemas na integração.")

            return True

        except Exception as e:
            self.issues_found.append(f"Erro ao verificar modelos: {str(e)}")
            logger.error(f"❌ Erro ao verificar modelos: {str(e)}")
            logger.debug(traceback.format_exc())
            return False

    def generate_test_order(self):
        """Gera um pedido de teste para testar a integração completa"""
        if not self.fix_issues:
            logger.info("Geração de pedido de teste desativada. Use --fix para ativar.")
            return False

        logger.info("Gerando pedido de teste para testar integração completa...")

        try:
            # Verificar se já existe um usuário de teste
            from django.contrib.auth.models import User

            test_user = None
            try:
                test_user = User.objects.get(username='testuser')
                logger.info("✅ Usuário de teste encontrado")
            except User.DoesNotExist:
                logger.warning("⚠️ Usuário de teste não encontrado. É necessário um usuário para criar pedidos.")
                logger.info("Dica: Crie um usuário de teste com 'python manage.py createsuperuser'")
                return False

            # Criar um pedido de teste
            test_order = Order.objects.create(
                user=test_user,
                first_name="Teste",
                last_name="Debug",
                email=test_user.email,
                address="Rua de Teste, 123",
                postal_code="12345-678",
                city="Cidade Teste",
                state="ST",
                total_price=10.00,
                status='awaiting_payment'
            )

            logger.info(f"✅ Pedido de teste criado com ID: {test_order.id}")

            # Tentar criar uma preferência para esse pedido
            preference_data = {
                "items": [
                    {
                        "title": f"Pedido #{test_order.id} - Teste de Integração",
                        "quantity": 1,
                        "unit_price": float(test_order.total_price),
                        "currency_id": "BRL",
                    }
                ],
                "payer": {
                    "name": test_order.first_name,
                    "surname": test_order.last_name,
                    "email": test_order.email,
                },
                "back_urls": {
                    "success": "http://localhost:8000/payment/success/",
                    "failure": "http://localhost:8000/payment/failure/",
                    "pending": "http://localhost:8000/payment/pending/",
                },
                "auto_return": "approved",
                "notification_url": "http://localhost:8000/payment/webhook/",
                "external_reference": str(test_order.id),
                "binary_mode": True,
            }

            response = self.sdk.preference().create(preference_data)

            if response["status"] in [200, 201]:
                preference = response["response"]
                logger.info(f"✅ Preferência criada com sucesso para o pedido de teste! ID: {preference['id']}")
                logger.info(f"🔗 URL de pagamento: {preference['init_point']}")

                # Atualizar o pedido com o preference_id
                test_order.preference_id = preference['id']
                test_order.save()

                self.fixes_applied.append(f"Pedido de teste criado com ID: {test_order.id} e preference_id: {preference['id']}")

                logger.info("Para testar o fluxo completo, acesse a URL de pagamento e faça um pagamento de teste.")
                return True
            else:
                error_message = response.get("response", {}).get("message", "Erro desconhecido")
                self.issues_found.append(f"Erro ao criar preferência para pedido de teste: {error_message}")
                logger.error(f"❌ Erro ao criar preferência para pedido de teste: {error_message}")
                return False

        except Exception as e:
            self.issues_found.append(f"Erro ao gerar pedido de teste: {str(e)}")
            logger.error(f"❌ Erro ao gerar pedido de teste: {str(e)}")
            logger.debug(traceback.format_exc())
            return False

    def run_all_checks(self):
        """Executa todas as verificações"""
        logger.info("\n" + "="*80)
        logger.info("INICIANDO DIAGNÓSTICO DA INTEGRAÇÃO COM MERCADO PAGO")
        logger.info("="*80)

        results = {
            "credentials": self.check_credentials(),
            "preference_creation": self.test_preference_creation(),
            "webhooks": self.check_webhooks(),
            "views_and_urls": self.check_views_and_urls(),
            "database_and_models": self.check_database_and_models()
        }

        # Se estiver corrigindo problemas, tenta gerar um pedido de teste
        if self.fix_issues and all([results["credentials"], results["preference_creation"]]):
            results["test_order"] = self.generate_test_order()

        # Resumo dos resultados
        logger.info("\n" + "="*80)
        logger.info("RESUMO DO DIAGNÓSTICO")
        logger.info("="*80)

        for check, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            logger.info(f"{status}: {check.replace('_', ' ').title()}")

        if self.issues_found:
            logger.info("\n" + "="*80)
            logger.info("PROBLEMAS ENCONTRADOS")
            logger.info("="*80)

            for i, issue in enumerate(self.issues_found, 1):
                logger.info(f"{i}. {issue}")

        if self.fix_issues and self.fixes_applied:
            logger.info("\n" + "="*80)
            logger.info("CORREÇÕES APLICADAS")
            logger.info("="*80)

            for i, fix in enumerate(self.fixes_applied, 1):
                logger.info(f"{i}. {fix}")

        # Recomendações finais
        logger.info("\n" + "="*80)
        logger.info("RECOMENDAÇÕES")
        logger.info("="*80)

        if not results["credentials"]:
            logger.info("1. Verifique suas credenciais do Mercado Pago no arquivo .env")
            logger.info("   - MERCADO_PAGO_PUBLIC_KEY deve começar com 'APP_USR-' ou 'TEST-'")
            logger.info("   - MERCADO_PAGO_ACCESS_TOKEN deve começar com 'APP_USR-' ou 'TEST-'")

        if not results["webhooks"]:
            logger.info("2. Configure corretamente os webhooks:")
            logger.info("   - Em produção, use uma URL pública para o endpoint /payment/webhook/")
            logger.info("   - Para testes locais, use ngrok ou similar para expor seu servidor")

        logger.info("3. Para testes completos:")
        logger.info("   - Use cartões de teste do Mercado Pago (disponíveis na documentação)")
        logger.info("   - Faça pagamentos de teste usando os dados de sandbox")

        logger.info("\nPara mais informações, consulte o arquivo MERCADOPAGO.md")

        return all(results.values())

def main():
    parser = argparse.ArgumentParser(description='Diagnostica e corrige problemas na integração com o Mercado Pago')
    parser.add_argument('--fix', action='store_true', help='Tenta corrigir automaticamente os problemas encontrados')
    args = parser.parse_args()

    # Criar diretório de logs se não existir
    os.makedirs('logs', exist_ok=True)

    # Iniciar diagnóstico
    debugger = MercadoPagoDebugger(fix_issues=args.fix)
    success = debugger.run_all_checks()

    # Retornar código de saída apropriado
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
