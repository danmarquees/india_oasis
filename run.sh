#!/bin/bash

# Ativar o ambiente virtual
source venv/bin/activate

# Executar as migrações
python manage.py makemigrations
python manage.py migrate

# Carregar dados iniciais
python manage.py load_initial_data

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Copiar arquivos de template para o diretório de templates
mkdir -p templates/store
cp -r templates_source/*.html templates/store/

# Copiar arquivos estáticos do template para o diretório static
mkdir -p static/css static/js static/images
cp -r templates_source/assets/css/* static/css/
cp -r templates_source/assets/js/* static/js/

# Iniciar o servidor
python manage.py runserver 0.0.0.0:8000

echo "India Oasis E-commerce está rodando em http://localhost:8000"
