import requests

def calcular_frete_melhor_envio(cep_origem, cep_destino, peso_kg, valor_produtos, token='SEU_TOKEN_AQUI', servicos=None):
    url = 'https://api.melhorenvio.com.br/api/v2/me/shipment/calculate'
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
            "width": 15,
            "height": 10,
            "length": 20,
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