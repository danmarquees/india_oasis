# India Oasis 🛍️

[![Django](https://img.shields.io/badge/Django-5.2.3-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

E-commerce completo de produtos indianos desenvolvido em Django, otimizado para produção em VPS Hostinger.

![India Oasis Screenshot](docs/screenshot.png)

## 🌟 Funcionalidades

### 🛒 E-commerce Completo
- **Catálogo de Produtos**: Categorias, filtros, busca avançada
- **Carrinho Inteligente**: AJAX, persistência, contador dinâmico
- **Lista de Desejos**: Favoritos por usuário/sessão
- **Reviews e Avaliações**: Sistema de estrelas e comentários
- **Banners Dinâmicos**: Carrossel gerenciável pelo admin

### 💳 Pagamentos e Frete
- **Mercado Pago**: Integração completa com webhooks
- **Frete em Tempo Real**: API Melhor Envio
- **Nota Fiscal**: Estrutura pronta para Olist NFe
- **Checkout Seguro**: Processo simplificado

### 🎨 Interface Moderna
- **Design Responsivo**: Tailwind CSS
- **SPA-like**: Navegação AJAX fluida
- **Menu Lateral**: Retrátil e intuitivo
- **Notificações Toast**: Feedback visual elegante
- **Admin Customizado**: Interface amigável

### 🔧 Arquitetura Robusta
- **Django 5.2.3**: Framework moderno e seguro
- **PostgreSQL**: Banco de dados robusto
- **Redis**: Cache e message broker
- **Celery**: Tarefas assíncronas
- **Docker**: Containerização completa
- **Nginx**: Proxy reverso otimizado

## 🚀 Deploy Rápido - Hostinger VPS

### Requisitos Mínimos
- **VPS KVM 4**: 4 vCPU, 16GB RAM, 200GB NVMe (**Recomendado**)
- **VPS KVM 2**: 2 vCPU, 8GB RAM, 100GB NVMe (Mínimo)
- **Ubuntu 20.04+** com acesso root
- **Domínio** configurado

### 1. Setup Inicial (5 min)
```bash
# Conectar ao VPS via SSH
ssh root@seu-vps-ip

# Executar setup automatizado
curl -sSL https://raw.githubusercontent.com/your-repo/india-oasis/main/scripts/setup.sh | bash
```

### 2. Deploy da Aplicação (10 min)
```bash
# Mudar para usuário django
sudo su - django

# Clonar projeto
git clone https://github.com/your-repo/india-oasis.git /opt/india_oasis
cd /opt/india_oasis

# Configurar ambiente
cp .env.example .env
nano .env  # Editar configurações

# Deploy automático
./scripts/deploy.sh production
```

### 3. Configurar SSL (2 min)
```bash
# Obter certificado gratuito
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

**🎉 Pronto! Sua loja está online em https://seu-dominio.com**

## ⚙️ Configuração Detalhada

### Variáveis de Ambiente Essenciais

```env
# Django Core
SECRET_KEY=sua-chave-secreta-muito-longa-e-complexa
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com,IP_DO_VPS

# Database
POSTGRES_DB=india_oasis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=senha-forte-do-banco

# Cache/Queue
REDIS_PASSWORD=senha-forte-do-redis

# MercadoPago (Obrigatório)
MERCADO_PAGO_PUBLIC_KEY=APP_USR-sua-public-key
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-seu-access-token
MERCADO_PAGO_WEBHOOK_SECRET=seu-webhook-secret

# Email (Obrigatório)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=noreply@seu-dominio.com
ORDER_EMAIL_ADMIN=admin@seu-dominio.com

# Melhor Envio (Opcional)
MELHOR_ENVIO_TOKEN=seu-token-melhor-envio
MELHOR_ENVIO_CEP_ORIGEM=01034-001

# Monitoramento (Opcional)
SENTRY_DSN=https://seu-sentry-dsn.ingest.sentry.io/project-id
```

### Comandos de Manutenção

```bash
# Status dos serviços
docker-compose -f docker-compose.prod.yml ps

# Logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Backup do banco de dados
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres india_oasis > backup.sql

# Aplicar migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Coletar arquivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Reiniciar serviço específico
docker-compose -f docker-compose.prod.yml restart web

# Verificar saúde da aplicação
curl https://seu-dominio.com/health/
```

## 🛠️ Desenvolvimento Local

### Setup Rápido
```bash
# Clonar repositório
git clone https://github.com/your-repo/india-oasis.git
cd india_oasis

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurar ambiente de desenvolvimento
cp .env.example .env.dev
# Editar .env.dev com configurações locais

# Aplicar migrations
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Executar servidor de desenvolvimento
python manage.py runserver
```

### Tailwind CSS (Opcional)
```bash
# Instalar Node.js e dependências
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init

# Gerar CSS (modo watch)
npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/styles.css --watch
```

### Testes
```bash
# Executar todos os testes
python manage.py test

# Testes com coverage
pytest --cov=.

# Linting
flake8 .
black .
isort .
```

## 📁 Estrutura do Projeto

```
india_oasis/
├── 🐳 docker-compose.prod.yml    # Produção
├── 🐳 Dockerfile                 # Container da aplicação
├── ⚙️ .env.example              # Variáveis de ambiente
├── 📋 requirements.txt           # Dependências core
├── 📋 requirements-prod.txt      # Dependências produção
├── 📋 requirements-dev.txt       # Dependências desenvolvimento
├── 🚀 scripts/
│   ├── setup.sh                 # Setup inicial do servidor
│   └── deploy.sh                # Deploy automatizado
├── 🌐 nginx/
│   ├── nginx.conf               # Configuração Nginx
│   └── proxy_params             # Parâmetros de proxy
├── 🏪 store/                    # App principal da loja
├── 💳 payment_processing/       # Integração pagamentos
├── 📧 email_service/            # Serviço de emails
├── 🎨 templates/                # Templates Django
├── 📁 static/                   # Arquivos estáticos
├── 📱 media/                    # Uploads de usuários
├── 📊 logs/                     # Logs da aplicação
└── 💾 backups/                  # Backups automáticos
```

## 🔧 Integrações

### MercadoPago
- ✅ Checkout transparente
- ✅ Webhooks para confirmação
- ✅ Painel administrativo
- ✅ Modo sandbox/produção

### Melhor Envio
- ✅ Cálculo de frete em tempo real
- ✅ Múltiplas transportadoras
- ✅ Rastreamento de pedidos

### Olist NFe
- ✅ Estrutura pronta para integração
- ✅ Emissão automática de notas fiscais
- 🔧 Configuração via admin

## 📊 Monitoramento

### Health Checks
- **Aplicação**: `/health/` - Status geral
- **Database**: Conectividade PostgreSQL
- **Cache**: Conectividade Redis
- **Disk**: Uso de armazenamento
- **Memory**: Uso de memória

### Logs Estruturados
- **Aplicação**: `/opt/india_oasis/logs/india_oasis.log`
- **Pagamentos**: `/opt/india_oasis/logs/payments.log`
- **Errors**: `/opt/india_oasis/logs/errors.log`
- **Nginx**: `/var/log/nginx/`

### Métricas Recomendadas
- **Uptime**: UptimeRobot
- **Errors**: Sentry.io
- **Performance**: New Relic
- **Security**: Fail2Ban + UFW

## 🔒 Segurança

### Recursos de Segurança
- ✅ HTTPS obrigatório (SSL/TLS)
- ✅ Headers de segurança (HSTS, CSP)
- ✅ Rate limiting por IP
- ✅ Proteção CSRF/XSS
- ✅ Validação de uploads
- ✅ Firewall configurado
- ✅ Fail2Ban ativo
- ✅ Usuário não-root

### Backup Automatizado
- 📅 **Diário**: Banco de dados
- 📅 **Semanal**: Arquivos de media
- 📅 **Mensal**: Backup completo
- 🔄 **Retenção**: 30 dias locais + cloud

## 🚨 Troubleshooting

### Problemas Comuns

**❌ Containers não iniciam**
```bash
docker-compose -f docker-compose.prod.yml logs
docker-compose -f docker-compose.prod.yml config
```

**❌ Erro de conexão com banco**
```bash
docker-compose -f docker-compose.prod.yml ps db
docker-compose -f docker-compose.prod.yml exec db pg_isready -U postgres
```

**❌ SSL não funciona**
```bash
sudo certbot certificates
sudo nginx -t
sudo systemctl reload nginx
```

**❌ Pagamentos não processam**
- Verificar credenciais MercadoPago
- Checar webhook configurado
- Analisar logs: `tail -f logs/payments.log`

## 🎯 Performance

### Otimizações Implementadas
- 🚀 **Cache Redis**: Páginas e consultas
- 🚀 **CDN Ready**: Arquivos estáticos
- 🚀 **Gzip/Brotli**: Compressão automática
- 🚀 **Image Optimization**: Pillow + WebP
- 🚀 **DB Indexing**: Consultas otimizadas
- 🚀 **Lazy Loading**: Templates otimizados

### Métricas de Performance
- **First Paint**: < 1.5s
- **Time to Interactive**: < 3s
- **Lighthouse Score**: 90+
- **Core Web Vitals**: Aprovado

## 🤝 Contribuição

### Como Contribuir
1. Fork o projeto
2. Crie uma branch: `git checkout -b feature/nova-funcionalidade`
3. Commit suas mudanças: `git commit -m 'Add nova funcionalidade'`
4. Push para a branch: `git push origin feature/nova-funcionalidade`
5. Abra um Pull Request

### Padrões de Código
- **Python**: PEP 8 + Black
- **JavaScript**: ESLint + Prettier
- **CSS**: BEM methodology
- **Git**: Conventional Commits

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🏆 Créditos

Desenvolvido com ❤️ para o mercado brasileiro de produtos indianos.

### Tecnologias Utilizadas
- [Django](https://djangoproject.com/) - Framework web
- [PostgreSQL](https://postgresql.org/) - Banco de dados
- [Redis](https://redis.io/) - Cache e message broker
- [Celery](https://celeryproject.org/) - Task queue
- [Docker](https://docker.com/) - Containerização
- [Nginx](https://nginx.org/) - Servidor web
- [Tailwind CSS](https://tailwindcss.com/) - Framework CSS

### APIs Integradas
- [MercadoPago](https://mercadopago.com.br/) - Gateway de pagamento
- [Melhor Envio](https://melhorenvio.com.br/) - Cálculo de frete
- [Olist](https://olist.com/) - Nota Fiscal Eletrônica

---

## 📞 Suporte

- 📖 **Documentação**: [DEPLOY.md](DEPLOY.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-repo/india-oasis/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/your-repo/india-oasis/discussions)
- 📧 **Email**: suporte@indiaoasis.com.br

**🌟 Se este projeto foi útil, deixe uma estrela no GitHub!**