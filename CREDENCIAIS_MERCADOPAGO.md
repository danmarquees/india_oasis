# Configuração de Credenciais do Mercado Pago

Este documento explica como obter e configurar corretamente as credenciais do Mercado Pago para a integração com a India Oasis.

## 1. Obter Credenciais

Para integrar com o Mercado Pago, você precisa de duas credenciais principais:

1. **Public Key** - Usada no frontend para o checkout
2. **Access Token** - Usado no backend para criar preferências e processar pagamentos

### Passos para obter suas credenciais:

1. Acesse a [página de credenciais do Mercado Pago](https://www.mercadopago.com.br/developers/panel/credentials)
2. Faça login na sua conta do Mercado Pago (ou crie uma se não tiver)
3. Escolha o tipo de credencial:
   - **Produção**: Para transações reais
   - **Teste**: Para desenvolvimento e testes (recomendado inicialmente)
4. Copie as credenciais de **Public Key** e **Access Token**

## 2. Formato Correto das Credenciais

É crucial que as credenciais estejam no formato correto:

- **Public Key** deve começar com:
  - `TEST-` (para ambiente de teste)
  - `APP_USR-` (para ambiente de produção)

- **Access Token** deve começar com:
  - `TEST-` (para ambiente de teste)
  - `APP_USR-` (para ambiente de produção)

### Exemplo de credenciais de teste válidas:

```
PUBLIC_KEY: TEST-00000000-0000-0000-0000-000000000000
ACCESS_TOKEN: TEST-0000000000000000000000000000000000-000000-00000000000000000000000000000000-000000000
```

## 3. Configurar no arquivo .env

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas credenciais:
   ```
   MERCADO_PAGO_PUBLIC_KEY=TEST-00000000-0000-0000-0000-000000000000
   MERCADO_PAGO_ACCESS_TOKEN=TEST-0000000000000000000000000000000000-000000-00000000000000000000000000000000-000000000
   ```

## 4. Verificar a Configuração

Para verificar se suas credenciais estão configuradas corretamente, execute:

```bash
python payment_processing/check_mercadopago_api.py
```

Este script testará suas credenciais e verificará se a integração está funcionando.

## 5. Solução de Problemas Comuns

### Erro: 'id' não encontrado na resposta

Se você receber um erro como `KeyError: 'id'`, pode ser que:

1. O token de acesso esteja incorreto ou inválido
2. O formato do token esteja errado (faltando caracteres ou com espaços extras)
3. A conta do Mercado Pago não tenha permissões para criar preferências

**Solução**: Verifique se o token está correto e completo. Tente gerar um novo token no painel do Mercado Pago.

### Erro: auto_return invalid. back_url.success must be defined

Este erro ocorre quando você define o parâmetro `auto_return` mas não define corretamente a URL de retorno de sucesso.

**Solução**:
1. Certifique-se de que as URLs de retorno (`back_urls`) estão configuradas corretamente
2. Verifique se a URL de sucesso (`back_urls.success`) não está vazia
3. Confirme se todas as URLs são válidas e acessíveis publicamente

### Erro: Access Token inválido

**Solução**: Certifique-se de estar copiando o token completo, sem espaços extras. O token é longo e deve ser copiado integralmente.

### Erro: Não redireciona para o Mercado Pago

**Solução**: Execute o script de diagnóstico e verifique os logs em `logs/mercadopago.log` para identificar o problema específico.

## 6. Ambientes de Teste e Produção

### Ambiente de Teste

- Use as credenciais que começam com `TEST-`
- Os pagamentos são simulados
- Use os [cartões de teste](https://www.mercadopago.com.br/developers/pt/docs/checkout-api/integration-test/test-cards) do Mercado Pago

### Ambiente de Produção

- Use as credenciais que começam com `APP_USR-`
- Os pagamentos são reais e processados
- Certifique-se de que sua conta do Mercado Pago está completamente verificada

## 7. Recursos Adicionais

- [Documentação oficial do Mercado Pago](https://www.mercadopago.com.br/developers/pt)
- [Cartões de teste para desenvolvimento](https://www.mercadopago.com.br/developers/pt/docs/checkout-api/integration-test/test-cards)
- [Painel de desenvolvimento do Mercado Pago](https://www.mercadopago.com.br/developers/panel)