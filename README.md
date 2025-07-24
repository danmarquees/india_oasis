# India Oasis

E-commerce de produtos indianos desenvolvido em Django.

## Funcionalidades Principais

- **Catálogo de produtos** com categorias, descontos, avaliações e banners dinâmicos.
- **Carrinho de compras** robusto (AJAX, contador dinâmico, persistência por usuário/sessão).
- **Lista de desejos** (wishlist) integrada.
- **Checkout** integrado com Mercado Pago (pagamento transparente, webhooks, painel administrativo).
- **Emissão de Nota Fiscal eletrônica (NF-e)** via Olist (estrutura pronta para integração).
- **Cálculo de frete em tempo real** via API da Melhor Envio.
- **Painel administrativo customizado** (produtos, banners, pedidos, usuários, etc).
- **Sistema de notificações toast** para feedback ao usuário (sucesso, erro, promoções, etc).
- **Frontend moderno** com Tailwind CSS, responsivo e com componentes reutilizáveis.
- **Menu lateral retrátil** e navegação SPA-like (com AJAX e atualização dinâmica de contadores).
- **Sistema de reviews** com estrelas, comentários e destaques na home.
- **Salvamento e restauração de carrinho** (localStorage).
- **Testes automatizados** para backend e integrações.

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

### 5. Instale e configure o Tailwind CSS (recomendado para desenvolvimento)

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

- **Mercado Pago:** Checkout transparente, webhooks e painel de pagamentos. Configure as credenciais no admin ou em variáveis de ambiente.
- **Olist/NF-e:** Estrutura pronta para emissão de notas fiscais (preencha as credenciais e adapte o payload conforme a documentação da Olist).
- **Melhor Envio:** Cálculo de frete em tempo real. Cadastre-se em [melhorenvio.com.br](https://www.melhorenvio.com.br/), gere um token de API e configure no código (substitua o placeholder `SEU_TOKEN_AQUI` em `store/services.py`).

## Desenvolvimento

- Use o painel admin para cadastrar produtos, banners, categorias, etc.
- Os banners do carrossel são totalmente gerenciáveis pelo admin.
- O menu lateral pode ser customizado em `templates/store/menu-funcional.html`.
- O frontend utiliza Tailwind CSS para estilização consistente.
- Scripts customizados em `static/js/` (ex: `script.js`, `toast-system.js`).
- Templates principais em `templates/store/` (ex: `index.html`, `products.html`, `cart.html`, `checkout.html`).

## Testes

```bash
python manage.py test
```

## Dicas

- Para produção, gere o CSS do Tailwind sem `--watch` e ative o purge para remover classes não usadas.
- Configure variáveis de ambiente para credenciais sensíveis (Mercado Pago, Olist, Melhor Envio, etc).
- Use o Django Debug Toolbar para facilitar o desenvolvimento.
- O contador do minicarrinho é atualizado via AJAX em todas as páginas, garantindo consistência.
- O carrinho e wishlist funcionam para usuários autenticados e anônimos (sessão).

## Licença

MIT