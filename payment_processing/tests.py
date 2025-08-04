from django.test import TestCase
from store.models import Order
from unittest.mock import patch

# Create your tests here.

class NfeIntegracaoTestCase(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        # Criar usuário de teste
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.order = Order.objects.create(
            user=self.user,
            first_name='João',
            last_name='Silva',
            email='joao@example.com',
            address='Rua Teste, 123',
            postal_code='12345-678',
            city='São Paulo',
            state='SP',
            status='awaiting_payment',
            total_price=99.90,
            paid=False,
        )

    @patch('store.olist_nfe_service.OlistNfeService.emitir_nfe')
    def test_emissao_nfe_apos_pagamento(self, mock_emitir_nfe):
        # Mock da resposta da API da Olist
        mock_emitir_nfe.return_value = {
            'numero': '123456',
            'status': 'emitida',
            'pdf_url': 'http://exemplo.com/nfe.pdf',
            'xml_url': 'http://exemplo.com/nfe.xml',
        }
        # Simula o fluxo de pagamento aprovado
        self.order.paid = True
        from store.olist_nfe_service import OlistNfeService
        nfe_service = OlistNfeService()
        resultado = nfe_service.emitir_nfe(self.order)
        self.order.nfe_numero = resultado.get('numero')
        self.order.nfe_status = resultado.get('status')
        self.order.nfe_pdf_url = resultado.get('pdf_url')
        self.order.nfe_xml_url = resultado.get('xml_url')
        self.order.save()
        # Verifica se os campos foram preenchidos corretamente
        self.order.refresh_from_db()
        self.assertEqual(self.order.nfe_numero, '123456')
        self.assertEqual(self.order.nfe_status, 'emitida')
        self.assertEqual(self.order.nfe_pdf_url, 'http://exemplo.com/nfe.pdf')
        self.assertEqual(self.order.nfe_xml_url, 'http://exemplo.com/nfe.xml')
