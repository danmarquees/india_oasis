# 🏪 India Oasis

Projeto de e-commerce simples desenvolvido com Django, com funcionalidades básicas como vitrine de produtos, carrinho de compras, sistema de pedidos e autenticação de usuários.

---

## 📦 Funcionalidades

- 🛍️ Visualização de produtos
- ➕ Adição e remoção de produtos no carrinho
- 🔐 Cadastro e login de usuários
- 📦 Finalização de pedidos
- 🧾 Histórico de pedidos (simples)
- 💬 Interface responsiva com Bootstrap

---

## 🚀 Tecnologias Utilizadas

- [Python 3.x](https://www.python.org/)
- [Django 5.x](https://www.djangoproject.com/)
- [SQLite3](https://www.sqlite.org/) (banco de dados padrão)
- [Bootstrap 5](https://getbootstrap.com/)

---

## ⚙️ Como executar localmente

### 1. Clone o repositório
```bash
git clone https://github.com/danmarquees/india_oasis.git
cd india_oasis

2. Crie e ative um ambiente virtual

python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate.bat  # Windows

3. Instale as dependências

pip install -r requirements.txt

    Se o arquivo requirements.txt não existir, você pode gerar com:

pip freeze > requirements.txt

4. Aplique as migrações

python manage.py makemigrations
python manage.py migrate

5. Crie um superusuário

python manage.py createsuperuser

6. Execute o servidor

python manage.py runserver

Acesse: http://127.0.0.1:8000
🗂️ Estrutura de Diretórios

india_oasis/
├── accounts/       # Gerenciamento de usuários
├── cart/           # Carrinho de compras
├── orders/         # Processamento de pedidos
├── store/          # Vitrine de produtos
├── india_oasis/    # Configurações do projeto Django
├── templates/      # HTMLs baseados em Bootstrap
├── manage.py       # Comando principal do Django

✅ Futuras melhorias

    Pagamento integrado com gateways (ex: PayPal, Stripe)

    Testes automatizados

    Upload de imagens para produtos

    Filtro e busca de produtos

    Melhor tratamento de erros

    Interface administrativa personalizada

📄 Licença

Este projeto está licenciado sob a MIT License.
👤 Autor

Desenvolvido por Danilo Marques
GitHub • LinkedIn • Email: d.silvamarques@gmail.com
