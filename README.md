# India Oasis - E-commerce Django (cPanel Version)

Sistema de e-commerce completo desenvolvido em Django, otimizado para hospedagem cPanel da GoDaddy.

## 🛍️ Características

- **E-commerce Completo**: Catálogo de produtos, carrinho, checkout
- **Pagamentos**: Integração com MercadoPago
- **Frete**: Cálculo via API Melhor Envio
- **Responsivo**: Interface mobile-friendly
- **Admin**: Painel administrativo Django
- **Email**: Notificações automáticas de pedidos
- **SEO**: URLs amigáveis e otimizações básicas

## 🔧 Tecnologias

- **Backend**: Django 5.2.3, Python 3.11+
- **Banco**: MySQL/MariaDB (compatível cPanel)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Pagamentos**: MercadoPago API
- **Frete**: Melhor Envio API
- **Cache**: Sistema de arquivos (FileBasedCache)

## 📋 Pré-requisitos cPanel

### Hospedagem Compatível
- ✅ GoDaddy Web Hosting: Deluxe, Premium, Unlimited, Ultimate
- ❌ NÃO compatível: Economy shared hosting
- ✅ Python 3.7+ via Python Selector
- ✅ MySQL/MariaDB database
- ✅ Mínimo 2GB de armazenamento

### Conhecimentos Necessários
- Acesso ao cPanel
- Configuração de banco MySQL
- Upload de arquivos (FTP/File Manager)
- Conceitos básicos de Django

## 🚀 Instalação cPanel

### 1. Preparação
```bash
# Download do projeto
git clone https://github.com/your-repo/india-oasis-cpanel.git
cd india-oasis-cpanel

# Configurar ambiente local (opcional para testes)
cp .env.cpanel.example .env
```

### 2. Configuração no cPanel

#### 2.1 Criar Banco MySQL
1. **cPanel > MySQL Databases**
2. Criar banco: `seuusuario_indiaoasis`
3. Criar usuário MySQL
4. Associar usuário ao banco (todos privilégios)

#### 2.2 Upload dos Arquivos
1. **cPanel > File Manager**
2. Navegar para `public_html/` (ou subdiretório)
3. Criar pasta `indiaoasis/`
4. Upload de todos os arquivos do projeto

#### 2.3 Setup Python App
1. **cPanel > Setup Python App**
2. **Create Application**:
   - Python version: `3.11` (ou mais recente)
   - Application root: `indiaoasis`
   - Application URL: `/` (ou subdiretório)
   - Startup file: `passenger_wsgi.py`
   - Entry point: `application`

### 3. Configuração da Aplicação

#### 3.1 Instalar Dependências
```bash
# Terminal cPanel (ou SSH)
source /home/seuusuario/virtualenv/indiaoasis/3.11/bin/activate
cd ~/indiaoasis
pip install -r requirements.txt
```

#### 3.2 Configurar .env
```env
# Django Core
SECRET_KEY=sua-chave-secreta-muito-longa
DEBUG=False
ALLOWED_HOSTS=seudominio.com,www.seudominio.com

# MySQL Database
DB_NAME=seuusuario_indiaoasis
DB_USER=seuusuario_mysql
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

#### 3.3 Setup do Banco
```bash
# Executar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Criar diretórios necessários
mkdir -p logs cache media/products
chmod 755 logs cache media
```

### 4. Configuração Adicional

#### 4.1 Atualizar .htaccess
- Editar `.htaccess` no diretório raiz
- Descomentar linhas do Passenger
- Ajustar caminhos conforme sua estrutura

#### 4.2 SSL (Opcional)
1. **cPanel > SSL/TLS**
2. Habilitar Let's Encrypt (gratuito)
3. Atualizar `.env`:
```env
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## 🛠️ Comandos Úteis

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

# Backup banco
mysqldump -u usuario -p banco > backup_$(date +%Y%m%d).sql

# Django shell
python manage.py shell

# Executar comandos específicos
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py migrate
```

## 📊 Estrutura do Projeto

```
india_oasis/
├── manage.py                 # Django management
├── passenger_wsgi.py         # WSGI para cPanel
├── requirements.txt          # Dependências Python
├── .env.cpanel.example      # Variáveis de ambiente
├── .htaccess                # Configuração Apache
├── DEPLOY_CPANEL.md         # Guia detalhado
├── india_oasis_project/     # Configurações Django
│   ├── settings_cpanel.py   # Settings para cPanel
│   ├── urls.py             # URLs principais
│   └── wsgi.py             # WSGI padrão
├── store/                   # App e-commerce
├── payment_processing/      # Processamento pagamentos
├── email_service/          # Serviço de email
├── templates/              # Templates HTML
├── static/                 # Arquivos estáticos
├── media/                  # Uploads de usuário
├── logs/                   # Logs da aplicação
└── scripts/               # Scripts utilitários
```

## 🔍 Troubleshooting

### Problemas Comuns

#### Erro 500
```bash
# Verificar logs
tail -20 logs/django.log
tail -20 logs/passenger.log

# Reiniciar aplicação
touch passenger_wsgi.py
```

#### Arquivos estáticos não carregam
```bash
# Recoletar arquivos
python manage.py collectstatic --noinput

# Verificar permissões
ls -la static/
chmod -R 755 public_html/static/
```

#### Erro de banco
```bash
# Testar conexão
python manage.py dbshell

# Verificar configurações
python manage.py check
```

#### Aplicação não inicia
```bash
# Verificar WSGI
python passenger_wsgi.py

# Reinstalar dependências
pip install -r requirements.txt --force-reinstall
```

## 📈 Performance

### Otimizações Implementadas
- Cache baseado em arquivos
- Compressão de arquivos estáticos
- Headers de cache apropriados
- Otimização de consultas ao banco
- Logs controlados

### Recomendações
- Usar SSL sempre que possível
- Configurar backup automático
- Monitorar logs regularmente
- Otimizar imagens antes do upload
- Manter dependências atualizadas

## 🔒 Segurança

### Medidas Implementadas
- SECRET_KEY única e segura
- DEBUG=False em produção
- Headers de segurança (HTTPS, XSS, etc.)
- Proteção CSRF ativa
- Validação de entrada de dados
- Sanitização de uploads

### Recomendações Adicionais
- Backups regulares
- Senhas fortes para banco e admin
- Monitoramento de logs de erro
- Atualizações de segurança regulares

## 🆘 Suporte

### Documentação
- [Guia Completo de Deploy](DEPLOY_CPANEL.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [cPanel Documentation](https://docs.cpanel.net/)
- [GoDaddy Help](https://godaddy.com/help)

### Logs Importantes
- `logs/django.log` - Logs da aplicação
- `logs/passenger.log` - Logs do servidor
- `logs/wsgi_error.log` - Erros WSGI

### Checklist Pós-Deploy
- [ ] Site carrega corretamente
- [ ] Admin acessível (`/admin/`)
- [ ] Login funciona
- [ ] Produtos aparecem no catálogo
- [ ] Carrinho funciona
- [ ] Processo de checkout completo
- [ ] Emails são enviados
- [ ] SSL configurado (se aplicável)
- [ ] Backup configurado

## 📝 Changelog

### v1.0.0-cpanel
- ✅ Conversão completa para cPanel
- ✅ PostgreSQL → MySQL
- ✅ Redis → Cache de arquivos
- ✅ Remoção do Celery
- ✅ Passenger WSGI
- ✅ Documentação completa

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

---

**🎉 Seu e-commerce India Oasis está pronto para o cPanel da GoDaddy!**

Para suporte técnico, consulte a documentação ou entre em contato através dos logs da aplicação.