import requests

BASE_URL = "http://127.0.0.1:8000"

def test_custom_create_preference():
    # Payload de exemplo (ajuste conforme necessário)
    payload = {
        "items": [
            {
                "id": "1234",
                "title": "Produto Teste",
                "description": "Descrição do produto de teste",
                "picture_url": "https://www.myapp.com/myimage.jpg",
                "category_id": "services",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": 99.90,
            }
        ],
        "payer": {
            "name": "Test",
            "surname": "User",
            "email": "test_user_123456@testuser.com",
            "phone": { "area_code": "11", "number": "999999999" },
            "identification": { "type": "CPF", "number": "19119119100" },
            "address": {
                "zip_code": "06233200",
                "street_name": "Rua Exemplo",
                "street_number": 123,
            }
        },
        "back_urls": {
            "success": BASE_URL + "/payment/success/",
            "failure": BASE_URL + "/payment/failure/",
            "pending": BASE_URL + "/payment/pending/"
        },
        "notification_url": BASE_URL + "/payment/webhook/",
        "external_reference": "test-1234",
        "auto_return": "all",
        "binary_mode": True
    }

    response = requests.post(
        BASE_URL + "/payment/custom_create/",
        json=payload
    )
    assert response.status_code == 200
    data = response.json()
    assert "init_point" in data
    print("URL de pagamento Mercado Pago:", data["init_point"])
