from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class CustomUser(AbstractUser):
    TIPO_CHOICES = (
        ('ADMINISTRADOR', 'Administrador'),
        ('PROFESSOR', 'Professor'),
    )
    role = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PROFESSOR', verbose_name="Função")

class Turma(models.Model):
    nome = models.CharField(max_length=50)
    ano_letivo = models.IntegerField()

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo}"
    
class Aluno(models.Model):
    nome_completo = models.CharField(max_length=200)
    data_nascimento = models.DateField(null=True, blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')

    def __str__(self):
        return self.nome_completo

class CompetenciaBNCC(models.Model):
    # Identificação
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código da Habilidade") 
    componente = models.CharField(max_length=50, verbose_name="Componente Curricular")
    
  
    pratica_linguagem = models.CharField(max_length=200, verbose_name="Práticas de Linguagens")
    
    habilidade = models.TextField(verbose_name="Habilidade")
    
    objetos_conhecimento = models.CharField(max_length=255, verbose_name="Objetos do Conhecimento")
    
    conteudos_relacionados = models.TextField(verbose_name="Conteúdos Relacionados", blank=True, null=True)
    
    orientacoes_pedagogicas = models.TextField(verbose_name="Orientações Pedagógicas", blank=True, null=True)
    
    descritores_saeb = models.TextField(verbose_name="Descritores do SAEB", blank=True, null=True)
    

    feedback_nivel_1 = models.TextField(help_text="Texto para Nível 1 (Não Desenvolvido)")
    feedback_nivel_2 = models.TextField(help_text="Texto para Nível 2 (Em desenvolvimento inicial)")
    feedback_nivel_3 = models.TextField(help_text="Texto para Nível 3 (Em desenvolvimento parcial)")
    feedback_nivel_4 = models.TextField(help_text="Texto para Nível 4 (Desenvolvido)")
    feedback_nivel_5 = models.TextField(help_text="Texto para Nível 5 (Plenamente Desenvolvido)")

    def __str__(self):
        return f"{self.codigo} - {self.componente}"
class Relatorio(models.Model):
    STATUS_CHOICES = (
        ('RASCUNHO', 'Rascunho'),
        ('ENVIADO', 'Enviado para Coordenação'),
        ('APROVADO', 'Aprovado'),
    )
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    professor = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    periodo = models.CharField(max_length=50)
    status = models.CharField(max_length=20 , choices=STATUS_CHOICES, default='RASCUNHO')

    avaliacoes = models.JSONField(default=dict, blank=True)

    observacoes_gerais = models.TextField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Relatório de {self.aluno.nome_completo} - {self.periodo}"
# ... (Mantenha as outras classes como estão)

class SugestaoAtividade(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE', 'Aguardando Aprovação'),
        ('APROVADO', 'Aprovado'),
        ('REJEITADO', 'Rejeitado'),
    )

    # Vínculos
    competencia = models.ForeignKey(CompetenciaBNCC, on_delete=models.CASCADE, verbose_name="Competência Alvo")
    professor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="Professor Autor")
    
    # O Conteúdo
    titulo = models.CharField(max_length=100, verbose_name="Título da Atividade")
    descricao = models.TextField(verbose_name="Descrição da Atividade/Prática")
    
    # Controle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.status}) - {self.professor.first_name}"