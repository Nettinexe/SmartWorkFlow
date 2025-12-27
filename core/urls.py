from django.contrib import admin
from django.urls import path, include 
from academic.views import (
    dashboard, turma_detail, avaliar_aluno, avaliar_materia, sugerir_atividade, 
    area_coordenacao, aprovar_sugestao, visualizar_relatorio, enviar_relatorio_final,
    limpar_materia, detalhe_sugestao, decisao_relatorio, configuracoes_sistema,
    gestao_escolar, salvar_turma, excluir_turma, salvar_aluno, excluir_aluno,
    salvar_professor, excluir_professor, criar_sugestao_coordenador, gestao_competencias,
    salvar_competencia, excluir_competencia, visualizar_competencias, historico_coordenacao
)

urlpatterns = [
    # ==========================================================================
    # 1. ADMINISTRAÇÃO E AUTENTICAÇÃO
    # ==========================================================================
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), # Login/Logout nativo
    
    # ==========================================================================
    # 2. DASHBOARD E FLUXO PRINCIPAL
    # ==========================================================================
    path('', dashboard, name='dashboard'), #
    path('turma/<int:turma_id>/', turma_detail, name='turma_detail'), #
    
    # ==========================================================================
    # 3. AVALIAÇÃO E RELATÓRIOS (Workflow do Professor)
    # ==========================================================================
    path('avaliar/<int:aluno_pk>/', avaliar_aluno, name='avaliar_aluno'), #
    path('relatorio/<int:relatorio_id>/disciplina/<str:materia_codigo>/', avaliar_materia, name='avaliar_materia'), #
    path('relatorio/<int:relatorio_id>/limpar/<str:materia_codigo>/', limpar_materia, name='limpar_materia'), #
    path('relatorio/<int:relatorio_id>/enviar/', enviar_relatorio_final, name='enviar_relatorio_final'), #
    path('relatorio/<int:relatorio_id>/visualizar/', visualizar_relatorio, name='visualizar_relatorio'), #
    
    # ==========================================================================
    # 4. INTELIGÊNCIA PEDAGÓGICA (Sugestões de Atividades)
    # ==========================================================================
    path('relatorio/<int:relatorio_id>/sugerir/<int:competencia_id>/', sugerir_atividade, name='sugerir_atividade'), #
    path('sugestao/criar/coordenacao/', criar_sugestao_coordenador, name='criar_sugestao_coordenador'), #
    path('sugestao/<int:sugestao_id>/detalhes/', detalhe_sugestao, name='detalhe_sugestao'), #
    path('sugestao/<int:sugestao_id>/<str:decisao>/', aprovar_sugestao, name='aprovar_sugestao'), #
    
    # ==========================================================================
    # 5. MODERAÇÃO E CONFIGURAÇÕES (Workflow da Coordenação)
    # ==========================================================================
    path('coordenacao/', area_coordenacao, name='area_coordenacao'), #
    path('relatorio/<int:relatorio_id>/decisao/', decisao_relatorio, name='decisao_relatorio'), #
    path('sistema/configuracoes/', configuracoes_sistema, name='configuracoes_sistema'), #
    path('coordenacao/historico/', historico_coordenacao, name='historico_coordenacao'),
    
    # ==========================================================================
    # 6. GESTÃO ESCOLAR (Turmas, Alunos e Professores)
    # ==========================================================================
    path('gestao/', gestao_escolar, name='gestao_escolar'), #
    
    # Turmas
    path('gestao/turma/salvar/', salvar_turma, name='criar_turma'), #
    path('gestao/turma/salvar/<int:turma_id>/', salvar_turma, name='editar_turma'), #
    path('gestao/turma/excluir/<int:turma_id>/', excluir_turma, name='excluir_turma'), #
    
    # Alunos
    path('gestao/aluno/salvar/', salvar_aluno, name='criar_aluno'), #
    path('gestao/aluno/salvar/<int:aluno_pk>/', salvar_aluno, name='editar_aluno'), #
    path('gestao/aluno/excluir/<int:aluno_pk>/', excluir_aluno, name='excluir_aluno'), #
    
    # Professores
    path('gestao/professor/salvar/', salvar_professor, name='criar_professor'), #
    path('gestao/professor/salvar/<int:professor_id>/', salvar_professor, name='editar_professor'), #
    path('gestao/professor/excluir/<int:professor_id>/', excluir_professor, name='excluir_professor'), #

    # ==========================================================================
    # 7. GESTÃO BNCC (Competências)
    # ==========================================================================
    path('gestao/competencias/', gestao_competencias, name='gestao_competencias'), #
    path('gestao/competencias/salvar/', salvar_competencia, name='criar_competencia'), #
    path('gestao/competencias/salvar/<int:competencia_id>/', salvar_competencia, name='editar_competencia'), #
    path('gestao/competencias/excluir/<int:competencia_id>/', excluir_competencia, name='excluir_competencia'), #
    path('bncc/catalogo/', visualizar_competencias, name='catalogo_bncc_professor'), #
]