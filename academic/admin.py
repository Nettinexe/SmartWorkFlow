from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Turma, Aluno, Competencia, SugestaoAtividade, Relatorio, Avaliacao

# ==============================================================================
# 1. CONFIGURAÇÃO ESPECIAL DE USUÁRIO (CRIPTOGRAFIA)
# ==============================================================================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    # Isso garante que a senha seja tratada com criptografia correta
    model = CustomUser
    
    # Exibe a coluna 'role' (Função) na lista de usuários
    list_display = ['username', 'first_name', 'email', 'role', 'is_staff']
    
    # Permite editar o campo 'role' na tela de edição do usuário
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Profissionais', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Profissionais', {'fields': ('role',)}),
    )

# ==============================================================================
# 2. CONFIGURAÇÃO ESPECIAL DA TURMA (FILTRO DE PROFESSORES)
# ==============================================================================
@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'serie_curricular', 'ano_letivo')
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "professores":
            kwargs["queryset"] = CustomUser.objects.filter(role='PROFESSOR')
        return super().formfield_for_manytomany(db_field, request, **kwargs)

# ==============================================================================
# 3. CONFIGURAÇÃO DA COMPETÊNCIA
# ==============================================================================
@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'componente', 'anos_aplicacao', 'habilidade') 
    search_fields = ('codigo', 'habilidade', 'obj_conhecimento') 
    list_filter = ('componente',) 

# ==============================================================================
# 4. REGISTROS SIMPLES
# ==============================================================================
# Note: Removi o CustomUser daqui porque ele já foi registrado lá em cima
admin.site.register(Aluno)
admin.site.register(Relatorio)
admin.site.register(Avaliacao)
admin.site.register(SugestaoAtividade)