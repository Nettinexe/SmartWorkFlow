from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Turma, Aluno, Competencia, 
    SugestaoAtividade, Relatorio, Avaliacao, ConfiguracaoSistema
)

# ==============================================================================
# 1. USUÁRIO (CustomUser)
# ==============================================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'first_name', 'email', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']
    
    # Organização dos campos na edição
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Profissionais', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Profissionais', {'fields': ('role',)}),
    )

# ==============================================================================
# 2. TURMA (Com filtro de professores e interface otimizada)
# ==============================================================================
@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'serie_curricular', 'exibir_professores')
    search_fields = ('nome',)
    list_filter = ('serie_curricular',)
    
    # Melhora a seleção de muitos para muitos (caixa de busca lateral)
    filter_horizontal = ('professores',)

    def exibir_professores(self, obj):
        return ", ".join([p.first_name for p in obj.professores.all()])
    exibir_professores.short_description = 'Professores Vinculados'

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "professores":
            # Filtra para mostrar apenas usuários com papel de PROFESSOR ou ADMIN
            kwargs["queryset"] = CustomUser.objects.filter(role__in=['PROFESSOR', 'ADMINISTRADOR'])
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# ==============================================================================
# 3. ALUNO
# ==============================================================================
@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'turma', 'data_nascimento')
    search_fields = ('nome_completo',)
    list_filter = ('turma',)

# ==============================================================================
# 4. COMPETÊNCIA (BNCC)
# ==============================================================================
@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'componente', 'anos_aplicacao', 'habilidade_curta')
    search_fields = ('codigo', 'habilidade')
    list_filter = ('componente', 'anos_aplicacao')
    list_per_page = 50 # Facilita navegar em muitas habilidades

    def habilidade_curta(self, obj):
        return obj.habilidade[:100] + "..." if len(obj.habilidade) > 100 else obj.habilidade
    habilidade_curta.short_description = 'Habilidade'

# ==============================================================================
# 5. RELATÓRIO E AVALIAÇÕES (Inlines para ver as notas dentro do relatório)
# ==============================================================================
class AvaliacaoInline(admin.TabularInline):
    model = Avaliacao
    extra = 0 # Não cria linhas vazias extras automaticamente
    fields = ('competencia', 'nivel', 'observacao_especifica')

@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'trimestre', 'ano', 'professor', 'status')
    list_filter = ('status', 'trimestre', 'ano')
    search_fields = ('aluno__nome_completo', 'professor__first_name')
    inlines = [AvaliacaoInline] # Permite ver todas as notas ao abrir um relatório

# ==============================================================================
# 6. SUGESTÃO DE ATIVIDADES
# ==============================================================================
@admin.register(SugestaoAtividade)
class SugestaoAtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'competencia', 'professor_autor', 'status', 'data_envio')
    list_filter = ('status', 'nivel_alvo')
    search_fields = ('titulo', 'descricao')
    date_hierarchy = 'data_envio' # Barra de tempo no topo para filtrar

# ==============================================================================
# 7. CONFIGURAÇÃO DO SISTEMA
# ==============================================================================
@admin.register(ConfiguracaoSistema)
class ConfiguracaoAdmin(admin.ModelAdmin):
    list_display = ('ano_letivo', 'trimestre_ativo', 'data_fim')
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True

# Opcional: Registrar Avaliacao separadamente se quiser buscar notas específicas
@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('relatorio', 'competencia', 'nivel')
    list_filter = ('nivel',)