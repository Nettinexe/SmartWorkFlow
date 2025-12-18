from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    # 1. Carrega o template HTML
    template = get_template(template_src)
    
    # 2. Preenche o template com os dados (nome do aluno, texto, etc)
    html  = template.render(context_dict)
    
    # 3. Cria um arquivo na memória (BytesIO)
    result = BytesIO()
    
    # 4. A mágica da conversão
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    # 5. Se não deu erro, entrega o arquivo PDF pronto
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None