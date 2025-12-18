from django import forms
from .models import Relatorio

class RelatorioForm(forms.ModelForm):
    class Meta:
        model = Relatorio
        fields = '__all__'
        exclude = ['aluno', 'professor', 'data_criacao']
        
        widgets = {}
        # Loop inteligente para aplicar estilo em todos os campos
        for field in [
            'port_nivel', 'port_obs', 'arte_nivel', 'arte_obs',
            'edfisica_nivel', 'edfisica_obs', 'mat_nivel', 'mat_obs',
            'ciencias_nivel', 'ciencias_obs', 'geo_nivel', 'geo_obs',
            'hist_nivel', 'hist_obs', 'religiao_nivel', 'religiao_obs'
        ]:
            if 'nivel' in field:
                widgets[field] = forms.Select(attrs={'class': 'form-select'})
            else:
                widgets[field] = forms.Textarea(attrs={
                    'class': 'form-control', 
                    'rows': 4,
                    'placeholder': 'Descreva as competências alcançadas nesta matéria...'
                })