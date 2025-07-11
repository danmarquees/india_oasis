# Integração com Mercado Pago - India Oasis

Este documento contém instruções detalhadas para configurar e solucionar problemas na integração com o Mercado Pago na loja India Oasis.

## Configuração

### 1. Obter Credenciais do Mercado Pago

1. Acesse a [página de credenciais do Mercado Pago](https://www.mercadopago.com.br/developers/panel/credentials)
2. Faça login ou crie uma conta
3. Escolha se deseja usar credenciais de teste ou produção:
   - Para ambiente de **teste**: Use as credenciais de teste (Sandbox)
   - Para ambiente de **produção**: Use as credenciais de produção

### 2. Configurar Credenciais no Projeto

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas credenciais:
   ```
   MERCADO_PAGO_PUBLIC_KEY=SUA_PUBLIC_KEY
   MERCADO_PAGO_ACCESS_TOKEN=SEU_ACCESS_TOKEN
   ```

### 3. Testar a Integração

Execute o script de teste para verificar se a integração está funcionando corretamente:

```bash
cd india_oasis
python payment_processing/test_mercadopago.py
```

Se o teste for bem-sucedido, você verá mensagens confirmando a criação de uma preferência de pagamento.

## Fluxo de Pagamento

O fluxo de pagamento na aplicação funciona da seguinte forma:

1. O usuário adiciona produtos ao carrinho
2. O usuário vai para o checkout e confirma os detalhes de entrega
3. O usuário clica em "Finalizar e Ir para Pagamento"
4. O sistema cria um pedido (Order) no banco de dados
5. O sistema cria uma preferência de pagamento no Mercado Pago
6. O usuário é redirecionado para a página de pagamento do Mercado Pago
7. Após o pagamento, o usuário é redirecionado de volta para a loja:
   - Pagamento aprovado → Página de sucesso
   - Pagamento pendente → Página de pagamento pendente
   - Pagamento rejeitado → Página de falha de pagamento
8. O Mercado Pago envia webhooks para atualizar o status do pedido

## Solução de Problemas

### Verificar Logs

Os logs da integração com o Mercado Pago estão em:

```
logs/mercadopago.log
```

### Problemas Comuns

#### 1. Erro "Invalid Access Token"

- Verifique se o `MERCADO_PAGO_ACCESS_TOKEN` está correto no arquivo `.env`
- Certifique-se de que está usando o token de acesso (Access Token) e não a chave pública (Public Key)

#### 2. Não Redireciona para o Mercado Pago

- Verifique se a preferência está sendo criada corretamente no log
- Verifique se a URL de redirecionamento (init_point) está sendo gerada

#### 3. Falha ao Processar Pagamento

- Verifique o Payload enviado para o Mercado Pago nos logs
- Tente usar os dados de teste fornecidos pelo Mercado Pago

#### 4. Webhook não Está Atualizando o Pedido

- Verifique se a URL do webhook está acessível publicamente
- Para testes locais, use uma ferramenta como [ngrok](https://ngrok.com/) para expor o endpoint

### Dados de Teste

Use estes dados para testar pagamentos no ambiente de sandbox:

#### Cartões de Teste
| Tipo | Número | CVV | Data de Validade | Status |
|------|--------|-----|------------------|--------|
| Mastercard | 5031 4332 1540 6351 | 123 | 11/25 | Aprovado |
| Visa | 4235 6477 2802 5682 | 123 | 11/25 | Aprovado |
| Visa | 4013 5406 8274 6260 | 123 | 11/25 | Rejeitado |

#### CPFs de Teste
- 12345678909

## Configurações Avançadas

### Personalizar o Checkout

Você pode personalizar a aparência do checkout do Mercado Pago editando o arquivo `payment_processing/views.py` e adicionando opções na preferência de pagamento:

```python
preference_data = {
    # ... configurações básicas ...
    "statement_descriptor": "India Oasis",  # Nome que aparece na fatura
    "payment_methods": {
        "excluded_payment_methods": [  # Métodos de pagamento excluídos
            {"id": "bolbradesco"}
        ],
        "excluded_payment_types": [],
        "installments": 6  # Número máximo de parcelas
    },
}
```

### Alterar URLs de Retorno

As URLs de retorno são configuradas em `payment_processing/views.py`. Se você precisar alterá-las, edite o dicionário `back_urls` na função `create_payment`.

## Ambientes

- **Teste**: As credenciais de teste permitem processar pagamentos fictícios
- **Produção**: As credenciais de produção processam pagamentos reais

Para alternar entre os ambientes, basta trocar as credenciais no arquivo `.env`.

## Recursos Adicionais

- [Documentação do Mercado Pago](https://www.mercadopago.com.br/developers/pt/docs/checkout-api/landing)
- [SDK Python do Mercado Pago](https://github.com/mercadopago/sdk-python)