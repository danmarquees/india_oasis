#!/usr/bin/env python
"""
Script para testar a integração com a API do Mercado Pago.
Este script valida se as credenciais estão configuradas corretamente e testa
a criação de uma preferência de pagamento.

Uso:
    python test_mercadopago.py

Requer:
    Django configurado com as credenciais do Mercado Pago no settings.py
    ou em variáveis de ambiente.
"""

import os
import sys
import json
import mercadopago
import logging
from urllib.parse import urljoin

# Adiciona o diretório do projeto ao path para importar o settings
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings')

import django
django.setup()

from django.conf import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_credentials():
    """Testa se as credenciais da API do Mercado Pago estão configuradas corretamente."""

    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
    public_key = getattr(settings, 'MERCADO_PAGO_PUBLIC_KEY', None)

    if not access_token:
        logger.error("MERCADO_PAGO_ACCESS_TOKEN não está configurado!")
        return False

    if not public_key:
        logger.warning("MERCADO_PAGO_PUBLIC_KEY não está configurado!")

    logger.info(f"Credenciais encontradas: Public Key: {public_key[:8]}... / Access Token: {access_token[:8]}...")
    return True

def test_create_preference():
    """Testa a criação de uma preferência de pagamento no Mercado Pago."""

    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)

    if not access_token:
        logger.error("MERCADO_PAGO_ACCESS_TOKEN não está configurado!")
        return False

    try:
        # Inicializa SDK do Mercado Pago
        sdk = mercadopago.SDK(access_token)

        # Cria dados de exemplo para teste
        preference_data = {
            "items": [
                {
                    "title": "Produto de Teste",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "currency_id": "BRL",
                }
            ],
            "payer": {
                "name": "João",
                "surname": "Silva",
                "email": "teste@teste.com",
            },
            "back_urls": {
                "success": "http://localhost:8000/payment/success/",
                "failure": "http://localhost:8000/payment/failure/",
                "pending": "http://localhost:8000/payment/pending/",
            },
            # Note: auto_return só deve ser usado se back_urls.success estiver definido
            "auto_return": "approved",
            "notification_url": "http://localhost:8000/payment/webhook/",
            "external_reference": "TEST-1234",
            "binary_mode": True,
        }

        # Envia requisição para criar preferência
        logger.info("Enviando requisição para criar preferência...")
        response = sdk.preference().create(preference_data)

        # Verifica se a resposta foi bem-sucedida
        if response["status"] == 201 or response["status"] == 200:
            preference = response["response"]
            logger.info(f"Preferência criada com sucesso! ID: {preference['id']}")
            logger.info(f"URL de pagamento: {preference['init_point']}")

            # Imprimir detalhes da preferência para depuração
            logger.info("Detalhes da preferência:")
            logger.info(json.dumps(preference, indent=2))

            return True
        else:
            logger.error(f"Erro ao criar preferência: {response['status']}")
            logger.error(json.dumps(response, indent=2))
            return False

    except Exception as e:
        logger.error(f"Exceção ao criar preferência: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_payment_methods():
    """Testa a obtenção dos métodos de pagamento disponíveis."""

    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)

    if not access_token:
        logger.error("MERCADO_PAGO_ACCESS_TOKEN não está configurado!")
        return False

    try:
        # Inicializa SDK do Mercado Pago
        sdk = mercadopago.SDK(access_token)

        # Busca métodos de pagamento disponíveis
        logger.info("Buscando métodos de pagamento disponíveis...")
        response = sdk.payment_methods().list_all()

        # Verifica se a resposta foi bem-sucedida
        if response["status"] == 200:
            payment_methods = response["response"]
            logger.info(f"Total de métodos de pagamento disponíveis: {len(payment_methods)}")

            # Lista os métodos de pagamento disponíveis
            for method in payment_methods:
                logger.info(f"- {method['name']} (ID: {method['id']})")

            return True
        else:
            logger.error(f"Erro ao buscar métodos de pagamento: {response['status']}")
            return False

    except Exception as e:
        logger.error(f"Exceção ao buscar métodos de pagamento: {str(e)}")
        return False

def run_all_tests():
    """Executa todos os testes de integração com o Mercado Pago."""

    logger.info("=== INICIANDO TESTES DE INTEGRAÇÃO COM MERCADO PAGO ===")

    # Testa credenciais
    logger.info("\n1. Testando credenciais da API...")
    if not test_api_credentials():
        logger.error("Teste de credenciais falhou!")
        return False

    # Testa métodos de pagamento
    logger.info("\n2. Testando métodos de pagamento...")
    if not test_payment_methods():
        logger.error("Teste de métodos de pagamento falhou!")

    # Testa criação de preferência
    logger.info("\n3. Testando criação de preferência...")
    if not test_create_preference():
        logger.error("Teste de criação de preferência falhou!")
        return False

    logger.info("\n=== TESTES CONCLUÍDOS COM SUCESSO ===")
    return True

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
