from django.shortcuts import render, get_object_or_404, redirect 
from django.contrib.auth.decorators import login_required
from .models import Turma, Aluno, Relatorio, Competencia, Avaliacao, SugestaoAtividade
from django.contrib import messages
import random


# ==============================================================================
# 1. PAINEL PRINCIPAL (DASHBOARD)
# ==============================================================================
# ==============================================================================
# 1. PAINEL PRINCIPAL (DASHBOARD COM KPIs PARA TODOS)
# ==============================================================================
@login_required
def dashboard(request):
    usuario = request.user
    
    # --- VISÃO DO PROFESSOR (Foca na produtividade dele) ---
    if usuario.role == 'PROFESSOR':
        # 1. Busca as turmas dele
        turmas = Turma.objects.filter(professores=usuario)
        
        # 2. Total de Alunos (Soma os alunos de todas as turmas dele)
        # O 'distinct()' evita contar o mesmo aluno 2x se ele estiver em 2 turmas do professor (raro, mas possível)
        total_alunos = Aluno.objects.filter(turma__in=turmas).distinct().count()
        
        # 3. Relatórios Iniciados (Quantos relatórios este professor já criou em 2025/1)
        iniciados = Relatorio.objects.filter(
            professor=usuario, 
            ano=2025, 
            trimestre='1'
        ).count()
        
        # 4. Cálculo de Pendentes (Quem falta começar?)
        # Pendentes = Total de Alunos - Iniciados
        pendentes = total_alunos - iniciados
        
        context = {
            'perfil_nome': 'Painel do Professor',
            'turmas': turmas,
            'is_professor': True,
            # KPIs do Professor
            'total_alunos': total_alunos,
            'total_turmas': turmas.count(),
            'iniciados': iniciados,
            'pendentes': pendentes
        }

    # --- VISÃO DA COORDENAÇÃO (Gestão Global) ---
    else:
        total_alunos = Aluno.objects.count()
        total_turmas = Turma.objects.count()
        sugestoes_pendentes = SugestaoAtividade.objects.filter(status='AGUARDANDO').count()
        relatorios_pendentes = Relatorio.objects.filter(status='RASCUNHO').count()
        
        context = {
            'perfil_nome': 'Gestão Escolar',
            'total_alunos': total_alunos,
            'total_turmas': total_turmas,
            'sugestoes_pendentes': sugestoes_pendentes,
            'relatorios_pendentes': relatorios_pendentes,
            'is_professor': False
        }
    
    return render(request, 'dashboard.html', context)

# ==============================================================================
# 2. DETALHES DA TURMA (LISTA DE ALUNOS)
# ==============================================================================
@login_required
def turma_detail(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    
    # Segurança
    if request.user.role == 'PROFESSOR' and request.user not in turma.professores.all():
        return redirect('dashboard')
    
    # Busca os alunos
    alunos = turma.alunos.all().order_by('nome_completo')
    
    # --- CÁLCULO DE PROGRESSO ---
    # 1. Descobre quantas competências existem para essa série (Ex: 1EF tem 50 competências)
    total_competencias = Competencia.objects.filter(
        anos_aplicacao__contains=turma.serie_curricular
    ).count()

    # 2. Para cada aluno, calcula quanto já foi feito
    for aluno in alunos:
        # Busca o relatório atual (Ano 2025, Tri 1)
        relatorio = Relatorio.objects.filter(
            aluno=aluno, 
            ano=2025, 
            trimestre='1'
        ).first()
        
        progresso = 0
        
        if relatorio and total_competencias > 0:
            # Conta quantas notas (Avaliacao) já foram salvas neste relatório
            avaliacoes_feitas = Avaliacao.objects.filter(relatorio=relatorio).count()
            # Regra de 3 para achar a porcentagem
            progresso = int((avaliacoes_feitas / total_competencias) * 100)
        
        # "Cola" essa informação no aluno temporariamente para usar no HTML
        aluno.progresso_calculado = progresso
        
        # Define a cor da barra baseado no progresso
        if progresso == 0:
            aluno.status_cor = "secondary"
        elif progresso == 100:
            aluno.status_cor = "success" # Verde
        else:
            aluno.status_cor = "primary" # Azul

    return render(request, 'turma_detail.html', {
        'turma': turma,
        'alunos': alunos
    })

@login_required
def avaliar_aluno(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # Contexto fixo (2025/1)
    ano_atual = 2025
    trimestre_atual = '1' 
    
    # Busca ou cria o relatório
    relatorio, created = Relatorio.objects.get_or_create(
        aluno=aluno,
        ano=ano_atual,
        trimestre=trimestre_atual,
        defaults={
            'professor': request.user,
            'status': 'RASCUNHO'
        }
    )
    
    # Lista base de matérias
    lista_materias = [
        ('PORT', 'Língua Portuguesa', 'bi-chat-quote'),
        ('MAT', 'Matemática', 'bi-calculator'),
        ('CIEN', 'Ciências', 'bi-virus'),
        ('HIST', 'História', 'bi-hourglass-split'),
        ('GEO', 'Geografia', 'bi-globe-americas'),
        ('ARTE', 'Arte', 'bi-palette'),
        ('EDFIS', 'Educação Física', 'bi-bicycle'),
        ('REL', 'Ensino Religioso', 'bi-heart'),
    ]

    # NOVA LÓGICA: Processa cada matéria para ver se está completa
    materias_processadas = []
    
    serie_aluno = aluno.turma.serie_curricular # Ex: "1EF"
    
    for codigo, nome, icone in lista_materias:
        # 1. Quantas competências existem para essa matéria nessa série?
        total = Competencia.objects.filter(
            componente=codigo, 
            anos_aplicacao__contains=serie_aluno
        ).count()
        
        # 2. Quantas avaliações já foram feitas nesse relatório?
        feitas = Avaliacao.objects.filter(
            relatorio=relatorio, 
            competencia__componente=codigo
        ).count()
        
        # 3. Verifica se completou (Só marca se tiver pelo menos 1 competência e tudo estiver feito)
        concluido = (total > 0 and feitas >= total)
        
        # Adiciona na lista final com o status
        materias_processadas.append({
            'codigo': codigo,
            'nome': nome,
            'icone': icone,
            'concluido': concluido,
            'progresso': f"{feitas}/{total}" # Opcional: para mostrar números se quiser
        })
    
    return render(request, 'selecionar_materia.html', {
        'aluno': aluno,
        'relatorio': relatorio,
        'materias': materias_processadas # Agora passamos a lista inteligente
    })

# ==============================================================================
# 4. FORMULÁRIO DE AVALIAÇÃO (COM PESQUISA E ADIÇÃO)
# ==============================================================================
@login_required
def avaliar_materia(request, relatorio_id, materia_codigo):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    aluno = relatorio.aluno
    serie_aluno = aluno.turma.serie_curricular
    
    # --- LÓGICA 1: ADICIONAR NOVA COMPETÊNCIA (Se o usuário pesquisou) ---
    if request.method == 'POST' and 'btn_adicionar' in request.POST:
        termo_busca = request.POST.get('termo_busca')
        
        # Busca competências que tenham esse código ou texto, 
        # MAS que sejam dessa matéria e dessa série
        competencia_encontrada = Competencia.objects.filter(
            componente=materia_codigo,
            anos_aplicacao__contains=serie_aluno,
            codigo__icontains=termo_busca # Busca pelo código (ex: EF01...)
        ).first() # Pega a primeira que achar
        
        if competencia_encontrada:
            # Cria a avaliação vazia para ela aparecer na lista
            Avaliacao.objects.get_or_create(
                relatorio=relatorio,
                competencia=competencia_encontrada
            )
            messages.success(request, f"Competência {competencia_encontrada.codigo} adicionada!")
        else:
            messages.error(request, "Competência não encontrada ou não pertence a esta matéria/série.")
            
        return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=materia_codigo)
    
    # ---------------------------------------------------------------
    # LÓGICA 2: EXCLUIR COMPETÊNCIA (COM TRAVA DE SEGURANÇA)
    # ---------------------------------------------------------------
    if request.method == 'POST' and 'btn_excluir' in request.POST:
        avaliacao_id = request.POST.get('btn_excluir')
        
        # Busca a avaliação
        avaliacao_para_apagar = get_object_or_404(Avaliacao, id=avaliacao_id, relatorio=relatorio)
        
        # REGRA DE NEGÓCIO: Se já tem nível (nota) salvo, NÃO pode excluir.
        if avaliacao_para_apagar.nivel:
            messages.error(request, "Não é possível excluir uma competência que já possui nota salva. Limpe a nota primeiro se necessário.")
        else:
            avaliacao_para_apagar.delete()
            messages.warning(request, "Competência removida da lista.")
            
        return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=materia_codigo)

    # --- LÓGICA 2: SALVAR NOTAS (Se o usuário clicou em Salvar Tudo) ---
    if request.method == 'POST' and 'btn_salvar' in request.POST:
        # Pega todas as avaliações que já estão na tela
        avaliacoes_na_tela = Avaliacao.objects.filter(relatorio=relatorio, competencia__componente=materia_codigo)
        
        for av in avaliacoes_na_tela:
            nivel = request.POST.get(f'nivel_{av.competencia.id}')
            obs = request.POST.get(f'obs_{av.competencia.id}')
            
            if nivel:
                av.nivel = nivel
                av.observacao_especifica = obs
                av.save()
        
        messages.success(request, "Notas atualizadas com sucesso!")
        return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=materia_codigo)

    # --- VISUALIZAÇÃO: MOSTRA SÓ O QUE JÁ FOI ADICIONADO ---
    avaliacoes_existentes = Avaliacao.objects.filter(
        relatorio=relatorio, 
        competencia__componente=materia_codigo
    ).order_by('competencia__codigo')

    return render(request, 'form_avaliacao.html', {
        'relatorio': relatorio,
        'materia_codigo': materia_codigo,
        'avaliacoes': avaliacoes_existentes # Agora passamos as avaliações, não a lista bruta de competências
    })

@login_required
def sugerir_atividade(request, relatorio_id, competencia_id):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    competencia = get_object_or_404(Competencia, id=competencia_id)
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        nivel_sugerido = request.POST.get('nivel_sugerido')

        # Define o status automaticamente com base no cargo
        if request.user.role in ['ADMINISTRADOR', 'COORDENADOR']:
            status_inicial = 'APROVADA' # Chefe não pega fila
        else:
            status_inicial = 'AGUARDANDO' # Professor precisa de aprovação
        
        # Cria a sugestão no banco
        SugestaoAtividade.objects.create(
            competencia=competencia,
            professor_autor=request.user,
            titulo=titulo,
            descricao=descricao,
            nivel_alvo=nivel_sugerido,
            status=status_inicial
        )
        
        messages.success(request, "Sua sugestão foi enviada para a coordenação! Obrigado por colaborar.")
        # Volta para a tela de avaliação onde ele estava
        return redirect('avaliar_materia', relatorio_id=relatorio.id, materia_codigo=competencia.componente)

    return render(request, 'form_sugestao.html', {
        'relatorio': relatorio,
        'competencia': competencia
    })

@login_required
def area_coordenacao(request):
    # SEGURANÇA: Só Coordenador/Admin pode entrar aqui
    if request.user.role == 'PROFESSOR':
        messages.error(request, "Acesso restrito à coordenação.")
        return redirect('dashboard')
    
    # 1. Busca Sugestões Pendentes (status='AGUARDANDO')
    # Nota: Usamos 'AGUARDANDO' na view anterior, então buscamos por ele aqui.
    sugestoes_pendentes = SugestaoAtividade.objects.filter(status='AGUARDANDO')
    
    # 2. Busca Relatórios Pendentes (futuramente, quando criarmos o botão de enviar)
    relatorios_pendentes = Relatorio.objects.filter(status='AGUARDANDO')
    
    return render(request, 'area_coordenacao.html', {
        'sugestoes': sugestoes_pendentes,
        'relatorios': relatorios_pendentes
    })

# ==============================================================================
# 7. AÇÃO DE APROVAR SUGESTÃO
# ==============================================================================
@login_required
def gerenciar_sugestao(request, sugestao_id, acao):
    # acao pode ser 'aprovar' ou 'rejeitar'
    if request.user.role == 'PROFESSOR':
        return redirect('dashboard')
        
    sugestao = get_object_or_404(SugestaoAtividade, id=sugestao_id)
    
    if acao == 'aprovar':
        sugestao.status = 'APROVADA'
        sugestao.save()
        messages.success(request, f"Sugestão '{sugestao.titulo}' aprovada! Agora ela aparecerá para todos.")
    
    elif acao == 'rejeitar':
        sugestao.status = 'REJEITADA'
        sugestao.save()
        messages.warning(request, f"Sugestão '{sugestao.titulo}' foi arquivada.")
        
    return redirect('area_coordenacao')

@login_required
def visualizar_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(Relatorio, id=relatorio_id)
    avaliacoes = Avaliacao.objects.filter(relatorio=relatorio)
    
    # Dicionário para guardar: { avaliacao_id : lista_de_sugestoes }
    sugestoes_por_avaliacao = {}
    
    for avaliacao in avaliacoes:
        # A MÁGICA: Busca sugestões APROVADAS que batem com a Competência E com o Nível da nota
        sugestoes_compativeis = list(SugestaoAtividade.objects.filter(
            competencia=avaliacao.competencia,
            nivel_alvo=avaliacao.nivel, # Se tirou 1, busca sugestão pra nível 1
            status='APROVADA'
        ))
        
        # Sorteia até 2 sugestões para não poluir o relatório
        if sugestoes_compativeis:
            sugestoes_escolhidas = random.sample(sugestoes_compativeis, min(len(sugestoes_compativeis), 2))
            sugestoes_por_avaliacao[avaliacao.id] = sugestoes_escolhidas
            
    return render(request, 'relatorio_final.html', {
        'relatorio': relatorio,
        'avaliacoes': avaliacoes,
        'sugestoes_map': sugestoes_por_avaliacao
    })