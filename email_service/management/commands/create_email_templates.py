from django.core.management.base import BaseCommand
from django.db import transaction
from email_service.services import EmailTemplateService
from email_service.models import EmailTemplate

class Command(BaseCommand):
    help = 'Cria templates padrão de e-mail para o sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a recriação dos templates existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando criação de templates de e-mail...'))

        try:
            with transaction.atomic():
                # Contar templates existentes
                existing_count = EmailTemplate.objects.count()

                if existing_count > 0 and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Já existem {existing_count} templates no sistema. '
                            'Use --force para recriar todos os templates.'
                        )
                    )
                    return

                if options['force']:
                    # Deletar templates existentes
                    deleted_count = EmailTemplate.objects.all().delete()[0]
                    self.stdout.write(
                        self.style.WARNING(f'{deleted_count} templates existentes foram removidos.')
                    )

                # Criar templates padrão
                EmailTemplateService.create_default_templates()

                # Contar templates criados
                new_count = EmailTemplate.objects.count()

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ {new_count} templates criados com sucesso!'
                    )
                )

                # Listar templates criados
                self.stdout.write('\nTemplates criados:')
                for template in EmailTemplate.objects.all().order_by('email_type'):
                    status = '✓ Ativo' if template.is_active else '✗ Inativo'
                    self.stdout.write(
                        f'  • {template.name} ({template.get_email_type_display()}) - {status}'
                    )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro ao criar templates: {str(e)}')
            )
            raise
