from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Turma, Aluno, CompetenciaBNCC, Relatorio, SugestaoAtividade

# --- CONFIGURAÇÃO ESPECIAL DO USUÁRIO ---
# Criamos uma classe que "herda" o admin padrão e adiciona nosso campo extra
class CustomUserAdmin(UserAdmin):
    # fieldsets controla a tela de EDIÇÃO de usuário (quando você clica num usuário existente)
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Profissionais', {'fields': ('role',)}),
    )
    
    # add_fieldsets controla a tela de CRIAÇÃO de usuário (quando você clica em Add User)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações Profissionais', {'fields': ('role',)}),
    )
    
    # Mostra a coluna 'role' na lista geral de usuários
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')

# Registramos o CustomUser usando nossa configuração nova (CustomUserAdmin)
admin.site.register(CustomUser, CustomUserAdmin)

# --- OUTROS REGISTROS ---
admin.site.register(Turma)
admin.site.register(Aluno)
admin.site.register(CompetenciaBNCC)
admin.site.register(Relatorio)

@admin.register(SugestaoAtividade)
class SugestaoAtividadeAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'competencia', 'professor', 'status', 'data_envio')
    list_filter = ('status', 'competencia')
    actions = ['aprovar_sugestoes']

    def aprovar_sugestoes(self, request, queryset):
        queryset.update(status='APROVADO')
    aprovar_sugestoes.short_description = "Aprovar sugestões selecionadas"