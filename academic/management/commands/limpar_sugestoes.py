from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from academic.models import SugestaoAtividade

class Command(BaseCommand):
    help = 'Remove sugestões rejeitadas há mais de 30 dias'

    def handle(self, *args, **kwargs):
        # Calcula a data limite (Hoje - 30 dias)
        data_limite = timezone.now() - timedelta(days=30)
        
        # Busca sugestões REJEITADAS criadas ANTES dessa data
        # data_envio__lte significa "Less Than or Equal" (Menor ou igual a)
        lixo = SugestaoAtividade.objects.filter(
            status='REJEITADA',
            data_envio__lte=data_limite
        )
        
        total = lixo.count()
        
        if total > 0:
            lixo.delete()
            self.stdout.write(self.style.SUCCESS(f'LIMPEZA CONCLUÍDA: {total} sugestões antigas foram excluídas permanentemente.'))
        else:
            self.stdout.write(self.style.SUCCESS('Nenhuma sugestão antiga para excluir hoje.'))