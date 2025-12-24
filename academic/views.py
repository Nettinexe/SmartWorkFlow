from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from datetime import date
import random

# Importações dos modelos e utilitários
from .models import (
    Turma, Aluno, Relatorio, Competencia, 
    Avaliacao, SugestaoAtividade, ConfiguracaoSistema
)
from .forms import TurmaForm, AlunoForm, ProfessorForm, CompetenciaForm
from .utils import get_periodo_atual, render_to_pdf

User = get_user_model()

# ==============================================================================
# 1. PAINEL PRINCIPAL (DASHBOARD)
# ==============================================================================
@login_required
def dashboard(request):
    """
    Dashboard dinâmico que alterna entre a visão operacional do Professor
    e a visão de gestão da Coordenação.
    """
    # 1. Definições de Período (Usando seu utilitário)
    ano_ativo, trimestre_ativo = get_periodo_atual()
    
    # 2. Identificação de Perfil
    # Ajuste 'ADMINISTRADOR' ou 'COORDENADOR' conforme definido no seu CustomUser
    is_professor = request.user.role == 'PROFESSOR'
    
    # Captura o trimestre da URL para filtros de histórico, ou usa o ativo por padrão
    trimestre_url = request.GET.get('tri', trimestre_ativo)

    if is_professor:
        # =====================================================================
        # LÓGICA DO PROFESSOR (JÁ REVISADA)
        # =====================================================================
        minhas_turmas = request.user.turmas.all() 
        relatorios_atuais = Relatorio.objects.filter(
            professor=request.user,
            trimestre=trimestre_url,
            ano=ano_ativo
        )

        alunos_ids = Aluno.objects.filter(turma__in=minhas_turmas).values_list('id', flat=True)
        total_alunos = len(alunos_ids)
        
        alunos_com_relatorio = relatorios_atuais.values_list('aluno_id', flat=True)
        pendentes = total_alunos - len(alunos_com_relatorio)

        iniciados = relatorios_atuais.filter(status__in=['RASCUNHO', 'CORRECAO']).count()
        qtd_enviados = relatorios_atuais.filter(status='ANALISE').count()
        qtd_correcao = relatorios_atuais.filter(status='CORRECAO').count()
        qtd_aprovados = relatorios_atuais.filter(status='APROVADO').count()

        turmas_data = []
        for turma in minhas_turmas:
            # Fallback seguro para evitar o AttributeError 'aluno_set'
            try:
                total_t = turma.alunos.count()
            except AttributeError:
                total_t = turma.aluno_set.count()

            concluidos_t = relatorios_atuais.filter(aluno__turma=turma, status__in=['APROVADO', 'ANALISE']).count()
            percent = (concluidos_t / total_t * 100) if total_t > 0 else 0
            
            turmas_data.append({
                'turma': turma,
                'total_alunos': total_t,
                'relatorios_concluidos': concluidos_t,
                'porcentagem_concluido': int(percent)
            })

        context = {
            'is_professor': True,
            'perfil_nome': 'Professor',
            'ano_ativo': ano_ativo,
            'trimestre_exibido': trimestre_url,
            'trimestre_ativo': trimestre_ativo,
            'total_alunos': total_alunos,
            'iniciados': iniciados,
            'pendentes': pendentes,
            'qtd_enviados': qtd_enviados,
            'qtd_correcao': qtd_correcao,
            'qtd_aprovados': qtd_aprovados,
            'turmas_data': turmas_data,
        }

    else:
        # =====================================================================
        # LÓGICA DO COORDENADOR (GESTÃO GLOBAL)
        # =====================================================================
        # 1. KPIs de Cabeçalho
        total_alunos_escola = Aluno.objects.count()
        total_turmas_escola = Turma.objects.count()
        
        relatorios_globais = Relatorio.objects.filter(ano=ano_ativo, trimestre=trimestre_ativo)
        
        # Quantidade de relatórios enviados pelos professores aguardando revisão
        qtd_relatorios_analise = relatorios_globais.filter(status='ANALISE').count()
        
        # Relatórios que ainda estão sendo escritos ou voltaram para correção
        relatorios_producao = relatorios_globais.filter(status__in=['RASCUNHO', 'CORRECAO']).count()

        # 2. Listas para as Abas (Tabs) do Dashboard
        # Aba: Relatórios para Aprovar
        lista_pendentes = relatorios_globais.filter(status='ANALISE').select_related('aluno', 'professor', 'aluno__turma')
        
        # Aba: Sugestões Pedagógicas para Moderar
        lista_sugestoes = SugestaoAtividade.objects.filter(status='PENDENTE').select_related('competencia', 'professor_autor')
        
        # Aba: Histórico Geral (Limitado aos últimos 50 para performance)
        historico = Relatorio.objects.filter(ano=ano_ativo).select_related('aluno', 'professor', 'aluno__turma').order_by('-id')[:50]
        
        # Aba: Banco de Ideias (Todas as aprovadas)
        banco_ideias = SugestaoAtividade.objects.all().select_related('competencia').order_by('-id')

        from .forms import TurmaForm, AlunoForm, ProfessorForm, CompetenciaForm # Certifique-se de que os nomes batem com seu forms.py

        context = {
            'is_professor': False,
            'perfil_nome': 'Coordenação/Administração',
            'ano_ativo': ano_ativo,
            'trimestre_exibido': trimestre_ativo,
            
            # Dados dos Cards
            'total_alunos': total_alunos_escola,
            'total_turmas': total_turmas_escola,
            'qtd_relatorios_pendentes': qtd_relatorios_analise,
            'relatorios_em_producao': relatorios_producao,
            
            # Listas das Tabelas
            'lista_relatorios_pendentes': lista_pendentes,
            'lista_sugestoes_pendentes': lista_sugestoes,
            'qtd_sugestoes_pendentes': lista_sugestoes.count(),
            'historico_relatorios': historico,
            'banco_sugestoes': banco_ideias,
            
            # Objetos de Formulário para os Modais
            'form_turma': TurmaForm(),
            'form_aluno': AlunoForm(),
            'form_professor': ProfessorForm(),
            'form_competencia': CompetenciaForm(),
        }

    return render(request, 'dashboard.html', context)
# ==============================================================================
# 2. DETALHES DA TURMA (COM FILTRO DE HISTÓRICO)
# ==============================================================================
@login_required
def turma_detail(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    
    # 1. Pega a configuração do sistema (O que está valendo hoje)
    ano_ativo, tri_ativo = get_periodo_atual()
    
    # 2. Verifica se o usuário pediu para ver um trimestre antigo (?tri=1)
    tri_exibido = request.GET.get('tri', tri_ativo)
    
    # Otimização: select_related evita múltiplas consultas ao carregar a turma do aluno
    alunos = Aluno.objects.filter(turma=turma).order_by('nome_completo')
    alunos_data = []
    
    codigos_materias = ['PORT', 'MAT', 'CIEN', 'HIST', 'GEO', 'ARTE', 'EDFIS', 'REL']
    
    for aluno in alunos:
        # Busca o relatório do trimestre EXIBIDO (escolhido pelo usuário)
        relatorio = Relatorio.objects.filter(
            aluno=aluno, 
            ano=ano_ativo, 
            trimestre=tri_exibido
        ).first()
        
        status = 'Não iniciado'
        progresso_percent = 0
        cor_badge = 'secondary'
        relatorio_id = None
        
        if relatorio:
            relatorio_id = relatorio.id
            
            # AJUSTE: Sincronizado status 'ANALISE' com o novo Model
            if relatorio.status in ['ANALISE', 'APROVADO']:
                status = relatorio.get_status_display()
                progresso_percent = 100
                cor_badge = 'success' if relatorio.status == 'APROVADO' else 'warning'
            elif relatorio.status == 'CORRECAO':
                status = 'Correção'
                progresso_percent = 100
                cor_badge = 'danger'
            else: 
                # Lógica de cálculo de progresso (Rascunho)
                materias_concluidas = 0
                for codigo in codigos_materias:
                    # Conta avaliações desta matéria
                    qs = Avaliacao.objects.filter(relatorio=relatorio, competencia__componente=codigo)
                    total_add = qs.count()
                    # Conta avaliações que já possuem nota
                    total_com_nota = qs.exclude(nivel__isnull=True).exclude(nivel='').count()
                    
                    # Matéria concluída se tiver pelo menos uma competência e todas tiverem nota
                    if total_add > 0 and total_add == total_com_nota:
                        materias_concluidas += 1
                
                progresso_percent = int((materias_concluidas / 8) * 100)
                
                if progresso_percent == 0:
                     status = 'Iniciado'
                     cor_badge = 'info'
                else:
                     status = f'{progresso_percent}% Concluído'
                     cor_badge = 'primary'
        else:
            # Tratamento para períodos passados sem entrega
            if tri_exibido != tri_ativo:
                 status = 'Não entregue'
                 cor_badge = 'light text-muted border'

        alunos_data.append({
            'aluno': aluno,
            'relatorio_id': relatorio_id,
            'status': status,
            'progresso': progresso_percent,
            'cor': cor_badge
        })

    return render(request, 'turma_detail.html', {
        'turma': turma,
        'alunos': alunos_data,
        'ano_atual': ano_ativo,
        'trimestre_atual': tri_exibido,
        'trimestre_sistema': tri_ativo 
    })

# ==============================================================================
# 3. TELA DE SELEÇÃO DE MATÉRIAS (Menu Principal do Professor)
# ==============================================================================
@login_required
def avaliar_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    config = ConfiguracaoSistema.objects.first()
    ano_atual = config.ano_letivo if config else 2025
    trimestre_atual = config.trimestre_ativo if config else '1'

    # 1. Identifica qual trimestre o professor quer visualizar
    trimestre_solicitado = request.GET.get('tri', trimestre_atual)
    
    # 2. Define se o período visualizado é o que está aberto para edição
    is_periodo_ativo = str(trimestre_solicitado) == str(trimestre_atual)

    # 3. Busca ou Cria o relatório
    # Se for o período ativo, garantimos que o relatório exista (get_or_create)
    if is_periodo_ativo:
        relatorio, created = Relatorio.objects.get_or_create(
            aluno=aluno,
            ano=ano_atual,
            trimestre=trimestre_atual,
            defaults={
                'professor': request.user,
                'status': 'RASCUNHO'
            }
        )
    else:
        # Se for histórico, apenas tentamos buscar. Se não existir, relatorio será None
        relatorio = Relatorio.objects.filter(
            aluno=aluno, ano=ano_atual, trimestre=trimestre_solicitado
        ).first()

    definicoes_materias = [
        ('PORT', 'Língua Portuguesa', 'bi-book'),
        ('MAT', 'Matemática', 'bi-calculator'),
        ('CIEN', 'Ciências', 'bi-virus'),
        ('HIST', 'História', 'bi-hourglass-split'),
        ('GEO', 'Geografia', 'bi-globe-americas'),
        ('ARTE', 'Arte', 'bi-palette'),
        ('EDFIS', 'Ed. Física', 'bi-bicycle'),
        ('REL', 'Ensino Religioso', 'bi-brightness-high'),
    ]
    
    lista_materias_processada = []
    
    # 4. Processamento das matérias (apenas se houver um relatório para este período)
    if relatorio:
        for codigo, nome, icone in definicoes_materias:
            avaliacoes_materia = Avaliacao.objects.filter(
                relatorio=relatorio, 
                competencia__componente=codigo
            )
            
            total_selecionadas = avaliacoes_materia.count()
            total_com_nota = avaliacoes_materia.exclude(nivel__isnull=True).exclude(nivel='').count()
            
            # Matéria concluída: tem competências E todas têm nota
            is_concluido = total_selecionadas > 0 and total_selecionadas == total_com_nota
            
            lista_materias_processada.append({
                'codigo': codigo,
                'nome': nome,
                'icone': icone,
                'concluido': is_concluido, 
                'tem_notas': total_selecionadas > 0
            })

    # 5. Lógica Final de Envio (Só permite enviar se for o período ativo E tudo estiver pronto)
    pode_enviar = False
    if is_periodo_ativo and lista_materias_processada:
        pode_enviar = all(m['concluido'] for m in lista_materias_processada)

    return render(request, 'selecionar_materia.html', {
        'aluno': aluno,
        'relatorio': relatorio,
        'materias': lista_materias_processada,
        'pode_enviar': pode_enviar,
        'is_periodo_ativo': is_periodo_ativo,  # ESSA VARIÁVEL PRECISA IR PARA O TEMPLATE
        'trimestre_atual': trimestre_solicitado,
        'trimestre_sistema': trimestre_atual
    })
# ==============================================================================
# 4. AVALIAR UMA MATÉRIA (Adicionar, Excluir e Salvar Notas)
# ==============================================================================
@login_required
def avaliar_materia(request, relatorio_id, materia_codigo):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    config = ConfiguracaoSistema.objects.first()

    trimestre_ativo = config.trimestre_ativo if config else '1'
    ano_ativo = config.ano_letivo if config else 2025

    is_periodo_ativo = (str(relatorio.trimestre) == str(trimestre_ativo) and 
                        int(relatorio.ano) == int(ano_ativo))
    
    # Trava de segurança: impede edição se não for Rascunho ou Correção
    pode_editar = relatorio.status in ['RASCUNHO', 'CORRECAO'] and is_periodo_ativo

    if request.method == 'POST':
        if not pode_editar:
            messages.error(request, "Este relatório está bloqueado para edições.")
            return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)

        # AÇÃO 1: ADICIONAR COMPETÊNCIA
        if 'btn_adicionar' in request.POST:
            termo = request.POST.get('termo_busca', '').strip()
            # Pega a série do aluno (Ex: '6' se for 6º ano)
            serie_aluno = relatorio.aluno.turma.serie_curricular
            
            try:
                # Busca a competência validando CÓDIGO, MATÉRIA e SÉRIE
                nova_comp = Competencia.objects.get(
                    codigo__iexact=termo,
                    componente=materia_codigo, # Garante que não adicione código de MAT em PORT
                )
                
                Avaliacao.objects.get_or_create(relatorio=relatorio, competencia=nova_comp)
                messages.success(request, f"Competência {nova_comp.codigo} adicionada!")
            
            except Competencia.DoesNotExist:
                messages.error(request, f"Habilidade '{termo}' não encontrada para o {serie_aluno}º ano nesta disciplina.")
            
            return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=materia_codigo)

        # AÇÃO 2: EXCLUIR COMPETÊNCIA
        elif 'btn_excluir' in request.POST:
            av_id = request.POST.get('btn_excluir')
            Avaliacao.objects.filter(id=av_id, relatorio=relatorio).delete()
            messages.success(request, "Competência removida.")
            return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=materia_codigo)

        # AÇÃO 3: SALVAR NOTAS
        elif 'btn_salvar' in request.POST:
            avaliacoes_atuais = Avaliacao.objects.filter(
                relatorio=relatorio, 
                competencia__componente=materia_codigo
            )
            
            for av in avaliacoes_atuais:
                # Captura os dados dinâmicos do template (ID da competência no nome do campo)
                nivel = request.POST.get(f'nivel_{av.competencia.id}')
                obs = request.POST.get(f'obs_{av.competencia.id}')
                
                if nivel:
                    av.nivel = nivel
                av.observacao_especifica = obs
                av.save()

            messages.success(request, "Alterações salvas com sucesso!")
            return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)

    # --- EXIBIÇÃO (GET) ---
    avaliacoes = Avaliacao.objects.filter(
        relatorio=relatorio,
        competencia__componente=materia_codigo
    ).select_related('competencia').order_by('competencia__codigo')

    return render(request, 'form_avaliacao.html', {
        'relatorio': relatorio,
        'materia_codigo': materia_codigo,
        'avaliacoes': avaliacoes,
        'pode_editar': pode_editar
    })

# ==============================================================================
# 5. CRIAR NOVA SUGESTÃO (Fluxo do Professor)
# ==============================================================================
@login_required
def sugerir_atividade(request, relatorio_id, competencia_id):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    competencia = get_object_or_404(Competencia, id=competencia_id)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        nivel_alvo = request.POST.get('nivel_alvo')
        
        if titulo and descricao and nivel_alvo:
            SugestaoAtividade.objects.create(
                titulo=titulo,
                descricao=descricao,
                nivel_alvo=nivel_alvo,
                competencia=competencia,
                professor_autor=request.user, 
                status='PENDENTE' # Sempre pendente para análise da coordenação
            )
            messages.success(request, "Obrigado! Sua sugestão foi enviada para a coordenação.")
        else:
            messages.error(request, "Erro: Todos os campos da sugestão são obrigatórios.")

    return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=competencia.componente)

@login_required
def area_coordenacao(request):
    if request.user.role == 'PROFESSOR':
        return redirect('dashboard')
    
    # Sugestões
    sugestoes_pendentes = SugestaoAtividade.objects.filter(status='AGUARDANDO')
    
    # Relatórios: Busca todos que estão AGUARDANDO aprovação
    relatorios_pendentes = Relatorio.objects.filter(status='AGUARDANDO').select_related('aluno', 'professor', 'aluno__turma')
    
    return render(request, 'area_coordenacao.html', {
        'sugestoes': sugestoes_pendentes,
        'relatorios': relatorios_pendentes
    })

# ==============================================================================
# 7. APROVAR/REJEITAR SUGESTÃO DE ATIVIDADE
# ==============================================================================
@login_required
def aprovar_sugestao(request, sugestao_id, decisao):
    # Trava de segurança para garantir que apenas gestores moderem
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Apenas coordenadores podem moderar sugestões.")
        return redirect('dashboard')

    sugestao = get_object_or_404(SugestaoAtividade, id=sugestao_id)
    
    if decisao == 'aprovada':
        sugestao.status = 'APROVADO'
        sugestao.save()
        messages.success(request, f"Sugestão '{sugestao.titulo}' aprovada com sucesso!")
        
    elif decisao == 'rejeitada':
        # Alinhado com o status do Models.py
        sugestao.status = 'REJEITADA'
        sugestao.save()
        messages.warning(request, f"Sugestão rejeitada e movida para o histórico.")
    
    base_url = reverse('dashboard')
    return redirect(f"{base_url}?tab=sugestoes")

# ==============================================================================
# 8. VISUALIZAÇÃO DO RELATÓRIO (Com Inteligência de Sugestões)
# ==============================================================================
@login_required
def visualizar_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    # Carrega avaliações com select_related para performance
    avaliacoes = Avaliacao.objects.filter(relatorio=relatorio).select_related('competencia')
    
    # Dicionário: { avaliacao_id : lista_de_sugestoes }
    sugestoes_por_avaliacao = {}
    
    for avaliacao in avaliacoes:
        # A MÁGICA: Busca sugestões que batem com a Competência E com o Nível da nota
        # Ajustado status para 'APROVADO' (conforme o Model)
        sugestoes_compativeis = list(SugestaoAtividade.objects.filter(
            competencia=avaliacao.competencia,
            nivel_alvo=avaliacao.nivel,
            status='APROVADO'
        ))
        
        # Sorteia até 2 sugestões pedagógicas para o relatório
        if sugestoes_compativeis:
            sugestoes_escolhidas = random.sample(sugestoes_compativeis, min(len(sugestoes_compativeis), 2))
            sugestoes_por_avaliacao[avaliacao.id] = sugestoes_escolhidas
            
    return render(request, 'relatorio_final.html', {
        'relatorio': relatorio,
        'avaliacoes': avaliacoes,
        'sugestoes_map': sugestoes_por_avaliacao
    })

# ==============================================================================
# 9. ENVIAR RELATÓRIO PARA A COORDENAÇÃO
# ==============================================================================
@login_required
def enviar_relatorio_final(request, relatorio_id):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    
    # 1. Permissão: Apenas o dono do relatório ou Admin
    if request.user != relatorio.professor and request.user.role != 'ADMINISTRADOR':
        messages.error(request, "Permissão negada.")
        return redirect('dashboard')

    if request.method == 'POST':
        # 2. Trava de Status: Só envia se estiver em edição
        if relatorio.status not in ['RASCUNHO', 'CORRECAO']:
             messages.error(request, "Este relatório já foi enviado ou está finalizado.")
             return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)

        # 3. Validação de Preenchimento (Não permite enviar se houver competência sem nota)
        pendencias = []
        codigos_materias = ['PORT', 'MAT', 'CIEN', 'HIST', 'GEO', 'ARTE', 'EDFIS', 'REL']
        
        for codigo in codigos_materias:
            qs_avaliacoes = Avaliacao.objects.filter(relatorio=relatorio, competencia__componente=codigo)
            
            total_adicionadas = qs_avaliacoes.count()
            total_com_nota = qs_avaliacoes.exclude(nivel__isnull=True).exclude(nivel='').count()
            
            # Se o professor listou a matéria mas não deu nota em tudo, gera erro
            if total_adicionadas > 0 and total_com_nota < total_adicionadas:
                pendencias.append(codigo)
        
        if pendencias:
            nomes_materias = {
                'PORT': 'Português', 'MAT': 'Matemática', 'CIEN': 'Ciências',
                'HIST': 'História', 'GEO': 'Geografia', 'ARTE': 'Arte',
                'EDFIS': 'Ed. Física', 'REL': 'Ensino Religioso'
            }
            lista_nomes = [nomes_materias.get(code, code) for code in pendencias]
            
            messages.error(request, f"Ação bloqueada! As seguintes matérias possuem competências sem nota: {', '.join(lista_nomes)}")
            return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)
        
        # --- FLUXO DE SUCESSO ---
        # Alterado para 'ANALISE' para manter consistência com o Dashboard e Models
        relatorio.status = 'ANALISE' 
        relatorio.save()
        
        messages.success(request, f"Sucesso! O relatório de {relatorio.aluno.nome_completo} foi enviado para análise.")
        return redirect('turma_detail', turma_id=relatorio.aluno.turma.id)

    return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)

# ==============================================================================
# 10. LIMPAR AVALIAÇÃO DE UMA MATÉRIA (RESETAR)
# ==============================================================================
@login_required
def limpar_materia(request, relatorio_id, materia_codigo):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    
    # Permissão: Apenas o professor dono do relatório ou Administrador
    if request.user != relatorio.professor and request.user.role != 'ADMINISTRADOR':
        messages.error(request, "Permissão negada.")
        return redirect('dashboard')
        
    # Trava de Segurança: Bloqueia limpeza se o relatório já foi enviado para análise ou aprovado
    if relatorio.status not in ['RASCUNHO', 'CORRECAO']:
        messages.error(request, "Não é possível limpar notas de um relatório que já está em análise ou finalizado.")
        return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)
        
    if request.method == 'POST':
        # Remove fisicamente todas as avaliações dessa matéria específica
        Avaliacao.objects.filter(
            relatorio=relatorio, 
            competencia__componente=materia_codigo
        ).delete()
        messages.success(request, f"As avaliações de {materia_codigo} foram removidas com sucesso.")
        
    return redirect('avaliar_aluno', aluno_id=relatorio.aluno.id)

# ==============================================================================
# 11. VER DETALHES DA SUGESTÃO (Moderação)
# ==============================================================================
@login_required
def detalhe_sugestao(request, sugestao_id):
    # Segurança reabilitada: Impede que professores vejam detalhes de sugestões de outros antes da aprovação
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Acesso restrito à coordenação.")
        return redirect('dashboard')
    
    sugestao = get_object_or_404(SugestaoAtividade, id=sugestao_id)
    return render(request, 'sugestao_detail.html', {
        'sugestao': sugestao
    })

# ==============================================================================
# 12. DECISÃO DO COORDENADOR (Aprovar ou Devolver Relatório)
# ==============================================================================
@login_required
def decisao_relatorio(request, relatorio_id):
    # Segurança: Apenas quem tem papel de gestão pode aprovar ou devolver
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Você não possui permissão para realizar esta ação.")
        return redirect('dashboard')

    if request.method == 'POST':
        relatorio = get_object_or_404(Relatorio, id=relatorio_id)
        acao = request.POST.get('acao') # 'aprovar' ou 'corrigir'
        
        if acao == 'aprovar':
            relatorio.status = 'APROVADO'
            # Limpa qualquer feedback anterior para manter o histórico limpo
            relatorio.feedback_coordenacao = '' 
            relatorio.save()
            messages.success(request, f"O relatório de {relatorio.aluno.nome_completo} foi APROVADO.")
            
        elif acao == 'corrigir':
            motivo = request.POST.get('motivo_devolucao')
            
            if not motivo:
                messages.error(request, "Atenção: Você precisa descrever o que deve ser corrigido.")
                return redirect('visualizar_relatorio', relatorio_id=relatorio.id)
            
            relatorio.status = 'CORRECAO'
            relatorio.feedback_coordenacao = motivo
            relatorio.save()
            messages.warning(request, f"Relatório devolvido para o professor. Motivo: {motivo}")

    return redirect('dashboard')

# ==============================================================================
# 13. CONFIGURAÇÕES DO SISTEMA (Coordenação)
# ==============================================================================
@login_required
def configuracoes_sistema(request):
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Acesso restrito.")
        return redirect('dashboard')
    
    # Busca a única instância de configuração ou cria a primeira (id=1)
    config, created = ConfiguracaoSistema.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        try:
            config.ano_letivo = request.POST.get('ano_letivo')
            config.trimestre_ativo = request.POST.get('trimestre_ativo')
            
            # Tratamento de data de fechamento para evitar erro de formato
            data_fim = request.POST.get('data_fim')
            config.data_fim = data_fim if data_fim else None
                
            config.save()
            messages.success(request, "As configurações globais do sistema foram atualizadas.")
        except Exception as e:
            messages.error(request, f"Erro ao salvar configurações: {e}")
        
        return redirect('configuracoes_sistema')

    return render(request, 'configuracoes.html', {'config': config})

# ==============================================================================
# 10. PAINEL DE GESTÃO ESCOLAR (Visão Geral)
# ==============================================================================
@login_required
def gestao_escolar(request):
    # Trava de segurança para garantir que apenas gestores acessem
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Acesso restrito.")
        return redirect('dashboard')
    
    # Buscas otimizadas com select_related e order_by
    turmas = Turma.objects.all().order_by('nome')
    alunos = Aluno.objects.all().select_related('turma').order_by('nome_completo')
    
    # Busca apenas usuários com papel de PROFESSOR
    User = get_user_model()
    professores = User.objects.filter(role='PROFESSOR').order_by('first_name')
    
    # Instancia formulários vazios para os modais de criação
    return render(request, 'gestao_escolar.html', {
        'turmas': turmas,
        'alunos': alunos,
        'professores': professores,
        'form_turma': TurmaForm(),
        'form_aluno': AlunoForm(),
        'form_professor': ProfessorForm()
    })

# ==============================================================================
# 11. CRUD DE TURMAS
# ==============================================================================
@login_required
def salvar_turma(request, turma_id=None):
    turma = get_object_or_404(Turma, id=turma_id) if turma_id else None
    
    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            msg = "Turma atualizada com sucesso!" if turma_id else "Nova turma cadastrada!"
            messages.success(request, msg)
        else:
            messages.error(request, "Erro ao salvar turma. Verifique se os dados estão corretos.")
            
    return redirect('gestao_escolar')

@login_required
def excluir_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    # Tenta excluir, mas o banco impede via CASCADE/PROTECT se houver dependências
    try:
        if turma.alunos.exists():
            messages.error(request, f"Não é possível excluir a turma {turma.nome} pois ela possui alunos matriculados.")
        else:
            turma.delete()
            messages.success(request, "Turma removida com sucesso.")
    except Exception:
        messages.error(request, "Erro técnico ao tentar excluir a turma.")
        
    return redirect('gestao_escolar')

# ==============================================================================
# 12. CRUD DE ALUNOS
# ==============================================================================
@login_required
def salvar_aluno(request, aluno_id=None):
    aluno = get_object_or_404(Aluno, id=aluno_id) if aluno_id else None
    
    if request.method == 'POST':
        form = AlunoForm(request.POST, instance=aluno)
        if form.is_valid():
            form.save()
            msg = "Dados do aluno atualizados!" if aluno_id else "Aluno matriculado com sucesso!"
            messages.success(request, msg)
        else:
            messages.error(request, "Erro ao processar matrícula. Verifique os campos.")
            
    return redirect('gestao_escolar')

@login_required
def excluir_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    # Verifica se existem relatórios antes de apagar (Integridade Pedagógica)
    if aluno.relatorio_set.exists():
        messages.warning(request, "Este aluno possui relatórios no sistema e não pode ser excluído para preservar o histórico.")
    else:
        aluno.delete()
        messages.success(request, "Registro do aluno removido.")
        
    return redirect('gestao_escolar')

# ==============================================================================
# 13. CRUD DE PROFESSORES (Gestão de Usuários e Vínculos)
# ==============================================================================
@login_required
def salvar_professor(request, professor_id=None):
    User = get_user_model()
    professor = get_object_or_404(User, id=professor_id) if professor_id else None
    
    if request.method == 'POST':
        form = ProfessorForm(request.POST, instance=professor)
        if form.is_valid():
            # Salva o usuário sem persistir no banco ainda (commit=False)
            user = form.save(commit=False)
            
            if not professor_id:
                user.set_password('123456') # Senha padrão para novos cadastros
                user.role = 'PROFESSOR'
            
            user.save() # Salva o usuário
            
            # Atualiza a relação Many-to-Many de Turmas de forma limpa
            # O Django gerencia a tabela intermediária automaticamente com .set()
            turmas = form.cleaned_data.get('turmas')
            user.turmas.set(turmas)

            msg = "Vínculos do professor atualizados!" if professor_id else "Professor cadastrado com acesso ao sistema!"
            messages.success(request, msg)
        else:
            # Erro comum: username (login) já existente
            messages.error(request, "Erro ao salvar. Certifique-se que o login é único e os campos estão preenchidos.")
            
    return redirect('gestao_escolar')

# ==============================================================================
# 14. EXCLUSÃO DE PROFESSORES
# ==============================================================================
@login_required
def excluir_professor(request, professor_id):
    User = get_user_model()
    professor = get_object_or_404(User, id=professor_id)
    
    # 1. Segurança: Impede que o usuário apague a si mesmo ou outros administradores
    if professor.id == request.user.id or professor.role == 'ADMINISTRADOR':
        messages.error(request, "Ação negada. Você não pode excluir sua própria conta ou um administrador.")
    else:
        # 2. Integridade: Verifica se há relatórios vinculados para não quebrar o histórico
        if professor.relatorio_set.exists():
            messages.warning(request, "Não é possível excluir este professor porque ele já possui relatórios cadastrados. Recomendamos apenas desativar o acesso.")
        else:
            professor.delete()
            messages.success(request, "Professor removido do sistema com sucesso.")
            
    return redirect('gestao_escolar')

# ==============================================================================
# 15. CRIAR SUGESTÃO DIRETA (COORDENAÇÃO)
# ==============================================================================
@login_required
def criar_sugestao_coordenador(request):
    # Trava de segurança para gestores
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Acesso negado.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        codigo_bncc = request.POST.get('codigo_bncc', '').strip()
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        nivel_alvo = request.POST.get('nivel_alvo')
        
        try:
            # Busca a competência ignorando maiúsculas/minúsculas
            competencia = Competencia.objects.filter(codigo__iexact=codigo_bncc).first()
            
            if not competencia:
                raise Competencia.DoesNotExist

            # Cria a sugestão com status APROVADO automaticamente
            SugestaoAtividade.objects.create(
                titulo=titulo,
                descricao=descricao,
                nivel_alvo=nivel_alvo,
                competencia=competencia,
                professor_autor=request.user, 
                status='APROVADO' 
            )
            messages.success(request, f"Atividade oficial vinculada à competência {competencia.codigo} criada com sucesso!")
            
        except Competencia.DoesNotExist:
            messages.error(request, f"Erro: O código '{codigo_bncc}' não foi encontrado no banco da BNCC.")
        except Exception as e:
            messages.error(request, f"Erro inesperado ao salvar: {e}")

    # Retorna para o dashboard na aba específica
    base_url = reverse('dashboard')
    return redirect(f"{base_url}?tab=sugestoes")

# ==============================================================================
# 16. GESTÃO E FILTRO DE COMPETÊNCIAS (BNCC)
# ==============================================================================
@login_required
def gestao_competencias(request):
    # Apenas coordenadores podem gerenciar o banco de dados BNCC
    if request.user.role not in ['ADMINISTRADOR', 'COORDENADOR']:
        messages.error(request, "Acesso restrito à gestão.")
        return redirect('dashboard')
    
    # Captura filtros da URL
    busca = request.GET.get('busca')
    filtro_materia = request.GET.get('filtro_materia')
    
    competencias = Competencia.objects.all().order_by('codigo')
    
    # Filtro de busca textual (Código ou Descrição)
    if busca:
        competencias = competencias.filter(
            Q(codigo__icontains=busca) | Q(habilidade__icontains=busca)
        )
    
    # Filtro por componente curricular
    if filtro_materia:
        competencias = competencias.filter(componente=filtro_materia)

    # Limite de 50 resultados iniciais para performance de carregamento
    aviso_limite = False
    if not busca and not filtro_materia:
        competencias = competencias[:50]
        aviso_limite = True

    return render(request, 'gestao_competencias.html', {
        'competencias': competencias,
        'form_competencia': CompetenciaForm(),
        'busca_ativa': busca,
        'aviso_limite': aviso_limite,
        'materias': ['PORT', 'MAT', 'CIEN', 'HIST', 'GEO', 'ARTE', 'EDFIS', 'REL']
    })

# ==============================================================================
# 17. CRUD DE COMPETÊNCIAS (BNCC)
# ==============================================================================
@login_required
def salvar_competencia(request, competencia_id=None):
    # Se houver ID, busca para edição; se não, prepara para criação
    comp = get_object_or_404(Competencia, id=competencia_id) if competencia_id else None
    
    if request.method == 'POST':
        # O formulário gerencia a limpeza e validação (incluindo o campo anos_aplicacao)
        form = CompetenciaForm(request.POST, instance=comp)
        if form.is_valid():
            form.save()
            msg = "Alterações na competência salvas!" if competencia_id else "Nova competência BNCC cadastrada!"
            messages.success(request, msg)
        else:
            # Captura erros de validação (ex: código duplicado)
            messages.error(request, "Falha ao salvar. Verifique se o código BNCC já existe ou se há campos inválidos.")
            
    return redirect('gestao_competencias')

@login_required
def excluir_competencia(request, competencia_id):
    comp = get_object_or_404(Competencia, id=competencia_id)
    try:
        # BLOQUEIO DE SEGURANÇA: Só exclui se nunca tiver sido usada em avaliações de alunos
        if comp.avaliacao_set.exists():
             messages.warning(request, "Ação bloqueada: Esta competência já faz parte do histórico de avaliações de alunos e não pode ser removida.")
        else:
            comp.delete()
            messages.success(request, "Competência removida definitivamente do banco de dados.")
    except Exception as e:
        messages.error(request, f"Erro técnico ao tentar excluir: {e}")
        
    return redirect('gestao_competencias')

# ==============================================================================
# 18. CATÁLOGO BNCC (Visão de Consulta do Professor)
# ==============================================================================
@login_required
def visualizar_competencias(request):
    """
    View idêntica à de gestão, mas com travas de segurança para modo leitura.
    Reutiliza o template 'gestao_competencias.html'.
    """
    busca = request.GET.get('busca')
    filtro_materia = request.GET.get('filtro_materia')
    
    # Busca baseada no código
    competencias = Competencia.objects.all().order_by('codigo')
    
    if busca:
        competencias = competencias.filter(
            Q(codigo__icontains=busca) | Q(habilidade__icontains=busca)
        )
    
    if filtro_materia:
        competencias = competencias.filter(componente=filtro_materia)

    # Performance: Limita resultados se não houver filtro ativo
    aviso_limite = False
    if not busca and not filtro_materia:
        competencias = competencias[:50]
        aviso_limite = True

    return render(request, 'gestao_competencias.html', {
        'competencias': competencias,
        'busca_ativa': busca,
        'aviso_limite': aviso_limite,
        'materias': ['PORT', 'MAT', 'CIEN', 'HIST', 'GEO', 'ARTE', 'EDFIS', 'REL'],
        
        # VARIÁVEIS DE CONTROLE PARA O TEMPLATE:
        'somente_leitura': True,   # Oculta botões de Novo, Editar e Excluir no HTML
        'form_competencia': None   # Impede a renderização de modais de formulário
    })

@login_required
def baixar_relatorio_pdf(request, relatorio_id):
    """
    View que gera e retorna o PDF do relatório para o navegador.
    """
    # 1. Busca o relatório e as avaliações (com select_related para ser rápido)
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    avaliacoes = Avaliacao.objects.filter(relatorio=relatorio).select_related('competencia')

    # 2. Prepara os dados (contexto) que o PDF vai usar
    # Deve ser o mesmo contexto que você usa na view 'visualizar_relatorio'
    context = {
        'relatorio': relatorio,
        'avaliacoes': avaliacoes,
        'aluno': relatorio.aluno,
        'data_emissao': date.today(),
    }

    # 3. Chama a função do utils.py
    # O primeiro parâmetro é o caminho do seu template HTML formatado para PDF
    pdf = render_to_pdf('pdf/relatorio_template.html', context)

    # 4. Retorna o arquivo para o usuário
    if pdf:
        # Se quiser que o navegador abra o PDF, use:
        return pdf
        
        # Se preferir que o navegador baixe direto, use:
        # response = HttpResponse(pdf.content, content_type='application/pdf')
        # response['Content-Disposition'] = f'attachment; filename="Relatorio_{relatorio.aluno.nome_completo}.pdf"'
        # return response

    return HttpResponse("Erro ao gerar PDF", status=400)