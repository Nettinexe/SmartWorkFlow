from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa
from .models import ConfiguracaoSistema
# ==============================================================================
# 1. UTILITÁRIOS DE PERÍODO E CONFIGURAÇÃO
# ==============================================================================

def get_periodo_atual():
    """Retorna tupla (ano, trimestre) baseada na configuração ativa."""
    config = ConfiguracaoSistema.objects.first()
    if config:
        return config.ano_letivo, config.trimestre_ativo
    return 2025, '1'

def periodo_edicao_aberto():
    """Verifica se a data atual está dentro do prazo de edição."""
    config = ConfiguracaoSistema.objects.first()
    if not config or (not config.data_inicio and not config.data_fim):
        return True
    
    agora = timezone.now().date()
    if config.data_inicio and agora < config.data_inicio:
        return False
    if config.data_fim and agora > config.data_fim:
        return False
    return True

# ==============================================================================
# 2. GERAÇÃO DE PDF ( XHTML2PDF )
# ==============================================================================

def render_to_pdf(template_src, context_dict={}):
    """
    Converte um template HTML do Django em um arquivo PDF.
    """
    # 1. Carrega o template HTML
    template = get_template(template_src)
    
    # 2. Preenche o template com os dados
    html = template.render(context_dict)
    
    # 3. Cria um buffer na memória
    result = BytesIO()
    
    # 4. Converte HTML para PDF com codificação UTF-8
    # Usamos o encoding para evitar que acentos fiquem bugados
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    # 5. Retorna o Response se a geração for bem-sucedida
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        # Opcional: Força o download em vez de abrir no navegador
        # response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
        return response
    
    return None