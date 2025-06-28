#!/bin/bash

# Ativar o ambiente virtual
source venv/bin/activate

# Executar as migrações
python manage.py makemigrations
python manage.py migrate


# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Iniciar o servidor
python manage.py runserver 0.0.0.0:8000

echo "India Oasis E-commerce está rodando em http://localhost:8000"
