import requests
from django.conf import settings

def calcular_frete_melhor_envio(cep_origem, cep_destino, peso_kg, valor_produtos, altura_cm, largura_cm, comprimento_cm, token=None, servicos=None):
    url = 'https://api.melhorenvio.com.br/api/v2/me/shipment/calculate'
    if token is None:
        token = settings.MELHOR_ENVIO_TOKEN
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    payload = {
        "from": {"postal_code": cep_origem},
        "to": {"postal_code": cep_destino},
        "products": [{
            "weight": int(peso_kg * 1000),  # em gramas
            "width": int(largura_cm),
            "height": int(altura_cm),
            "length": int(comprimento_cm),
            "insurance_value": float(valor_produtos),
            "quantity": 1
        }],
        "services": servicos or [],  # Ex: ["1", "2"] para PAC e SEDEX
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"erro": response.text} 