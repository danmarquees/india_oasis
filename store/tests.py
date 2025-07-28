from django.test import TestCase
from unittest.mock import patch
from store.services import calcular_frete_melhor_envio

# Create your tests here.

class CalculoFreteMelhorEnvioTest(TestCase):
    @patch('store.services.requests.post')
    def test_calculo_frete_melhor_envio(self, mock_post):
        # Mock da resposta da API
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = [{
            'id': '1',
            'name': 'PAC',
            'price': 25.50,
            'delivery_time': 7
        }]
        resultado = calcular_frete_melhor_envio(
            cep_origem='01034-001',
            cep_destino='01001-000',
            peso_kg=1.0,
            valor_produtos=100.0,
            altura_cm=10,
            largura_cm=15,
            comprimento_cm=20,
            servicos=["1"]
        )
        self.assertIsInstance(resultado, list)
        self.assertEqual(resultado[0]['name'], 'PAC')
        self.assertEqual(resultado[0]['price'], 25.50)
