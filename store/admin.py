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
    list_display = ("name", "category", "price", "stock", "available")
    list_filter = ("available", "category")
    search_fields = ("name", "description", "sku")
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {
            'fields': ("category", "name", "slug", "description", "price", "discount_price", "sku", "stock", "available")
        }),
        ("Imagens do Produto", {
            'fields': ("image", "image_1", "image_2", "image_3"),
        }),
        ("Datas", {
            'fields': ("created", "updated"),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ("created", "updated")
    # Exibe miniaturas das imagens no admin (opcional)
    def image_tag(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height:60px;max-width:60px;" />'
        return ""
    image_tag.short_description = 'Imagem'
    image_tag.allow_tags = True

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
