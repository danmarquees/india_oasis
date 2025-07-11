#!/usr/bin/env python
"""
Script para diagnosticar problemas específicos com a API do Mercado Pago.
Este script testa detalhadamente a comunicação com a API e verifica a estrutura da resposta.

Uso:
    python check_mercadopago_api.py
"""

import os
import sys
import json
import mercadopago
import traceback

# Adiciona o diretório do projeto ao path para importar o settings
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'india_oasis_project.settings')

import django
django.setup()

from django.conf import settings

# Cores para o terminal
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"

def print_header(text):
    print(f"\n{MAGENTA}{'=' * 80}{RESET}")
    print(f"{MAGENTA}{text.center(80)}{RESET}")
    print(f"{MAGENTA}{'=' * 80}{RESET}")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text):
    print(f"{CYAN}ℹ {text}{RESET}")

def print_json(data):
    print(f"{BLUE}{json.dumps(data, indent=2)}{RESET}")

def check_environment():
    """Verifica se as variáveis de ambiente necessárias estão configuradas."""
    print_header("VERIFICANDO CONFIGURAÇÕES DE AMBIENTE")

    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
    public_key = getattr(settings, 'MERCADO_PAGO_PUBLIC_KEY', None)

    if not access_token:
        print_error("MERCADO_PAGO_ACCESS_TOKEN não está configurado!")
        print_info("Configure-o no arquivo .env na raiz do projeto.")
        return False

    if not public_key:
        print_warning("MERCADO_PAGO_PUBLIC_KEY não está configurado (não é crítico, mas recomendado).")

    # Verificar formato das credenciais
    if access_token:
        if access_token.startswith('TEST-'):
            print_info("Usando ambiente de TESTE do Mercado Pago.")
        elif access_token.startswith('APP_USR-'):
            print_info("Usando ambiente de PRODUÇÃO do Mercado Pago.")
        else:
            print_error(f"Formato de MERCADO_PAGO_ACCESS_TOKEN inválido: {access_token[:8]}...")
            print_info("O token deve começar com 'TEST-' ou 'APP_USR-'. Certifique-se de copiar o token completo.")
            return False

    print_success("Configurações de ambiente verificadas.")
    return True

def test_raw_api_call():
    """Testa uma chamada direta à API do Mercado Pago para verificar a estrutura da resposta."""
    print_header("TESTE DE CHAMADA DIRETA À API")

    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
    if not access_token:
        print_error("Access token não configurado. Impossível testar.")
        return False

    # Criar instância do SDK
    try:
        sdk = mercadopago.SDK(access_token)
        print_success("SDK inicializado com sucesso.")
    except Exception as e:
        print_error(f"Erro ao inicializar SDK: {str(e)}")
        return False

    # Testar chamada simples: buscar métodos de pagamento
    try:
        print_info("Testando chamada à API para buscar métodos de pagamento...")
        response = sdk.payment_methods().list_all()

        # Verificar estrutura da resposta
        if "status" not in response:
            print_error("Resposta da API não contém campo 'status'.")
            print_info("Estrutura da resposta:")
            print_json(response)
            return False

        if response["status"] != 200:
            print_error(f"API retornou status {response['status']} (esperado: 200).")
            print_info("Estrutura da resposta:")
            print_json(response)
            return False

        if "response" not in response:
            print_error("Resposta da API não contém campo 'response'.")
            print_info("Estrutura da resposta:")
            print_json(response)
            return False

        payment_methods = response["response"]
        print_success(f"API retornou {len(payment_methods)} métodos de pagamento.")

        # Mostrar alguns métodos de pagamento
        print_info("Exemplos de métodos de pagamento:")
        for i, method in enumerate(payment_methods[:3], 1):
            print(f"  {i}. {method.get('name', 'N/A')} (ID: {method.get('id', 'N/A')})")

        if len(payment_methods) > 3:
            print_info(f"  ... e mais {len(payment_methods) - 3} métodos.")

        return True

    except Exception as e:
        print_error(f"Erro ao chamar API: {str(e)}")
        print_info("Rastreamento de pilha:")
        traceback.print_exc()
        return False

def test_create_preference(include_auto_return=False):
    """Testa a criação de uma preferência de pagamento e analisa detalhadamente a resposta."""
    print_header("TESTE DE CRIAÇÃO DE PREFERÊNCIA")

    access_token = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', None)
    if not access_token:
        print_error("Access token não configurado. Impossível testar.")
        return False

    # Criar instância do SDK
    try:
        sdk = mercadopago.SDK(access_token)
    except Exception as e:
        print_error(f"Erro ao inicializar SDK: {str(e)}")
        return False

    # Dados de teste para criar uma preferência
    preference_data = {
        "items": [
            {
                "title": "Produto de Teste - Diagnóstico API",
                "quantity": 1,
                "unit_price": 0.01,  # Valor mínimo para teste
                "currency_id": "BRL",
            }
        ],
        "payer": {
            "name": "Teste",
            "surname": "API",
            "email": "teste@teste.com",
        },
        "back_urls": {
            "success": "http://localhost:8000/payment/success/",
            "failure": "http://localhost:8000/payment/failure/",
            "pending": "http://localhost:8000/payment/pending/",
        },
        # "auto_return": "approved", # Removido para evitar o erro "auto_return invalid. back_url.success must be defined"
        "notification_url": "http://localhost:8000/payment/webhook/",
        # Nota: O auto_return só deve ser incluído quando back_urls.success estiver definido e válido
        "external_reference": "TEST-DIAG-API",
        "binary_mode": True,
    }

    try:
        print_info("Enviando requisição para criar preferência...")
        response = sdk.preference().create(preference_data)

        # Analisar estrutura da resposta
        print_info("Analisando estrutura da resposta...")

        if "status" not in response:
            print_error("Resposta da API não contém campo 'status'.")
            print_info("Estrutura da resposta:")
            print_json(response)
            return False

        status = response["status"]
        print_info(f"Status da resposta: {status}")

        if status not in [200, 201]:
            print_error(f"API retornou status {status} (esperado: 200 ou 201).")
            print_info("Estrutura da resposta:")
            print_json(response)
            return False

        if "response" not in response:
            print_error("Resposta da API não contém campo 'response'.")
            print_info("Estrutura da resposta:")
            print_json(response)
            return False

        preference = response["response"]

        # Verificar campos críticos na preferência
        required_fields = ["id", "init_point", "sandbox_init_point"]
        missing_fields = [field for field in required_fields if field not in preference]

        if missing_fields:
            print_error(f"Campos obrigatórios ausentes na resposta: {', '.join(missing_fields)}")
            print_info("Campos presentes na resposta:")
            print(", ".join(preference.keys()))
            print_info("Estrutura completa da resposta:")
            print_json(preference)
            return False

        print_success("Preferência criada com sucesso! Seu token de acesso está funcionando.")
        print_info(f"ID da preferência: {preference['id']}")
        print_info(f"URL de pagamento: {preference['init_point']}")

        # Verificar outros campos importantes
        if "items" not in preference:
            print_warning("Campo 'items' não está presente na resposta.")

        if "expires" in preference:
            print_info(f"A preferência expira: {preference['expires']}")

        return True

    except Exception as e:
        print_error(f"Erro ao criar preferência: {str(e)}")
        print_info("Rastreamento de pilha:")
        traceback.print_exc()
        return False

def check_version_compatibility():
    """Verifica a compatibilidade de versões do SDK e dependências."""
    print_header("VERIFICANDO COMPATIBILIDADE DE VERSÕES")

    # Verificar versão do SDK
    try:
        mercadopago_version = mercadopago.__version__
        print_info(f"Versão do SDK do Mercado Pago: {mercadopago_version}")

        # Verificar versão do requests
        import requests
        requests_version = requests.__version__
        print_info(f"Versão do requests: {requests_version}")

        # Verificar versão do Python
        python_version = sys.version.split()[0]
        print_info(f"Versão do Python: {python_version}")

        # Verificar se é uma versão conhecida por ter problemas
        if mercadopago_version == "2.0.0":
            print_warning("A versão 2.0.0 do SDK do Mercado Pago tem problemas conhecidos. Considere atualizar para 2.2.0 ou posterior.")

        return True
    except AttributeError:
        print_warning("Não foi possível determinar a versão do SDK do Mercado Pago.")
        print_info("Isso não é crítico, mas pode indicar um SDK desatualizado.")
        return True
    except Exception as e:
        print_error(f"Erro ao verificar versões: {str(e)}")
        return False

def suggest_fixes(issues):
    """Sugere correções para os problemas encontrados."""
    print_header("SUGESTÕES DE CORREÇÃO")

    if not issues:
        print_success("Nenhum problema crítico encontrado que precise de correção.")
        return

    for issue, suggestion in issues:
        print_error(f"Problema: {issue}")
        print_info(f"Sugestão: {suggestion}")
        print()

def main():
    """Função principal do script."""
    print_header("DIAGNÓSTICO DA API DO MERCADO PAGO")
    print("Este script testa a integração com a API do Mercado Pago e identifica problemas.")

    issues = []

    # Verificar ambiente
    if not check_environment():
        issues.append((
            "Configurações de ambiente incorretas",
            "Verifique se as variáveis MERCADO_PAGO_ACCESS_TOKEN e MERCADO_PAGO_PUBLIC_KEY estão configuradas corretamente no arquivo .env. Certifique-se de que o token está completo e não contém espaços extras."
        ))

    # Verificar compatibilidade de versões
    if not check_version_compatibility():
        issues.append((
            "Problemas de compatibilidade de versões",
            "Atualize o SDK do Mercado Pago para a versão mais recente: pip install mercadopago==2.2.0"
        ))

    # Testar chamada direta à API
    if not test_raw_api_call():
        issues.append((
            "Falha na comunicação básica com a API",
            "Verifique sua conexão com a internet e se o token de acesso é válido. Também confirme se não há um firewall bloqueando as requisições."
        ))
    else:
        # Se a chamada básica funcionar, testa a criação de preferência sem auto_return
        if not test_create_preference(include_auto_return=False):
            issues.append((
                "Falha na criação de preferência de pagamento",
                "Verifique se o token de acesso tem permissões para criar preferências. Se você recebeu o erro 'auto_return invalid', verifique se as back_urls estão configuradas corretamente. Em ambiente de sandbox, certifique-se de que sua conta está configurada corretamente."
            ))

    # Sugerir correções
    suggest_fixes(issues)

    # Resultado final
    print_header("RESULTADO FINAL")
    if not issues:
        print_success("Todos os testes passaram com sucesso! A API do Mercado Pago está funcionando corretamente.")
        print_info("Se você ainda estiver tendo problemas com a integração, verifique a lógica específica de sua aplicação.")
        sys.exit(0)
    else:
        print_error(f"Foram encontrados {len(issues)} problemas que precisam ser corrigidos.")
        print_info("Consulte as sugestões acima para resolver os problemas.")
        sys.exit(1)

if __name__ == "__main__":
    main()
