from django.contrib import admin
from django.urls import path, include 
from academic.views import dashboard, turma_detail, avaliar_aluno, avaliar_materia,sugerir_atividade, area_coordenacao, gerenciar_sugestao, visualizar_relatorio

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', dashboard, name='dashboard'),
    path('turma/<int:turma_id>/', turma_detail, name='turma_detail'),
    path('avaliar/<int:aluno_id>/', avaliar_aluno, name='avaliar_aluno'),
    path('relatorio/<int:relatorio_id>/disciplina/<str:materia_codigo>/', avaliar_materia, name='avaliar_materia'),
    path('relatorio/<int:relatorio_id>/sugerir/<int:competencia_id>/', sugerir_atividade, name='sugerir_atividade'),
    path('coordenacao/', area_coordenacao, name='area_coordenacao'),
    path('coordenacao/sugestao/<int:sugestao_id>/<str:acao>/', gerenciar_sugestao, name='gerenciar_sugestao'),
    path('relatorio/<int:relatorio_id>/visualizar/', visualizar_relatorio, name='visualizar_relatorio'),
]