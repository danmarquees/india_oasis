from django.core.management.base import BaseCommand
from django.utils import timezone
from india_oasis.email_service.services import EmailService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    Comando de gerenciamento do Django para processar a fila de e-mails.

    Este comando busca e envia e-mails que estão na fila (EmailQueue),
    respeitando a prioridade, agendamento e tentativas de envio.
    """
    help = 'Processa a fila de e-mails pendentes no sistema.'

    def add_arguments(self, parser):
        """
        Adiciona argumentos para o comando.
        """
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='O número máximo de e-mails a serem processados em uma execução.',
        )

    def handle(self, *args, **options):
        """
        O ponto de entrada principal para o comando.
        """
        limit = options['limit']
        self.stdout.write(self.style.NOTICE(f'Iniciando processamento da fila de e-mails às {timezone.now()}...'))
        self.stdout.write(f'Limite de {limit} e-mails por execução.')

        try:
            email_service = EmailService()
            processed_count = email_service.process_email_queue(max_emails=limit)

            if processed_count > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'{processed_count} e-mail(s) processado(s) com sucesso.'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    'Nenhum e-mail para processar na fila no momento.'
                ))

        except Exception as e:
            logger.error(f"Ocorreu um erro inesperado ao processar a fila de e-mails: {e}", exc_info=True)
            self.stderr.write(self.style.ERROR(
                'Ocorreu um erro inesperado. Verifique os logs para mais detalhes.'
            ))

        self.stdout.write(self.style.NOTICE('Processamento da fila de e-mails concluído.'))
