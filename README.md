# India Oasis

E-commerce de produtos indianos desenvolvido em Django.

## Funcionalidades
- Catálogo de produtos com categorias, descontos e avaliações
- Carrinho de compras e lista de desejos
- Checkout integrado com Mercado Pago
- Emissão de Nota Fiscal eletrônica (NF-e) via Olist (estrutura pronta)
- Painel administrativo customizado (produtos, banners, pedidos, etc)
- Banners dinâmicos gerenciáveis pelo admin
- Menu lateral funcional
- Sistema de notificações toast
- Frontend com Tailwind CSS (configuração local recomendada)
- **Cálculo de frete em tempo real via API da Melhor Envio**

## Instalação

### 1. Clone o repositório
```bash
git clone <repo-url>
cd india_oasis
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instale as dependências Python
```bash
pip install -r requirements.txt
```

### 4. Instale dependências extras para frete
```bash
pip install requests
```

### 5. Instale e configure o Tailwind CSS (recomendado)
```bash
npm init -y
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init
```
Edite o `tailwind.config.js` para incluir:
```js
module.exports = {
  content: [
    './templates/**/*.html',
    './store/**/*.py',
    './payment_processing/**/*.py',
  ],
  theme: { extend: {} },
  plugins: [],
}
```
Crie `static/css/tailwind.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```
Gere o CSS final:
```bash
npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/styles.css --watch
```
Inclua `{% static 'css/styles.css' %}` no seu `base.html`.

### 6. Migrações e superusuário
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Rodando o projeto
```bash
python manage.py runserver
```

Acesse: http://localhost:8000/

## Integrações
- **Mercado Pago:** Checkout transparente, webhooks e painel de pagamentos.
- **Olist/NF-e:** Estrutura pronta para emissão de notas fiscais (preencha as credenciais e adapte o payload conforme a documentação da Olist).
- **Melhor Envio:** Cálculo de frete em tempo real. Cadastre-se em [melhorenvio.com.br](https://www.melhorenvio.com.br/), gere um token de API e configure no código (substitua o placeholder `SEU_TOKEN_AQUI` em `store/services.py`).

## Desenvolvimento
- Use o painel admin para cadastrar produtos, banners, categorias, etc.
- Os banners do carrossel são totalmente gerenciáveis pelo admin.
- O menu lateral pode ser customizado em `templates/store/menu-funcional.html`.
- O frontend utiliza Tailwind CSS para estilização consistente.

## Testes
```bash
python manage.py test
```

## Dicas
- Para produção, gere o CSS do Tailwind sem `--watch` e ative o purge para remover classes não usadas.
- Configure variáveis de ambiente para credenciais sensíveis (Mercado Pago, Olist, Melhor Envio, etc).
- Use o Django Debug Toolbar para facilitar o desenvolvimento.

## Licença
MIT