# India Oasis - Guia de Deploy para Hostinger VPS

Este guia fornece instruções completas para fazer o deploy do e-commerce India Oasis em um VPS da Hostinger.

## 📋 Pré-requisitos

### Recursos Mínimos Recomendados
- **VPS Plan**: KVM 4 (4 vCPU, 16GB RAM, 200GB NVMe) - **RECOMENDADO**
- **Mínimo**: KVM 2 (2 vCPU, 8GB RAM, 100GB NVMe)
- **Sistema**: Ubuntu 20.04 LTS ou superior
- **Domínio**: Configurado e apontando para o IP do VPS

### Conhecimentos Necessários
- Acesso SSH ao servidor
- Conceitos básicos de Docker
- Configuração de DNS
- Noções de administração Linux

## 🚀 Instalação Rápida

### 1. Configuração Inicial do Servidor

Execute como root no seu VPS:

```bash
# Baixar e executar script de setup
curl -sSL https://raw.githubusercontent.com/your-repo/india-oasis/main/scripts/setup.sh | sudo bash
```

**OU faça a instalação manual:**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Criar usuário de deploy
sudo useradd -m -s /bin/bash django
sudo usermod -aG docker django
sudo usermod -aG sudo django
```

### 2. Preparar o Projeto

```bash
# Mudar para usuário django
sudo su - django

# Clonar repositório
git clone https://github.com/your-repo/india-oasis.git /opt/india_oasis
cd /opt/india_oasis

# Dar permissões aos scripts
chmod +x scripts/*.sh
```

### 3. Configurar Variáveis de Ambiente

Crie o arquivo `.env`:

```bash
cp .env.example .env
nano .env
```

**Configurações obrigatórias:**

```env
# Django Settings
SECRET_KEY=your-very-secret-key-here-min-50-chars
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,IP_DO_VPS

# Database
POSTGRES_DB=india_oasis
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong-database-password

# Redis
REDIS_PASSWORD=strong-redis-password

# MercadoPago (obrigatório)
MERCADO_PAGO_PUBLIC_KEY=APP_USR-your-public-key
MERCADO_PAGO_ACCESS_TOKEN=APP_USR-your-access-token
MERCADO_PAGO_WEBHOOK_SECRET=your-webhook-secret

# Email (obrigatório)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com
ORDER_EMAIL_ADMIN=admin@your-domain.com

# Melhor Envio (opcional)
MELHOR_ENVIO_TOKEN=your-melhor-envio-token
MELHOR_ENVIO_CEP_ORIGEM=01034-001

# Monitoring (opcional)
SENTRY_DSN=https://your-sentry-dsn.ingest.sentry.io/project-id
```

### 4. Deploy da Aplicação

```bash
# Executar deploy
./scripts/deploy.sh production
```

### 5. Configurar SSL (HTTPS)

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obter certificado SSL
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

## 🔧 Configuração Manual Detalhada

### Estrutura de Diretórios

```
/opt/india_oasis/
├── docker-compose.prod.yml
├── Dockerfile
├── .env
├── nginx/
│   ├── nginx.conf
│   └── proxy_params
├── scripts/
│   ├── deploy.sh
│   └── setup.sh
├── logs/
├── media/
├── staticfiles/
├── backups/
└── ssl/
```

### Comandos Úteis de Manutenção

```bash
# Ver status dos containers
docker-compose -f docker-compose.prod.yml ps

# Ver logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart específico
docker-compose -f docker-compose.prod.yml restart web

# Backup do banco
docker-compose -f docker-compose.prod.yml exec db pg_dump -U postgres india_oasis > backup.sql

# Acessar container Django
docker-compose -f docker-compose.prod.yml exec web bash

# Executar migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Criar superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Coletar arquivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## 🔍 Monitoramento e Logs

### Localização dos Logs

- **Aplicação**: `/opt/india_oasis/logs/`
- **Nginx**: `/var/log/nginx/`
- **Sistema**: `/var/log/syslog`

### Verificação de Saúde

```bash
# Health check da aplicação
curl http://your-domain.com/health/

# Status dos containers
docker-compose -f docker-compose.prod.yml ps

# Uso de recursos
docker stats

# Espaço em disco
df -h

# Uso de memória
free -h
```

## 🔒 Segurança

### Configurações Essenciais

1. **Firewall (UFW)**:
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
```

2. **Fail2Ban**:
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

3. **Atualizações Automáticas**:
```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

### Backup Automatizado

Adicione ao crontab do usuário django:

```bash
crontab -e

# Backup diário às 2h da manhã
0 2 * * * /opt/india_oasis/scripts/backup.sh

# Limpeza de logs antigos (semanal)
0 3 * * 0 find /opt/india_oasis/logs -name "*.log" -mtime +30 -delete
```

## 🚨 Troubleshooting

### Problemas Comuns

**1. Container não inicia:**
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs web

# Verificar configuração
docker-compose -f docker-compose.prod.yml config
```

**2. Erro de conexão com banco:**
```bash
# Verificar se PostgreSQL está rodando
docker-compose -f docker-compose.prod.yml ps db

# Testar conexão
docker-compose -f docker-compose.prod.yml exec db pg_isready -U postgres
```

**3. Arquivos estáticos não carregam:**
```bash
# Recoletar arquivos estáticos
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Verificar permissões
ls -la staticfiles/
```

**4. SSL não funciona:**
```bash
# Verificar certificados
sudo certbot certificates

# Testar configuração nginx
sudo nginx -t

# Recarregar nginx
sudo systemctl reload nginx
```

### Restauração de Backup

```bash
# Parar aplicação
docker-compose -f docker-compose.prod.yml down

# Restaurar banco de dados
docker-compose -f docker-compose.prod.yml up -d db
docker-compose -f docker-compose.prod.yml exec -T db psql -U postgres -d india_oasis < backup.sql

# Restaurar arquivos
tar -xzf media_backup.tar.gz
tar -xzf static_backup.tar.gz

# Reiniciar aplicação
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Otimização de Performance

### Para VPS KVM 2 (8GB RAM)
```yaml
# docker-compose.prod.yml - ajustar recursos
services:
  web:
    deploy:
      resources:
        limits:
          memory: 512M
  worker:
    deploy:
      resources:
        limits:
          memory: 256M
```

### Para VPS KVM 4 (16GB RAM)
```yaml
# Configuração padrão já otimizada
# Pode aumentar workers do Gunicorn se necessário
```

## 📞 Suporte

### Recursos Úteis

- **Documentação Django**: https://docs.djangoproject.com/
- **Docker Docs**: https://docs.docker.com/
- **Hostinger Help**: https://support.hostinger.com/

### Monitoramento Recomendado

- **Uptime**: UptimeRobot ou similar
- **Logs**: Sentry.io para erros da aplicação
- **Performance**: New Relic ou DataDog
- **Backup**: Estratégia 3-2-1 (3 cópias, 2 mídias, 1 offsite)

## ✅ Checklist Pós-Deploy

- [ ] Aplicação acessível via HTTP/HTTPS
- [ ] SSL funcionando corretamente
- [ ] Admin panel acessível (/admin/)
- [ ] Health check respondendo (/health/)
- [ ] Backup automatizado configurado
- [ ] Monitoramento ativo
- [ ] DNS configurado corretamente
- [ ] Emails sendo enviados
- [ ] Pagamentos funcionando (modo teste)
- [ ] Firewall configurado
- [ ] Logs rotacionando corretamente

---

**🎉 Parabéns! Seu e-commerce India Oasis está online!**

Para suporte adicional, consulte os logs da aplicação ou entre em contato com a equipe de desenvolvimento.