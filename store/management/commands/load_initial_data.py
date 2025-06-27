from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from store.models import Category, Product
from django.utils.text import slugify
import random
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Carrega dados iniciais para o e-commerce'

    def handle(self, *args, **kwargs):
        self.stdout.write('Carregando dados iniciais...')

        # Criar um superusuário se não existir
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@indiaoasis.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superusuário admin criado!'))

        # Criar categorias
        categories = [
            {
                'name': 'Temperos',
                'description': 'Temperos autênticos da Índia para dar sabor às suas receitas.'
            },
            {
                'name': 'Grãos',
                'description': 'Grãos importados diretamente da Índia.'
            },
            {
                'name': 'Especiarias',
                'description': 'Especiarias aromáticas para dar um toque especial à sua comida.'
            },
            {
                'name': 'Chás',
                'description': 'Chás tradicionais indianos com aromas e sabores únicos.'
            },
            {
                'name': 'Curry',
                'description': 'Diferentes tipos de curry para seus pratos indianos.'
            },
        ]

        created_categories = []
        for category_data in categories:
            category, created = Category.objects.get_or_create(
                name=category_data['name'],
                defaults={
                    'slug': slugify(category_data['name']),
                    'description': category_data['description']
                }
            )
            created_categories.append(category)
            if created:
                self.stdout.write(f'Categoria {category.name} criada!')
            else:
                self.stdout.write(f'Categoria {category.name} já existe!')

        # Criar produtos
        products = [
            {
                'name': 'Curry Garam Masala',
                'category': 'Curry',
                'description': 'Mistura de especiarias aromáticas, incluindo canela, cardamomo, cravo, cominho e outros. Ideal para carnes, legumes e pratos de arroz.',
                'price': 19.90,
                'stock': 50
            },
            {
                'name': 'Curry Madras',
                'category': 'Curry',
                'description': 'Tempero picante originário do sul da Índia. Combina pimenta, cominho, coentro, açafrão e outras especiarias.',
                'price': 22.50,
                'stock': 40
            },
            {
                'name': 'Sementes de Cominho',
                'category': 'Especiarias',
                'description': 'Sementes aromáticas com sabor amargo e doce. Usadas em currys, sopas e molhos.',
                'price': 12.90,
                'stock': 60
            },
            {
                'name': 'Sementes de Mostarda Preta',
                'category': 'Especiarias',
                'description': 'Sementes picantes usadas para dar sabor a muitos pratos indianos. São torradas em óleo antes de adicionar outros ingredientes.',
                'price': 15.40,
                'stock': 45
            },
            {
                'name': 'Cardamomo Verde',
                'category': 'Especiarias',
                'description': 'Especiaria aromática com notas cítricas e mentoladas. Usada em pratos doces e salgados, além de chás.',
                'price': 28.90,
                'stock': 30
            },
            {
                'name': 'Açafrão em Pó',
                'category': 'Temperos',
                'description': 'Conhecido por sua cor amarela vibrante, o açafrão é anti-inflamatório e usado em diversos pratos indianos.',
                'price': 14.90,
                'stock': 55
            },
            {
                'name': 'Pimenta Caiena',
                'category': 'Temperos',
                'description': 'Pimenta picante usada para adicionar calor aos pratos. Indispensável na culinária indiana.',
                'price': 11.50,
                'stock': 65
            },
            {
                'name': 'Coentro em Pó',
                'category': 'Temperos',
                'description': 'Tempero feito de sementes de coentro moídas. Adiciona um sabor citrico e terroso aos pratos.',
                'price': 13.90,
                'stock': 70
            },
            {
                'name': 'Arroz Basmati',
                'category': 'Grãos',
                'description': 'Arroz de grão longo com aroma característico. Perfeito para acompanhar currys e outros pratos indianos.',
                'price': 25.90,
                'stock': 80
            },
            {
                'name': 'Lentilha Vermelha',
                'category': 'Grãos',
                'description': 'Lentilha de cozimento rápido, ideal para sopas, ensopados e o tradicional dal indiano.',
                'price': 18.50,
                'stock': 75
            },
            {
                'name': 'Grão de Bico',
                'category': 'Grãos',
                'description': 'Grão versátil usado em diversos pratos indianos, como o chana masala.',
                'price': 16.90,
                'stock': 60
            },
            {
                'name': 'Chá Masala',
                'category': 'Chás',
                'description': 'Mistura tradicional de chá preto com especiarias como cardamomo, canela, gengibre e cravo.',
                'price': 24.90,
                'stock': 40
            },
            {
                'name': 'Chá Verde com Jasmim',
                'category': 'Chás',
                'description': 'Chá verde delicado aromatizado com flores de jasmim. Refrescante e relaxante.',
                'price': 22.90,
                'stock': 35
            },
            {
                'name': 'Chá de Gengibre',
                'category': 'Chás',
                'description': 'Chá revigorante feito com gengibre fresco. Ótimo para digestão e para os dias frios.',
                'price': 19.90,
                'stock': 45
            },
        ]

        for product_data in products:
            category_name = product_data.pop('category')
            category = next((c for c in created_categories if c.name == category_name), None)

            if category:
                product, created = Product.objects.get_or_create(
                    name=product_data['name'],
                    defaults={
                        'category': category,
                        'slug': slugify(product_data['name']),
                        'description': product_data['description'],
                        'price': product_data['price'],
                        'stock': product_data['stock'],
                        'available': True,
                    }
                )

                if created:
                    self.stdout.write(f'Produto {product.name} criado!')
                else:
                    self.stdout.write(f'Produto {product.name} já existe!')

        self.stdout.write(self.style.SUCCESS('Dados iniciais carregados com sucesso!'))
