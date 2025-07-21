from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, CustomerProfile, ContactMessage, Review
from django.utils.html import format_html

@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'cpf', 'telefone', 'data_nascimento', 'genero', 'cidade', 'estado',]
    search_fields = ['user__username', 'cpf', 'telefone']

    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    full_name.short_description = 'Nome Completo'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'discount_price', 'is_on_sale', 'stock', 'is_low_stock', 'image_tag')
    search_fields = ('name', 'sku', 'description')
    list_filter = ('stock', 'discount_price', 'category')
    readonly_fields = ('image_tag', 'is_on_sale', 'is_low_stock')
    actions = ['set_promotion', 'remove_promotion']
    fieldsets = (
        ('Informações Gerais', {
            'fields': ('name', 'description', 'category', 'sku')
        }),
        ('Preços', {
            'fields': (('price', 'discount_price'), 'is_on_sale')
        }),
        ('Estoque', {
            'fields': ('stock', 'is_low_stock')
        }),
        ('Imagens', {
            'fields': ('image', 'image_1', 'image_2', 'image_3', 'image_tag')
        }),
    )

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 60px; max-height: 60px;" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Miniatura'

    def is_on_sale(self, obj):
        return bool(obj.discount_price)
    is_on_sale.boolean = True
    is_on_sale.short_description = 'Promoção?'

    def is_low_stock(self, obj):
        return obj.stock is not None and obj.stock < 5
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Estoque Baixo?'

    def set_promotion(self, request, queryset):
        queryset.update(discount_price=1)  # Exemplo: define desconto simbólico
    set_promotion.short_description = 'Ativar promoção (definir desconto simbólico)'

    def remove_promotion(self, request, queryset):
        queryset.update(discount_price=None)
    remove_promotion.short_description = 'Remover promoção'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_id', 'created']

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'first_name', 'last_name', 'email', 'address', 'postal_code', 'city', 'state', 'created', 'updated', 'status']
    list_filter = ['created', 'updated', 'status']
    inlines = [OrderItemInline]

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'created']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'sent_at', 'newsletter_opt_in']
    list_filter = ['sent_at', 'newsletter_opt_in']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'sent_at', 'newsletter_opt_in']

    def has_add_permission(self, request):
        return False

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'comment', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['comment', 'product__name', 'user__username']
    readonly_fields = ('created_at',)
