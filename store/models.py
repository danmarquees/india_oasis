from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=20, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    endereco = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=2, blank=True)

    def __str__(self):
        return self.user.username



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.slug])

class Product(models.Model):
    # Adicionado related_name para definir explicitamente a relação inversa
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/')
    image_1 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="Preço promocional (deixe em branco se não houver desconto)")

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', args=[self.slug])

    # Estes métodos foram removidos para evitar problemas com o ORM do Django
    # As anotações serão usadas na view em vez de propriedades no modelo

class Cart(models.Model):
    # Adicionado related_name para clareza
    user = models.ForeignKey(User, related_name='carts', on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Cart {self.id}'

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    # 'related_name' já estava correto aqui, o que é ótimo!
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='cart_items', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    @property
    def total_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    STATUS_CHOICES = (
        ('awaiting_payment', 'Aguardando Pagamento'),
        ('payment_rejected', 'Pagamento Recusado'),
        ('payment_approved', 'Pagamento Aprovado'),
        ('processing', 'Em Processamento'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregue'),
        ('cancelled', 'Cancelado'),
    )

    # Adicionado related_name para clareza
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='awaiting_payment')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)

    # Novos campos para integração com Mercado Pago
    preference_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID da preferência de pagamento do Mercado Pago")
    payment_id = models.CharField(max_length=255, null=True, blank=True, help_text="ID do pagamento no Mercado Pago")

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return f'Order {self.id}'

class OrderItem(models.Model):
    # 'related_name' já estava correto aqui!
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return str(self.id)

    @property
    def total_price(self):
        return self.price * self.quantity

class Wishlist(models.Model):
    # Adicionado related_name para definir a relação inversa
    user = models.OneToOneField(User, related_name='wishlist', on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, related_name='wishlists')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Wishlist of {self.user.username}'

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=[(i, str(i)) for i in range(1, 6)], default=5)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    helpful_votes = models.ManyToManyField(User, related_name='helpful_reviews', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Review by {self.user.username} for {self.product.name} ({self.rating} stars)'

    @property
    def helpful_count(self):
        """Retorna o número de votos úteis para esta avaliação"""
        return self.helpful_votes.count()

    def mark_helpful(self, user):
        """Marca a avaliação como útil para um usuário"""
        if user != self.user:  # Impedir que o autor marque sua própria avaliação
            self.helpful_votes.add(user)

    def unmark_helpful(self, user):
        """Remove a marcação de útil para um usuário"""
        self.helpful_votes.remove(user)

    def is_marked_helpful_by(self, user):
        """Verifica se um usuário marcou esta avaliação como útil"""
        if not user.is_authenticated:
            return False
        return self.helpful_votes.filter(id=user.id).exists()

# ---- NOVO MODELO PARA MENSAGENS DE CONTATO ----
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=150)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    # Opcional: campo para indicar se o usuário quer receber newsletter
    newsletter_opt_in = models.BooleanField(default=False)

    class Meta:
        ordering = ('-sent_at',)

    def __str__(self):
        return f'Mensagem de {self.name} ({self.subject})'
