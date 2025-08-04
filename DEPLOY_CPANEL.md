# India Oasis - Guia de Deploy para cPanel GoDaddy

Este guia fornece instruções completas para fazer o deploy do e-commerce India Oasis adaptado para hospedagem cPanel da GoDaddy.

## 📋 Pré-requisitos

### Hospedagem Compatível
- **GoDaddy Web Hosting (cPanel)**: Deluxe, Premium, Unlimited ou Ultimate
- **NÃO compatível**: Economy shared hosting
- **Python**: Versão 3.7+ disponível via Python Selector
- **MySQL**: Banco de dados MySQL/MariaDB
- **Espaço**: Mínimo 2GB de armazenamento

### Conhecimentos Necessários
- Acesso ao cPanel
- Conceitos básicos de Django
- Configuração de banco MySQL
- Upload de arquivos via FTP/File Manager

## 🚀 Instalação Passo a Passo

### 1. Preparação dos Arquivos

#### 1.1 Download e Preparação Local
```bash
# Baixar projeto adaptado para cPanel
git clone https://github.com/your-repo/india-oasis.git
cd india-oasis

# Instalar dependências localmente para teste
pip install -r requirements-cpanel.txt

# Configurar ambiente
cp .env.cpanel.example .env
```

#### 1.2 Configurar .env
Edite o arquivo `.env` com suas configurações:

```env
# Django Core
SECRET_KEY=sua-chave-secreta-muito-longa-aqui
DEBUG=False
ALLOWED_HOSTS=seudominio.com,www.seudominio.com

# MySQL Database (obter do cPanel)
DB_NAME=seu_banco_mysql
DB_USER=seu_usuario_mysql
DB_PASSWORD=sua_senha_mysql
DB_HOST=localhost

# Email
EMAIL_HOST=localhost
EMAIL_HOST_USER=noreply@seudominio.com
EMAIL_HOST_PASSWORD=sua_senha_email
DEFAULT_FROM_EMAIL=noreply@seudominio.com
ORDER_EMAIL_ADMIN=admin@seudominio.com

# MercadoPago
MERCADO_PAGO_PUBLIC_KEY=APP_USR-sua-chave-publica
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-seu-token-acesso
```

### 2. Configuração no cPanel

#### 2.1 Criar Banco MySQL
1. Acesse **cPanel > MySQL Databases**
2. Crie novo banco: `seuusuario_indiaoasis`
3. Crie usuário MySQL com senha forte
4. Associe usuário ao banco com todos os privilégios
5. Anote credenciais para o arquivo `.env`

#### 2.2 Configurar Email
1. Acesse **cPanel > Email Accounts**
2. Crie conta: `noreply@seudominio.com`
3. Crie conta: `admin@seudominio.com`
4. Anote credenciais para o arquivo `.env`

#### 2.3 Upload dos Arquivos
**Via File Manager (Recomendado):**
1. Acesse **cPanel > File Manager**
2. Vá para `public_html/` (ou subdiretório se desejar)
3. Crie pasta `indiaoasis/`
4. Upload todos os arquivos do projeto
5. Extrair se uploaded como ZIP

**Via FTP:**
```bash
# Upload via FTP client (FileZilla, etc.)
# Servidor: ftp.seudominio.com
# Usuário: seu_usuario_cpanel
# Upload para: public_html/indiaoasis/
```

### 3. Configuração da Aplicação Python

#### 3.1 Setup Python App
1. Acesse **cPanel > Setup Python App**
2. Clique **Create Application**
3. Configure:
   - **Python version**: 3.11 (ou mais recente disponível)
   - **Application root**: `indiaoasis`
   - **Application URL**: `/` (ou subdiretório desejado)
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`

#### 3.2 Instalar Dependências
1. Após criar a aplicação, note o comando para ativar virtualenv
2. Acesse **cPanel > Terminal** (ou SSH)
3. Execute:

```bash
# Ativar ambiente virtual (comando exibido no cPanel)
source /home/seuusuario/virtualenv/indiaoasis/3.11/bin/activate

# Navegar para aplicação
cd ~/indiaoasis

# Instalar dependências
pip install -r requirements-cpanel.txt

# Criar diretórios necessários
mkdir -p logs cache media static

# Definir permissões
chmod 755 logs cache media
```

### 4. Configuração do Banco de Dados

#### 4.1 Executar Migração
```bash
# No terminal cPanel, com virtualenv ativo
cd ~/indiaoasis

# Executar script de migração MySQL
python scripts/migrate_to_mysql.py

# OU manualmente:
python manage.py makemigrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput
```

### 5. Configuração de Arquivos Estáticos

#### 5.1 Configurar .htaccess
Crie/edite `.htaccess` em `public_html/`:

```apache
# India Oasis - cPanel Configuration
RewriteEngine On

# Handle static files
RewriteRule ^static/(.*)$ /indiaoasis/public_html/static/$1 [L]
RewriteRule ^media/(.*)$ /indiaoasis/public_html/media/$1 [L]

# Python application
RewriteCond %{REQUEST_URI} !^/static/
RewriteCond %{REQUEST_URI} !^/media/
PassengerAppRoot "/home/seuusuario/indiaoasis"
PassengerBaseURI "/"
PassengerPython "/home/seuusuario/virtualenv/indiaoasis/3.11/bin/python"
PassengerAppLogFile "/home/seuusuario/indiaoasis/logs/passenger.log"
```

### 6. Configuração SSL (Opcional)

#### 6.1 Habilitar SSL
1. **cPanel > SSL/TLS**
2. **Let's Encrypt** (gratuito) ou upload de certificado
3. Habilitar **Force HTTPS Redirect**
4. Atualizar `.env`:
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### 7. Testes e Verificação

#### 7.1 Verificar Funcionamento
```bash
# Testar aplicação
curl -I https://seudominio.com

# Verificar logs
tail -f ~/indiaoasis/logs/django.log
tail -f ~/indiaoasis/logs/passenger.log
```

#### 7.2 Checklist de Testes
- [ ] Site carrega na URL principal
- [ ] Admin acessível em `/admin/`
- [ ] Login de usuário funciona
- [ ] Imagens carregam corretamente
- [ ] Formulários funcionam (contato, etc.)
- [ ] Carrinho de compras funciona
- [ ] Processo de checkout (teste)
- [ ] Emails são enviados

## 🔧 Manutenção e Troubleshooting

### Comandos Úteis

```bash
# Ativar ambiente virtual
source /home/seuusuario/virtualenv/indiaoasis/3.11/bin/activate

# Navegar para aplicação
cd ~/indiaoasis

# Ver logs
tail -f logs/django.log
tail -f logs/passenger.log

# Reiniciar aplicação (após mudanças)
touch passenger_wsgi.py

# Backup banco de dados
mysqldump -u seu_usuario -p seu_banco > backup_$(date +%Y%m%d).sql

# Executar comandos Django
python manage.py shell
python manage.py dbshell
python manage.py collectstatic --noinput
```

### Problemas Comuns

#### 1. Erro 500 - Internal Server Error
```bash
# Verificar logs
tail -20 logs/django.log
tail -20 logs/passenger.log

# Verificar permissões
ls -la logs/
chmod 755 logs/

# Reiniciar aplicação
touch passenger_wsgi.py
```

#### 2. Arquivos Estáticos Não Carregam
```bash
# Recoletar arquivos estáticos
python manage.py collectstatic --noinput

# Verificar .htaccess
cat .htaccess

# Verificar permissões
ls -la public_html/static/
```

#### 3. Erro de Conexão com Banco
```bash
# Testar conexão MySQL
mysql -u seu_usuario -p -h localhost seu_banco

# Verificar configurações
python manage.py dbshell

# Verificar .env
cat .env | grep DB_
```

#### 4. Aplicação Não Inicia
```bash
# Verificar passenger_wsgi.py
python passenger_wsgi.py

# Verificar requirements
pip list | grep Django

# Reinstalar dependências
pip install -r requirements-cpanel.txt --force-reinstall
```

### Logs Importantes

- **Django**: `~/indiaoasis/logs/django.log`
- **Passenger**: `~/indiaoasis/logs/passenger.log`
- **MySQL**: `/var/log/mysql/error.log` (se acessível)
- **Apache**: `/var/log/apache2/error.log` (se acessível)

## 🔄 Atualizações e Backup

### Backup Automático
```bash
# Criar script de backup
cat > ~/backup_indiaoasis.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups

mkdir -p $BACKUP_DIR

# Backup banco de dados
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/db_$DATE.sql

# Backup arquivos media
tar -czf $BACKUP_DIR/media_$DATE.tar.gz ~/indiaoasis/media/

# Limpar backups antigos (>7 dias)
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
EOF

chmod +x ~/backup_indiaoasis.sh

# Agendar no cron (cPanel > Cron Jobs)
# Diário às 2h: 0 2 * * * /home/seuusuario/backup_indiaoasis.sh
```

### Atualização da Aplicação
```bash
# Backup antes da atualização
~/backup_indiaoasis.sh

# Upload novos arquivos
# Atualizar dependências se necessário
pip install -r requirements-cpanel.txt

# Executar migrações
python manage.py migrate

# Coletar novos arquivos estáticos
python manage.py collectstatic --noinput

# Reiniciar aplicação
touch passenger_wsgi.py
```

## 📊 Otimização de Performance

### Configurações MySQL
```sql
-- Otimizações para o banco (via phpMyAdmin)
SET GLOBAL innodb_buffer_pool_size = 128M;
SET GLOBAL innodb_log_file_size = 64M;
SET GLOBAL max_connections = 100;
```

### Configurações Django
```python
# No settings_cpanel.py (já configurado)
# Cache baseado em arquivos
# Sessões otimizadas
# Logs controlados
```

### Limpeza Periódica
```bash
# Limpar cache
rm -rf ~/indiaoasis/cache/*

# Limpar logs antigos
find ~/indiaoasis/logs -name "*.log" -mtime +30 -delete

# Otimizar banco MySQL
mysqlcheck -u $DB_USER -p$DB_PASSWORD --optimize --all-databases
```

## 🚨 Limitações da Versão cPanel

### Funcionalidades Removidas
- ❌ **Redis**: Cache agora é baseado em arquivos
- ❌ **Celery**: Processamento em background removido
- ❌ **PostgreSQL**: Migrado para MySQL
- ❌ **Docker**: Execução nativa
- ❌ **Gunicorn**: Usa mod_wsgi/Passenger

### Funcionalidades Mantidas
- ✅ **E-commerce completo**: Produtos, carrinho, checkout
- ✅ **MercadoPago**: Pagamentos funcionando
- ✅ **Admin Django**: Interface administrativa
- ✅ **Email**: Notificações de pedidos
- ✅ **Upload de imagens**: Produtos e categorias
- ✅ **Responsivo**: Interface mobile-friendly

## 📞 Suporte

### Recursos Úteis
- **cPanel Documentation**: https://docs.cpanel.net/
- **Django Documentation**: https://docs.djangoproject.com/
- **GoDaddy Help**: https://godaddy.com/help

### Checklist Pós-Deploy
- [ ] Site acessível via HTTPS
- [ ] Admin funcionando (/admin/)
- [ ] Banco de dados conectado
- [ ] Emails sendo enviados
- [ ] Backup configurado
- [ ] SSL ativo (se desejado)
- [ ] MercadoPago testado
- [ ] Performance adequada

---

**🎉 Parabéns! Seu e-commerce India Oasis está online no cPanel!**

Para suporte, consulte os logs da aplicação ou a documentação oficial do Django e cPanel.