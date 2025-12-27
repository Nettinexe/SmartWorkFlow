from django import forms
from django.contrib.auth import get_user_model
from .models import Relatorio, Turma, Aluno, Competencia

User = get_user_model()

# ==============================================================================
# 1. GESTÃO DE PROFESSORES
# ==============================================================================
class ProfessorForm(forms.ModelForm):
    turmas = forms.ModelMultipleChoiceField(
        queryset=Turma.objects.all().order_by('nome'),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled d-flex flex-wrap gap-3'}),
        required=False,
        label="Turmas Vinculadas"
    )

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email'] # Incluído e-mail
        labels = {
            'first_name': 'Nome Completo',
            'username': 'Login',
            'email': 'E-mail'
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login de Acesso'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite o nome completo'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail para contato'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['turmas'].initial = self.instance.turmas.all()

# ==============================================================================
# 2. GESTÃO DE TURMAS
# ==============================================================================
class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        # Adicionados: ano_letivo e turno conforme solicitado
        fields = ['nome', 'serie_curricular', 'ano_letivo', 'turno']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 3º Ano B'}),
            'serie_curricular': forms.Select(attrs={'class': 'form-select'}),
            'ano_letivo': forms.NumberInput(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-select'}),
        }

# ==============================================================================
# 3. GESTÃO DE ALUNOS
# ==============================================================================
class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        # Reordenado e incluído o campo matricula (Chave Primária)
        fields = ['nome_completo', 'data_nascimento', 'turma', 'matricula']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do estudante'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'turma': forms.Select(attrs={'class': 'form-select'}),
            'matricula': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número da Matrícula'}),
        }

# ==============================================================================
# 4. GESTÃO DE COMPETÊNCIAS E RELATÓRIOS (Mantidos conforme sua lógica)
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

class RelatorioForm(forms.ModelForm):
    class Meta:
        model = Relatorio
        fields = '__all__'
        exclude = ['aluno', 'professor', 'data_criacao']
        widgets = {}