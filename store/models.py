from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import re


def validate_cpf(value):
    """Validador de CPF brasileiro"""
    if not value:
        return

    # Remove caracteres não numéricos
    cpf = re.sub(r'\D', '', value)

    # Verifica se tem 11 dígitos
    if len(cpf) != 11:
        raise ValidationError('CPF deve ter 11 dígitos.')

    # Verifica se não são todos números iguais
    if cpf == cpf[0] * 11:
        raise ValidationError('CPF inválido.')

    # Validação do primeiro dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto

    if int(cpf[9]) != digito1:
        raise ValidationError('CPF inválido.')

    # Validação do segundo dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto

    if int(cpf[10]) != digito2:
        raise ValidationError('CPF inválido.')


def validate_cep(value):
    """Validador de CEP brasileiro"""
    if not value:
        return

    cep = re.sub(r'\D', '', value)
    if len(cep) != 8:
        raise ValidationError('CEP deve ter 8 dígitos.')


def validate_phone(value):
    """Validador de telefone brasileiro"""
    if not value:
        return

    phone = re.sub(r'\D', '', value)
    if len(phone) < 10 or len(phone) > 11:
        raise ValidationError('Telefone deve ter 10 ou 11 dígitos.')


class CustomerProfile(models.Model):
    """Perfil estendido do cliente com informações pessoais e endereço"""

    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outros'),
        ('N', 'Prefiro não informar'),
    ]

    STATE_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
        ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'), ('PE', 'Pernambuco'),
        ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'),
        ('TO', 'Tocantins'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Usuário'
    )

    # Informações pessoais
    cpf = models.CharField(
        'CPF',
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        validators=[validate_cpf],
        help_text='Formato: 000.000.000-00'
    )
    telefone = models.CharField(
        'Telefone',
        max_length=20,
        null=True,
        blank=True,
        validators=[validate_phone],
        help_text='Formato: (00) 00000-0000'
    )
    data_nascimento = models.DateField(
        'Data de Nascimento',
        null=True,
        blank=True
    )
    genero = models.CharField(
        'Gênero',
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )

    # Endereço
    cep = models.CharField(
        'CEP',
        max_length=9,
        blank=True,
        validators=[validate_cep],
        help_text='Formato: 00000-000'
    )
    endereco = models.CharField(
        'Endereço',
        max_length=255,
        blank=True
    )
    numero = models.CharField(
        'Número',
        max_length=20,
        blank=True
    )
    complemento = models.CharField(
        'Complemento',
        max_length=100,
        blank=True
    )
    bairro = models.CharField(
        'Bairro',
        max_length=100,
        blank=True
    )
    cidade = models.CharField(
        'Cidade',
        max_length=100,
        blank=True
    )
    estado = models.CharField(
        'Estado',
        max_length=2,
        choices=STATE_CHOICES,
        blank=True
    )

    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    is_verified = models.BooleanField('Verificado', default=False)
    marketing_consent = models.BooleanField('Aceita marketing', default=False)

    class Meta:
        verbose_name = 'Perfil do Cliente'
        verbose_name_plural = 'Perfis dos Clientes'
        indexes = [
            models.Index(fields=['cpf']),
            models.Index(fields=['telefone']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.user.username})"

    @property
    def endereco_completo(self):
        """Retorna o endereço completo formatado"""
        parts = [self.endereco]
        if self.numero:
            parts.append(f"nº {self.numero}")
        if self.complemento:
            parts.append(self.complemento)
        if self.bairro:
            parts.append(f"- {self.bairro}")
        if self.cidade and self.estado:
            parts.append(f"- {self.cidade}/{self.estado}")
        if self.cep:
            parts.append(f"CEP: {self.cep}")
        return ", ".join(filter(None, parts))

    def clean(self):
        """Validações customizadas"""
        super().clean()

        # Se informar endereço, deve informar campos obrigatórios
        if any([self.endereco, self.numero, self.bairro, self.cidade, self.cep]):
            required_fields = ['endereco', 'numero', 'bairro', 'cidade', 'estado', 'cep']
            missing_fields = []

            for field in required_fields:
                if not getattr(self, field):
                    missing_fields.append(field)

            if missing_fields:
                raise ValidationError(
                    f"Para cadastrar endereço, os seguintes campos são obrigatórios: {', '.join(missing_fields)}"
                )


class Category(models.Model):
    """Categoria de produtos"""

    name = models.CharField('Nome', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    description = models.TextField('Descrição', blank=True)
    image = models.ImageField('Imagem', upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)
    sort_order = models.PositiveIntegerField('Ordem', default=0)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name='Categoria Pai'
    )

    # SEO
    meta_title = models.CharField('Meta Title', max_length=60, blank=True)
    meta_description = models.CharField('Meta Description', max_length=160, blank=True)

    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_list_by_category', args=[self.slug])

    @property
    def product_count(self):
        """Retorna o número de produtos ativos na categoria"""
        return self.products.filter(available=True).count()


class Product(models.Model):
    """Modelo de produto com informações completas"""

    category = models.ForeignKey(
        Category,
        related_name='products',
        on_delete=models.CASCADE,
        verbose_name='Categoria'
    )
    name = models.CharField('Nome', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True)
    description = models.TextField('Descrição')
    short_description = models.CharField(
        'Descrição Curta',
        max_length=255,
        blank=True,
        help_text='Descrição breve para listagens'
    )

    # Preços
    price = models.DecimalField(
        'Preço',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    discount_price = models.DecimalField(
        'Preço Promocional',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Preço promocional (deixe em branco se não houver desconto)"
    )

    # Imagens
    image = models.ImageField('Imagem Principal', upload_to='products/')
    image_1 = models.ImageField('Imagem 2', upload_to='products/', blank=True, null=True)
    image_2 = models.ImageField('Imagem 3', upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField('Imagem 4', upload_to='products/', blank=True, null=True)

    # Estoque e disponibilidade
    sku = models.CharField('SKU', max_length=50, unique=True)
    stock = models.PositiveIntegerField('Estoque', default=0)
    available = models.BooleanField('Disponível', default=True)
    track_stock = models.BooleanField('Controlar Estoque', default=True)

    # Dimensões e peso para frete
    peso = models.DecimalField(
        'Peso (kg)',
        max_digits=5,
        decimal_places=2,
        default=0.5,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Peso do produto em kg para cálculo de frete'
    )
    altura = models.DecimalField(
        'Altura (cm)',
        max_digits=5,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(Decimal('0.1'))],
        help_text='Altura do produto em centímetros'
    )
    largura = models.DecimalField(
        'Largura (cm)',
        max_digits=5,
        decimal_places=2,
        default=15,
        validators=[MinValueValidator(Decimal('0.1'))],
        help_text='Largura do produto em centímetros'
    )
    comprimento = models.DecimalField(
        'Comprimento (cm)',
        max_digits=5,
        decimal_places=2,
        default=20,
        validators=[MinValueValidator(Decimal('0.1'))],
        help_text='Comprimento do produto em centímetros'
    )

    # Informações adicionais
    origem = models.CharField(
        'Origem',
        max_length=100,
        blank=True,
        null=True,
        help_text='Ex: Índia, Brasil, etc'
    )
    validade = models.CharField(
        'Validade',
        max_length=50,
        blank=True,
        null=True,
        help_text='Ex: 24 meses'
    )
    ingredientes = models.TextField(
        'Ingredientes',
        blank=True,
        null=True,
        help_text='Lista de ingredientes do produto'
    )
    certificacao = models.CharField(
        'Certificação',
        max_length=100,
        blank=True,
        null=True,
        help_text='Ex: 100% Natural, Sem Conservantes'
    )
    uso = models.TextField(
        'Modo de Uso',
        blank=True,
        null=True,
        help_text='Instruções de uso do produto'
    )

    # SEO
    meta_title = models.CharField('Meta Title', max_length=60, blank=True)
    meta_description = models.CharField('Meta Description', max_length=160, blank=True)

    # Flags especiais
    is_featured = models.BooleanField('Produto em Destaque', default=False)
    is_new = models.BooleanField('Produto Novo', default=False)
    is_bestseller = models.BooleanField('Mais Vendido', default=False)

    # Metadados
    created = models.DateTimeField('Criado em', auto_now_add=True)
    updated = models.DateTimeField('Atualizado em', auto_now=True)
    view_count = models.PositiveIntegerField('Visualizações', default=0)

    class Meta:
        verbose_name = 'Produto'
        verbose_name_plural = 'Produtos'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['available']),
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'available']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    @property
    def final_price(self):
        """Retorna o preço final (promocional se disponível, senão o preço normal)"""
        return self.discount_price if self.discount_price else self.price

    @property
    def discount_percentage(self):
        """Calcula a porcentagem de desconto"""
        if self.discount_price and self.price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0

    @property
    def is_in_stock(self):
        """Verifica se o produto está em estoque"""
        if not self.track_stock:
            return True
        return self.stock > 0

    @property
    def average_rating(self):
        """Retorna a média das avaliações (será calculado via annotation nas views)"""
        return getattr(self, '_average_rating', 0)

    @property
    def review_count(self):
        """Retorna o número de avaliações (será calculado via annotation nas views)"""
        return getattr(self, '_review_count', 0)

    def can_be_purchased(self, quantity=1):
        """Verifica se o produto pode ser comprado na quantidade especificada"""
        if not self.available:
            return False
        if not self.track_stock:
            return True
        return self.stock >= quantity

    def reserve_stock(self, quantity):
        """Reserva estoque do produto"""
        if self.track_stock and self.stock >= quantity:
            self.stock -= quantity
            self.save(update_fields=['stock'])
            return True
        return False

    def release_stock(self, quantity):
        """Libera estoque do produto"""
        if self.track_stock:
            self.stock += quantity
            self.save(update_fields=['stock'])

    def clean(self):
        """Validações customizadas"""
        super().clean()

        # Validar preço promocional
        if self.discount_price and self.discount_price >= self.price:
            raise ValidationError('O preço promocional deve ser menor que o preço normal.')

        # Validar dimensões
        if self.peso <= 0:
            raise ValidationError('O peso deve ser maior que zero.')


class Review(models.Model):
    """Avaliação de produto por usuário"""

    RATING_CHOICES = [
        (1, '1 Estrela'),
        (2, '2 Estrelas'),
        (3, '3 Estrelas'),
        (4, '4 Estrelas'),
        (5, '5 Estrelas'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Produto'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Usuário'
    )
    rating = models.PositiveIntegerField(
        'Avaliação',
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(
        'Título',
        max_length=100,
        blank=True,
        help_text='Título da avaliação (opcional)'
    )
    comment = models.TextField(
        'Comentário',
        blank=True,
        null=True,
        help_text='Seu comentário sobre o produto'
    )
    pros = models.TextField(
        'Pontos Positivos',
        blank=True,
        null=True,
        help_text='O que você gostou no produto'
    )
    cons = models.TextField(
        'Pontos Negativos',
        blank=True,
        null=True,
        help_text='O que poderia ser melhor'
    )
    helpful_votes = models.ManyToManyField(
        User,
        related_name='helpful_reviews',
        blank=True,
        verbose_name='Votos Úteis'
    )
    is_verified_purchase = models.BooleanField(
        'Compra Verificada',
        default=False,
        help_text='Indica se o usuário realmente comprou o produto'
    )
    is_approved = models.BooleanField(
        'Aprovado',
        default=True,
        help_text='Moderação da avaliação'
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Avaliação'
        verbose_name_plural = 'Avaliações'
        ordering = ['-created_at']
        unique_together = ['user', 'product']  # Um usuário só pode avaliar uma vez cada produto
        indexes = [
            models.Index(fields=['product', 'is_approved']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f'Avaliação de {self.user.username} para {self.product.name} ({self.rating} estrelas)'

    @property
    def helpful_count(self):
        """Retorna o número de votos úteis para esta avaliação"""
        return self.helpful_votes.count()

    def mark_helpful(self, user):
        """Marca a avaliação como útil para um usuário"""
        if user != self.user and user.is_authenticated:
            self.helpful_votes.add(user)

    def unmark_helpful(self, user):
        """Remove a marcação de útil para um usuário"""
        if user.is_authenticated:
            self.helpful_votes.remove(user)

    def is_marked_helpful_by(self, user):
        """Verifica se um usuário marcou esta avaliação como útil"""
        if not user.is_authenticated:
            return False
        return self.helpful_votes.filter(id=user.id).exists()

    @property
    def rating_stars(self):
        """Retorna uma representação em estrelas da avaliação"""
        return '★' * self.rating + '☆' * (5 - self.rating)

    def clean(self):
        """Validações customizadas"""
        super().clean()

        # Verificar se o usuário já avaliou este produto
        if Review.objects.filter(user=self.user, product=self.product).exclude(pk=self.pk).exists():
            raise ValidationError('Você já avaliou este produto.')


class ContactMessage(models.Model):
    """Mensagem de contato do site"""

    SUBJECT_CHOICES = [
        ('duvida-produto', 'Dúvida sobre produto'),
        ('pedido', 'Informações sobre pedido'),
        ('sugestao', 'Sugestão'),
        ('reclamacao', 'Reclamação'),
        ('parceria', 'Parceria comercial'),
        ('outro', 'Outro'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Baixa'),
        ('normal', 'Normal'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    name = models.CharField('Nome', max_length=100)
    email = models.EmailField('E-mail')
    phone = models.CharField(
        'Telefone',
        max_length=20,
        blank=True,
        null=True,
        validators=[validate_phone]
    )
    subject = models.CharField(
        'Assunto',
        max_length=50,
        choices=SUBJECT_CHOICES
    )
    custom_subject = models.CharField(
        'Assunto Personalizado',
        max_length=150,
        blank=True,
        help_text='Use se selecionou "Outro" no assunto'
    )
    message = models.TextField('Mensagem')
    order_number = models.CharField(
        'Número do Pedido',
        max_length=20,
        blank=True,
        null=True,
        help_text='Se relacionado a um pedido específico'
    )
    priority = models.CharField(
        'Prioridade',
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    newsletter_opt_in = models.BooleanField(
        'Aceita Newsletter',
        default=False,
        help_text='Deseja receber nossas novidades por e-mail?'
    )
    is_read = models.BooleanField('Lida', default=False)
    is_responded = models.BooleanField('Respondida', default=False)
    response = models.TextField('Resposta', blank=True, null=True)
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responded_messages',
        verbose_name='Respondido por'
    )
    responded_at = models.DateTimeField('Respondido em', null=True, blank=True)
    sent_at = models.DateTimeField('Enviado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Mensagem de Contato'
        verbose_name_plural = 'Mensagens de Contato'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['is_read']),
            models.Index(fields=['is_responded']),
            models.Index(fields=['priority']),
            models.Index(fields=['sent_at']),
        ]

    def __str__(self):
        subject_display = self.custom_subject if self.subject == 'outro' else self.get_subject_display()
        return f'Mensagem de {self.name} - {subject_display}'

    @property
    def subject_display(self):
        """Retorna o assunto apropriado"""
        if self.subject == 'outro' and self.custom_subject:
            return self.custom_subject
        return self.get_subject_display()

    def mark_as_read(self):
        """Marca a mensagem como lida"""
        self.is_read = True
        self.save(update_fields=['is_read'])

    def mark_as_responded(self, user, response):
        """Marca a mensagem como respondida"""
        from django.utils import timezone
        self.is_responded = True
        self.response = response
        self.responded_by = user
        self.responded_at = timezone.now()
        self.save(update_fields=['is_responded', 'response', 'responded_by', 'responded_at'])


class Banner(models.Model):
    """Banner promocional do site"""

    POSITION_CHOICES = [
        ('home_carousel', 'Carrossel da Home'),
        ('home_top', 'Topo da Home'),
        ('category_top', 'Topo das Categorias'),
        ('product_sidebar', 'Lateral dos Produtos'),
        ('checkout_top', 'Topo do Checkout'),
    ]

    titulo = models.CharField('Título', max_length=200)
    subtitulo = models.CharField(
        'Subtítulo',
        max_length=400,
        blank=True,
        help_text='Texto secundário do banner'
    )
    descricao = models.TextField(
        'Descrição',
        blank=True,
        help_text='Descrição completa do banner'
    )
    imagem = models.ImageField(
        'Imagem',
        upload_to='banners/',
        help_text='Imagem principal do banner'
    )
    imagem_mobile = models.ImageField(
        'Imagem Mobile',
        upload_to='banners/mobile/',
        blank=True,
        null=True,
        help_text='Versão otimizada para dispositivos móveis'
    )
    posicao = models.CharField(
        'Posição',
        max_length=20,
        choices=POSITION_CHOICES,
        default='home_carousel'
    )
    ordem = models.PositiveIntegerField(
        'Ordem',
        default=0,
        help_text='Ordem de exibição (menor número aparece primeiro)'
    )
    ativo = models.BooleanField('Ativo', default=True)

    # Botão de ação
    texto_botao = models.CharField(
        'Texto do Botão',
        max_length=100,
        blank=True,
        help_text='Texto do botão de ação (opcional)'
    )
    url_botao = models.URLField(
        'URL do Botão',
        blank=True,
        help_text='Link para onde o botão deve levar'
    )
    botao_externo = models.BooleanField(
        'Link Externo',
        default=False,
        help_text='Abrir link em nova aba'
    )

    # Estilização
    cor_texto = models.CharField(
        'Cor do Texto',
        max_length=20,
        blank=True,
        default='#FFFFFF',
        help_text='Cor do texto em hexadecimal (ex: #FFFFFF)'
    )
    cor_fundo = models.CharField(
        'Cor de Fundo',
        max_length=20,
        blank=True,
        help_text='Cor de fundo em hexadecimal (ex: #000000)'
    )
    posicao_texto = models.CharField(
        'Posição do Texto',
        max_length=20,
        choices=[
            ('left', 'Esquerda'),
            ('center', 'Centro'),
            ('right', 'Direita'),
        ],
        default='center'
    )

    # Programação
    data_inicio = models.DateTimeField(
        'Data de Início',
        null=True,
        blank=True,
        help_text='Data para começar a exibir o banner'
    )
    data_fim = models.DateTimeField(
        'Data de Fim',
        null=True,
        blank=True,
        help_text='Data para parar de exibir o banner'
    )

    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    click_count = models.PositiveIntegerField('Cliques', default=0)
    view_count = models.PositiveIntegerField('Visualizações', default=0)

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Banners'
        ordering = ['posicao', 'ordem', 'titulo']
        indexes = [
            models.Index(fields=['ativo']),
            models.Index(fields=['posicao', 'ativo']),
            models.Index(fields=['ordem']),
        ]

    def __str__(self):
        return f'{self.titulo} ({self.get_posicao_display()}) - Ordem {self.ordem}'

    @property
    def is_active_now(self):
        """Verifica se o banner está ativo no momento atual"""
        from django.utils import timezone
        now = timezone.now()

        if not self.ativo:
            return False

        if self.data_inicio and now < self.data_inicio:
            return False

        if self.data_fim and now > self.data_fim:
            return False

        return True

    def increment_views(self):
        """Incrementa o contador de visualizações"""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def increment_clicks(self):
        """Incrementa o contador de cliques"""
        self.click_count += 1
        self.save(update_fields=['click_count'])

    @property
    def click_through_rate(self):
        """Calcula a taxa de cliques (CTR)"""
        if self.view_count == 0:
            return 0
        return (self.click_count / self.view_count) * 100

    def clean(self):
        """Validações customizadas"""
        super().clean()

        # Validar datas
        if self.data_inicio and self.data_fim and self.data_inicio >= self.data_fim:
            raise ValidationError('A data de início deve ser anterior à data de fim.')

        # Validar URL do botão se texto foi informado
        if self.texto_botao and not self.url_botao:
            raise ValidationError('URL do botão é obrigatória quando há texto do botão.')


class Cart(models.Model):
    """Carrinho de compras"""

    user = models.ForeignKey(
        User,
        related_name='carts',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Usuário'
    )
    session_id = models.CharField(
        'ID da Sessão',
        max_length=100,
        null=True,
        blank=True
    )
    created = models.DateTimeField('Criado em', auto_now_add=True)
    updated = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Carrinho'
        verbose_name_plural = 'Carrinhos'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        if self.user:
            return f'Carrinho de {self.user.username}'
        return f'Carrinho {self.id} (Anônimo)'

    @property
    def total_price(self):
        """Calcula o preço total do carrinho"""
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        """Calcula o número total de itens no carrinho"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_weight(self):
        """Calcula o peso total do carrinho"""
        return sum(item.total_weight for item in self.items.all())

    def clear(self):
        """Limpa o carrinho"""
        self.items.all().delete()

    def add_item(self, product, quantity=1):
        """Adiciona um item ao carrinho"""
        if not product.can_be_purchased(quantity):
            raise ValidationError('Produto indisponível ou estoque insuficiente.')

        item, created = self.items.get_or_create(
            product=product,
            defaults={'quantity': 0}
        )

        # Verifica se a quantidade total não excede o estoque
        new_quantity = item.quantity + quantity
        if not product.can_be_purchased(new_quantity):
            raise ValidationError('Estoque insuficiente para a quantidade solicitada.')

        item.quantity = new_quantity
        item.save()
        return item


class CartItem(models.Model):
    """Item do carrinho"""

    cart = models.ForeignKey(
        Cart,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Carrinho'
    )
    product = models.ForeignKey(
        Product,
        related_name='cart_items',
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
    quantity = models.PositiveIntegerField(
        'Quantidade',
        default=1,
        validators=[MinValueValidator(1)]
    )
    created = models.DateTimeField('Criado em', auto_now_add=True)
    updated = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Item do Carrinho'
        verbose_name_plural = 'Itens do Carrinho'
        unique_together = ['cart', 'product']
        indexes = [
            models.Index(fields=['cart']),
        ]

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def unit_price(self):
        """Preço unitário do produto"""
        return self.product.final_price

    @property
    def total_price(self):
        """Preço total do item (quantidade x preço unitário)"""
        return self.unit_price * self.quantity

    @property
    def total_weight(self):
        """Peso total do item"""
        return self.product.peso * self.quantity

    def clean(self):
        """Validações do item"""
        super().clean()

        if not self.product.can_be_purchased(self.quantity):
            raise ValidationError('Quantidade indisponível para este produto.')


class Order(models.Model):
    """Pedido de compra"""

    STATUS_CHOICES = [
        ('awaiting_payment', 'Aguardando Pagamento'),
        ('payment_approved', 'Pagamento Aprovado'),
        ('payment_rejected', 'Pagamento Recusado'),
        ('processing', 'Em Processamento'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]

    # Dados do usuário
    user = models.ForeignKey(
        User,
        related_name='orders',
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )

    # Dados de entrega
    first_name = models.CharField('Nome', max_length=100)
    last_name = models.CharField('Sobrenome', max_length=100)
    email = models.EmailField('E-mail')
    phone = models.CharField('Telefone', max_length=20, blank=True)
    address = models.CharField('Endereço', max_length=250)
    number = models.CharField('Número', max_length=20)
    complement = models.CharField('Complemento', max_length=100, blank=True)
    neighborhood = models.CharField('Bairro', max_length=100)
    postal_code = models.CharField('CEP', max_length=20)
    city = models.CharField('Cidade', max_length=100)
    state = models.CharField('Estado', max_length=100)

    # Dados do pedido
    status = models.CharField(
        'Status',
        max_length=20,
        choices=STATUS_CHOICES,
        default='awaiting_payment'
    )
    total_price = models.DecimalField(
        'Valor Total',
        max_digits=10,
        decimal_places=2
    )
    shipping_cost = models.DecimalField(
        'Custo do Frete',
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    paid = models.BooleanField('Pago', default=False)

    # Integração com pagamento
    preference_id = models.CharField(
        'ID da Preferência MP',
        max_length=255,
        null=True,
        blank=True,
        help_text="ID da preferência de pagamento do Mercado Pago"
    )
    payment_id = models.CharField(
        'ID do Pagamento MP',
        max_length=255,
        null=True,
        blank=True,
        help_text="ID do pagamento no Mercado Pago"
    )

    # Nota Fiscal
    nfe_numero = models.CharField(
        "Número da NF-e",
        max_length=50,
        blank=True,
        null=True
    )
    nfe_status = models.CharField(
        "Status da NF-e",
        max_length=50,
        blank=True,
        null=True
    )
    nfe_pdf_url = models.URLField(
        "URL do PDF da NF-e",
        blank=True,
        null=True
    )
    nfe_xml_url = models.URLField(
        "URL do XML da NF-e",
        blank=True,
        null=True
    )

    # Rastreamento
    tracking_code = models.CharField(
        'Código de Rastreamento',
        max_length=100,
        blank=True,
        null=True
    )
    shipping_method = models.CharField(
        'Método de Envio',
        max_length=100,
        blank=True,
        null=True
    )

    # Metadados
    created = models.DateTimeField('Criado em', auto_now_add=True)
    updated = models.DateTimeField('Atualizado em', auto_now=True)
    notes = models.TextField('Observações', blank=True)

    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['created']),
            models.Index(fields=['payment_id']),
        ]

    def __str__(self):
        return f'Pedido #{self.id}'

    @property
    def full_name(self):
        """Nome completo do destinatário"""
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self):
        """Endereço completo formatado"""
        parts = [self.address]
        if self.number:
            parts.append(f"nº {self.number}")
        if self.complement:
            parts.append(self.complement)
        if self.neighborhood:
            parts.append(f"- {self.neighborhood}")
        if self.city and self.state:
            parts.append(f"- {self.city}/{self.state}")
        if self.postal_code:
            parts.append(f"CEP: {self.postal_code}")
        return ", ".join(filter(None, parts))

    @property
    def can_be_cancelled(self):
        """Verifica se o pedido pode ser cancelado"""
        return self.status in ['awaiting_payment', 'payment_approved']

    def cancel(self):
        """Cancela o pedido e libera o estoque"""
        if self.can_be_cancelled:
            # Liberar estoque dos produtos
            for item in self.items.all():
                item.product.release_stock(item.quantity)

            self.status = 'cancelled'
            self.save(update_fields=['status'])
            return True
        return False


class OrderItem(models.Model):
    """Item do pedido"""

    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE,
        verbose_name='Produto'
    )
    product_name = models.CharField(
        'Nome do Produto',
        max_length=200,
        help_text='Nome do produto no momento da compra'
    )
    product_sku = models.CharField(
        'SKU do Produto',
        max_length=50,
        help_text='SKU do produto no momento da compra'
    )
    price = models.DecimalField(
        'Preço Unitário',
        max_digits=10,
        decimal_places=2,
        help_text='Preço do produto no momento da compra'
    )
    quantity = models.PositiveIntegerField('Quantidade', default=1)

    class Meta:
        verbose_name = 'Item do Pedido'
        verbose_name_plural = 'Itens do Pedido'

    def __str__(self):
        return f'{self.quantity} x {self.product_name}'

    @property
    def total_price(self):
        """Preço total do item"""
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        """Salva informações do produto no momento da compra"""
        if not self.product_name:
            self.product_name = self.product.name
        if not self.product_sku:
            self.product_sku = self.product.sku
        if not self.price:
            self.price = self.product.final_price
        super().save(*args, **kwargs)


class Wishlist(models.Model):
    """Lista de desejos do usuário"""

    user = models.OneToOneField(
        User,
        related_name='wishlist',
        on_delete=models.CASCADE,
        verbose_name='Usuário'
    )
    products = models.ManyToManyField(
        Product,
        related_name='wishlists',
        verbose_name='Produtos'
    )
    created = models.DateTimeField('Criado em', auto_now_add=True)
    updated = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Lista de Desejos'
        verbose_name_plural = 'Listas de Desejos'

    def __str__(self):
        return f'Lista de desejos de {self.user.username}'

    def add_product(self, product):
        """Adiciona produto à lista de desejos"""
        self.products.add(product)
        self.save()

    def remove_product(self, product):
        """Remove produto da lista de desejos"""
        self.products.remove(product)
        self.save()

    def has_product(self, product):
        """Verifica se o produto está na lista de desejos"""
        return self.products.filter(id=product.id).exists()
