# 🏪 India Oasis

E-commerce de temperos indianos desenvolvido com Django, focado em simplicidade, responsividade e integração com Mercado Pago para pagamentos online.

---

## 📦 Funcionalidades

- 🛍️ Vitrine de produtos com categorias e busca
- ➕ Carrinho de compras persistente (usuário ou sessão)
- 🔐 Cadastro, login e perfil de usuário com endereço
- 📦 Finalização de pedidos e histórico do cliente
- 💳 Integração com Mercado Pago (Cartão, PIX, Boleto)
- 🧾 Wishlist (lista de desejos)
- ⭐ Avaliações de produtos
- 💬 Formulário de contato e FAQ
- 📱 Interface responsiva com Bootstrap e Tailwind CSS

---

## 🚀 Tecnologias Utilizadas

- [Python 3.x](https://www.python.org/)
- [Django 5.x](https://www.djangoproject.com/)
- [SQLite3](https://www.sqlite.org/) (banco de dados padrão)
- [Bootstrap 5](https://getbootstrap.com/) + Tailwind CSS (front-end)
- [Mercado Pago SDK](https://www.mercadopago.com.br/developers/pt/docs/sdks/python)
- [Pillow](https://python-pillow.org/) (imagens)
- [django-environ](https://django-environ.readthedocs.io/) (variáveis de ambiente)

---

## 🗂️ Estrutura de Diretórios

```
india_oasis/
├── india_oasis_project/   # Configurações do projeto Django
├── store/                 # App principal: produtos, carrinho, pedidos, usuários
├── payment_processing/    # App de integração com Mercado Pago
├── templates/             # Templates HTML (Bootstrap/Tailwind)
├── static/                # Arquivos estáticos (CSS, JS, imagens)
├── media/                 # Uploads de imagens de produtos
├── requirements.txt       # Dependências Python
├── manage.py              # Comando principal do Django
└── Procfile               # Deploy (Heroku/Gunicorn)
```

---

## ⚙️ Como executar localmente

1. **Clone o repositório**
   ```bash
   git clone https://github.com/danmarquees/india_oasis.git
   cd india_oasis
   ```

2. **Crie e ative um ambiente virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/Mac
   venv\Scripts\activate.bat  # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**
   - Crie um arquivo `.env` na raiz do projeto com:
     ```
     SECRET_KEY=sua_secret_key
     DEBUG=True
     MERCADO_PAGO_PUBLIC_KEY=sua_public_key
     MERCADO_PAGO_ACCESS_TOKEN=seu_access_token
     ```

5. **Aplique as migrações**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Crie um superusuário**
   ```bash
   python manage.py createsuperuser
   ```

7. **Execute o servidor**
   ```bash
   python manage.py runserver
   ```
   Acesse: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🛒 Principais Apps

- `store`: Produtos, categorias, carrinho, pedidos, avaliações, wishlist, perfil do usuário, contato.
- `payment_processing`: Integração Mercado Pago (checkout, webhooks, status de pagamento).

---

## ✅ Futuras melhorias

- Integração com outros gateways de pagamento (ex: PayPal, Stripe)
- Testes automatizados (Pytest/Django Test)
- Upload múltiplo de imagens para produtos
- Filtros avançados e busca por atributos
- Melhor tratamento de erros e UX
- Painel administrativo customizado

---

## 📝 Licença

Este projeto está licenciado sob a MIT License.

---

## 👤 Autor

Desenvolvido por Danilo Marques  
[GitHub](https://github.com/danmarquees) • [LinkedIn](https://www.linkedin.com/in/danmarquesdev/)  
Contato: d.silvamarques@gmail.com

---