from django import forms
from django.contrib.auth import get_user_model
from .models import Relatorio, Turma, Aluno, Competencia

User = get_user_model()

# ==============================================================================
# 1. GESTÃO DE PROFESSORES
# ==============================================================================
class ProfessorForm(forms.ModelForm):
    # Campo para selecionar as turmas vinculadas ao professor
    turmas = forms.ModelMultipleChoiceField(
        queryset=Turma.objects.all().order_by('nome'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled d-flex flex-wrap gap-3'}),
        required=False,
        label="Turmas Vinculadas"
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login de Acesso'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail (Opcional)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se estiver editando um professor, pré-seleciona as turmas dele
        if self.instance and self.instance.pk:
            self.fields['turmas'].initial = self.instance.turmas.all()

# ==============================================================================
# 2. GESTÃO DE RELATÓRIOS (Campos de Matéria)
# ==============================================================================
class RelatorioForm(forms.ModelForm):
    class Meta:
        model = Relatorio
        fields = '__all__'
        exclude = ['aluno', 'professor', 'data_criacao']
        
        # Mantendo seu loop inteligente para estilização
        widgets = {}
        campos_materias = [
            'port_nivel', 'port_obs', 'arte_nivel', 'arte_obs',
            'edfisica_nivel', 'edfisica_obs', 'mat_nivel', 'mat_obs',
            'ciencias_nivel', 'ciencias_obs', 'geo_nivel', 'geo_obs',
            'hist_nivel', 'hist_obs', 'religiao_nivel', 'religiao_obs'
        ]
        
        for field in campos_materias:
            # Verifica se o campo existe no modelo antes de aplicar o widget
            if 'nivel' in field:
                widgets[field] = forms.Select(attrs={'class': 'form-select'})
            else:
                widgets[field] = forms.Textarea(attrs={
                    'class': 'form-control', 
                    'rows': 4,
                    'placeholder': 'Descreva as competências alcançadas...'
                })

# ==============================================================================
# 3. GESTÃO DE TURMAS E ALUNOS
# ==============================================================================
class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome', 'serie_curricular']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1º Ano A'}),
            'serie_curricular': forms.Select(attrs={'class': 'form-select'}),
        }

class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome_completo', 'turma', 'data_nascimento']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Aluno'}),
            'turma': forms.Select(attrs={'class': 'form-select'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

# ==============================================================================
# 4. GESTÃO DE COMPETÊNCIAS (BNCC)
# ==============================================================================
class CompetenciaForm(forms.ModelForm):
    anos_selecao = forms.MultipleChoiceField(
        choices=[(str(i), f'{i}º Ano') for i in range(1, 10)],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'd-flex gap-3 flex-wrap'}),
        label="Anos de Aplicação",
        required=True
    )

    class Meta:
        model = Competencia
        fields = ['codigo', 'componente', 'habilidade']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control text-uppercase', 'placeholder': 'Ex: EF01MA01'}),
            'componente': forms.Select(attrs={'class': 'form-select'}),
            'habilidade': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        anos = cleaned_data.get('anos_selecao')
        if anos:
            self.instance.anos_aplicacao = ",".join(anos)
        return cleaned_data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.anos_aplicacao:
            self.fields['anos_selecao'].initial = self.instance.anos_aplicacao.split(',')