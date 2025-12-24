from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# ==============================================================================
# 1. GESTÃO DE USUÁRIOS E PERMISSÕES
# ==============================================================================
class CustomUser(AbstractUser):
    TIPO_CHOICES = (
        ('ADMINISTRADOR', 'Administrador/Coordenador'),
        ('PROFESSOR', 'Professor'),
    )
    
    role = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES, 
        default='PROFESSOR', 
        verbose_name="Função"
    )
    
    def __str__(self):
        # Usamos first_name se disponível, senão o username
        nome = self.get_full_name() or self.username
        return f"{nome} ({self.get_role_display()})"


# ==============================================================================
# 2. ESTRUTURA ESCOLAR (TURMAS E ALUNOS)
# ==============================================================================
class Turma(models.Model):
    # Padronização das séries conforme usamos no formulário de competências
    SERIES_BNCC = [
        ('1', '1º Ano Fundamental'),
        ('2', '2º Ano Fundamental'),
        ('3', '3º Ano Fundamental'),
        ('4', '4º Ano Fundamental'),
        ('5', '5º Ano Fundamental'),
        ('6', '6º Ano Fundamental'),
        ('7', '7º Ano Fundamental'),
        ('8', '8º Ano Fundamental'),
        ('9', '9º Ano Fundamental'),
    ]

    nome = models.CharField(max_length=50, verbose_name="Nome da Turma")
    serie_curricular = models.CharField(max_length=2, choices=SERIES_BNCC, verbose_name="Série (Currículo)")
    ano_letivo = models.IntegerField(default=2026)
    
    # Campo ManyToMany centralizado (removida a duplicata que existia no arquivo anterior)
    professores = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='turmas', 
        blank=True,
        verbose_name="Professores da Turma"
    )

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"

class Aluno(models.Model):
    nome_completo = models.CharField(max_length=200)
    data_nascimento = models.DateField(null=True, blank=True)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')

    def __str__(self):
        return self.nome_completo


# ==============================================================================
# 3. O CATÁLOGO BNCC (COMPETÊNCIAS)
# ==============================================================================
class Competencia(models.Model):
    # Siglas alinhadas com o que usamos nas Views e Templates
    COMPONENTES = [
        ('PORT', 'Língua Portuguesa'),
        ('ARTE', 'Arte'),
        ('EDFIS', 'Educação Física'),
        ('MAT', 'Matemática'),
        ('CIEN', 'Ciências'),
        ('GEO', 'Geografia'),
        ('HIST', 'História'),
        ('REL', 'Ensino Religioso'),
    ]

    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código BNCC")
    componente = models.CharField(max_length=10, choices=COMPONENTES, verbose_name="Componente Curricular")
    
    # Campo que armazena os anos (Ex: "1,2,3")
    anos_aplicacao = models.CharField(
        max_length=100, 
        help_text="Ex: 1, 2, 3 (Números das séries separados por vírgula)"
    )
    
    habilidade = models.TextField("Descrição da Habilidade")
    prat_linguagens = models.TextField("Práticas de Linguagens/Unidade Temática", blank=True)
    obj_conhecimento = models.TextField("Objetos do Conhecimento", blank=True)
    cont_relacionado = models.TextField("Conteúdos Relacionados", blank=True)
    or_pedagogicas = models.TextField("Orientações Pedagógicas", blank=True)
    desc_saeb = models.TextField("Descritores do SAEB", blank=True)
    
    def __str__(self):
        return f"[{self.componente}] {self.codigo}"


# ==============================================================================
# 4. INTELIGÊNCIA PEDAGÓGICA (SUGESTÕES)
# ==============================================================================
class SugestaoAtividade(models.Model):
    STATUS_CHOICES = (
        ('PENDENTE', 'Aguardando Aprovação'),
        ('APROVADO', 'Aprovado (Disponível)'),
        ('REJEITADA', 'Rejeitada'), # Alinhado com a lógica de exclusão automática
    )
    
    NIVEL_ALVO_CHOICES = [
        ('1', '1 - Não desenvolvido'),
        ('2', '2 - Em desenvolvimento (início)'),
        ('3', '3 - Em desenvolvimento (parcial)'),
        ('4', '4 - Desenvolvido'),
        ('5', '5 - Plenamente desenvolvido'),
    ]

    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    professor_autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    nivel_alvo = models.CharField(max_length=1, choices=NIVEL_ALVO_CHOICES, verbose_name="Sugerir para Nível")
    
    titulo = models.CharField(max_length=100)
    descricao = models.TextField(verbose_name="Descrição da Prática")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    data_envio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.competencia.codigo}"


# ==============================================================================
# 5. O RELATÓRIO TRIMESTRAL (A "CAPA")
# ==============================================================================
class Relatorio(models.Model):
    TRIMESTRES = [
        ('1', '1º Trimestre'),
        ('2', '2º Trimestre'),
        ('3', '3º Trimestre'),
    ]
    
    STATUS_FLUXO = [
        ('RASCUNHO', '📝 Rascunho (Professor Editando)'),
        ('ANALISE', '⏳ Aguardando Coordenação'), # Alterado de AGUARDANDO para ANALISE para bater com as Views
        ('APROVADO', '✅ Aprovado (Finalizado)'),
        ('CORRECAO', '⚠️ Devolvido para Correção'),
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trimestre = models.CharField(max_length=1, choices=TRIMESTRES, default='1')
    ano = models.IntegerField(default=2025)
    status = models.CharField(max_length=20, choices=STATUS_FLUXO, default='RASCUNHO')
    feedback_coordenacao = models.TextField(blank=True, verbose_name="Feedback da Coordenação")
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['aluno', 'trimestre', 'ano']

    def __str__(self):
        return f"Relatório {self.aluno} - {self.get_trimestre_display()} ({self.ano})"


# ==============================================================================
# 6. AS AVALIAÇÕES (O "MIOLO" DO RELATÓRIO)
# ==============================================================================
class Avaliacao(models.Model):
    NIVEIS = [
        ('1', '1 - Não desenvolvido'),
        ('2', '2 - Em desenvolvimento (início)'),
        ('3', '3 - Em desenvolvimento (parcial)'),
        ('4', '4 - Desenvolvido'),
        ('5', '5 - Plenamente desenvolvido'),
    ]
    
    relatorio = models.ForeignKey(Relatorio, on_delete=models.CASCADE, related_name='avaliacoes')
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=1, choices=NIVEIS, null=True, blank=True) # Permitir null para competências selecionadas mas não avaliadas
    observacao_especifica = models.TextField(blank=True, verbose_name="Obs. desta competência")
    
    class Meta:
        unique_together = ('relatorio', 'competencia')
        verbose_name_plural = "Avaliações"

# ==============================================================================
# 7. CONFIGURAÇÃO GLOBAL DO SISTEMA
# ==============================================================================
class ConfiguracaoSistema(models.Model):
    TRIMESTRES = [
        ('1', '1º Trimestre'),
        ('2', '2º Trimestre'),
        ('3', '3º Trimestre'),
    ]
    
    ano_letivo = models.IntegerField(default=2025, verbose_name="Ano Letivo Atual")
    trimestre_ativo = models.CharField(max_length=1, choices=TRIMESTRES, default='1', verbose_name="Trimestre Ativo")
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = "Configuração do Sistema"
        verbose_name_plural = "Configurações do Sistema"

    def __str__(self):
        return f"Configuração Atual: {self.get_trimestre_ativo_display()} de {self.ano_letivo}"