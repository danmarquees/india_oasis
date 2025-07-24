from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, CustomerProfile, ContactMessage, Review, Banner
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

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'thumbnail', 'price', 'available', 'stock', 'category')
    list_filter = ('available', 'category')
    search_fields = ('name', 'description')
    actions = ['ativar_produtos', 'desativar_produtos']
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description', 'price', 'discount_price', 'sku', 'stock', 'available')
        }),
        ('Imagens do Produto', {
            'fields': ('image', 'image_1', 'image_2', 'image_3'),
        }),
        ('Detalhes Técnicos', {
            'fields': ('peso', 'origem', 'validade', 'ingredientes', 'certificacao', 'uso'),
        }),
        ('Datas', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created', 'updated')

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover; border-radius:6px;" />', obj.image.url)
        return "-"
    thumbnail.short_description = 'Imagem'

    def ativar_produtos(self, request, queryset):
        queryset.update(available=True)
    ativar_produtos.short_description = "Ativar produtos selecionados"

    def desativar_produtos(self, request, queryset):
        queryset.update(available=False)
    desativar_produtos.short_description = "Desativar produtos selecionados"

admin.site.register(Product, ProductAdmin)

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

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'ordem', 'ativo', 'thumbnail')
    list_editable = ('ordem', 'ativo')
    search_fields = ('titulo', 'subtitulo')
    list_filter = ('ativo',)
    actions = ['ativar_banners', 'desativar_banners']
    fields = ('titulo', 'subtitulo', 'imagem', 'ordem', 'ativo', 'texto_botao', 'url_botao', 'cor_texto', 'cor_fundo')

    def thumbnail(self, obj):
        if obj.imagem:
            return format_html('<img src="{}" width="80" height="40" style="object-fit:cover; border-radius:6px;" />', obj.imagem.url)
        return "-"
    thumbnail.short_description = 'Preview'

    def ativar_banners(self, request, queryset):
        queryset.update(ativo=True)
    ativar_banners.short_description = "Ativar banners selecionados"

    def desativar_banners(self, request, queryset):
        queryset.update(ativo=False)
    desativar_banners.short_description = "Desativar banners selecionados"
