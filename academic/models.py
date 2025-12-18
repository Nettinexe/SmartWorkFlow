from django.db import models
# Importamos AbstractUser para criar nosso próprio usuário (Professor/Coordenador)
# mantendo as funções nativas do Django (login, senha, grupos)
from django.contrib.auth.models import AbstractUser
# Importamos settings para referenciar o modelo de usuário de forma segura
from django.conf import settings

# ==============================================================================
# 1. GESTÃO DE USUÁRIOS E PERMISSÕES
# ==============================================================================
class CustomUser(AbstractUser):
    """
    Tabela de usuários personalizada.
    Substitui o usuário padrão do Django para adicionar o campo 'role' (função).
    """
    # Tupla de opções para o campo 'role'. O primeiro valor grava no banco, o segundo aparece na tela.
    TIPO_CHOICES = (
        ('ADMINISTRADOR', 'Administrador/Coordenador'), # Tem acesso total e painel de gestão
        ('PROFESSOR', 'Professor'),                     # Tem acesso restrito às suas turmas
    )
    
    # Campo que define o perfil de acesso. Default é 'Professor' por segurança.
    role = models.CharField(max_length=20, choices=TIPO_CHOICES, default='PROFESSOR', verbose_name="Função")
    
    # Função mágica que diz como o objeto aparece em textos (Ex: "Eduardo (Professor)")
    def __str__(self):
        return f"{self.first_name} ({self.get_role_display()})"


# ==============================================================================
# 2. ESTRUTURA ESCOLAR (TURMAS E ALUNOS)
# ==============================================================================
class Turma(models.Model):
    """
    Representa uma sala de aula física (o grupo de alunos).
    """
    # Lista fixa das séries curriculares baseadas na BNCC.
    # Isso padroniza o currículo, independente do nome da turma.
    SERIES_BNCC = [
        ('EI', 'Educação Infantil'),
        ('1EF', '1º Ano Fundamental'),
        ('2EF', '2º Ano Fundamental'),
        ('3EF', '3º Ano Fundamental'),
        ('4EF', '4º Ano Fundamental'),
        ('5EF', '5º Ano Fundamental'),
    ]
    
    # O nome que identifica a turma no dia a dia. Ex: "1º Ano B - Vespertino".
    nome = models.CharField(max_length=50, verbose_name="Nome da Turma")
    
    # Define O QUE essa turma estuda. Duas turmas diferentes (1º A e 1º B)
    # podem ter a mesma 'serie_curricular' (1EF), compartilhando as mesmas competências.
    serie_curricular = models.CharField(max_length=5, choices=SERIES_BNCC, verbose_name="Série (Currículo)")
    
    # Ano calendário da turma. Ajuda a filtrar turmas ativas de turmas passadas.
    ano_letivo = models.IntegerField(default=2025)
    
    # Vínculo Muitos-para-Muitos: Uma turma tem vários professores, e um professor tem várias turmas.
    # 'settings.AUTH_USER_MODEL' aponta para o nosso CustomUser.
    professores = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='turmas', blank=True)

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"

class Aluno(models.Model):
    # Nome completo do estudante.
    nome_completo = models.CharField(max_length=200)
    
    # Data de nascimento (opcional: null=True permite deixar vazio no banco).
    data_nascimento = models.DateField(null=True, blank=True)
    
    # Chave Estrangeira: Liga o aluno a UMA turma específica.
    # on_delete=models.CASCADE significa: se a Turma for apagada, o Aluno também é apagado.
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='alunos')

    def __str__(self):
        return self.nome_completo


# ==============================================================================
# 3. O CATÁLOGO BNCC (COMPETÊNCIAS)
# ==============================================================================
class Competencia(models.Model):
    """
    O Catálogo da BNCC. Esta tabela guarda todas as regras e descrições oficiais.
    Não está vinculada a alunos diretamente, é apenas uma biblioteca de consulta.
    """
    # Lista dos componentes curriculares (Matérias).
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

    # O código oficial (Ex: EF01LP19). unique=True impede cadastrar o mesmo código duas vezes.
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código BNCC")
    
    # A qual matéria isso pertence? (Ex: Matemática)
    componente = models.CharField(max_length=10, choices=COMPONENTES, verbose_name="Componente Curricular")
    
    # Campo texto simples para dizer quais séries usam essa competência (Ex: "1EF, 2EF").
    anos_aplicacao = models.CharField(max_length=100, help_text="Ex: 1EF, 2EF (Separados por vírgula)")
    
    # --- Campos Descritivos da BNCC ---
    # Usamos TextField em vez de CharField porque esses textos oficiais costumam ser grandes.
    habilidade = models.TextField("Descrição da Habilidade") # Texto principal da competência
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
    """
    Banco de ideias pedagógicas.
    Serve para o sistema sugerir ações baseadas na nota que o aluno tirou.
    """
    # Status da sugestão: Se for professor que criou, nasce PENDENTE. Se for Coordenador, já nasce APROVADO.
    STATUS_CHOICES = (
        ('PENDENTE', 'Aguardando Aprovação'),
        ('APROVADO', 'Aprovado (Disponível)'),
        ('REJEITADO', 'Rejeitado'),
    )
    
    # Níveis de nota (1 a 5) para gatilho da sugestão.
    NIVEL_ALVO_CHOICES = [
        ('1', '1 - Não desenvolvido'),
        ('2', '2 - Em desenvolvimento (início)'),
        ('3', '3 - Em desenvolvimento (parcial)'),
        ('4', '4 - Desenvolvido'),
        ('5', '5 - Plenamente desenvolvido'),
    ]

    # Liga a sugestão a uma competência específica (Ex: Sugestão para EF01MA01).
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    
    # Quem criou? Se o usuário for apagado, mantemos a sugestão mas deixamos autor vazio (SET_NULL).
    professor_autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # O "Cérebro": Se o aluno tirar nota '1', o sistema busca sugestões com nivel_alvo='1'.
    nivel_alvo = models.CharField(max_length=1, choices=NIVEL_ALVO_CHOICES, verbose_name="Sugerir para Nível")
    
    titulo = models.CharField(max_length=100) # Título curto (Ex: "Jogo dos Dados")
    descricao = models.TextField(verbose_name="Descrição da Prática") # Explicação detalhada
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDENTE')
    data_envio = models.DateTimeField(auto_now_add=True) # Data automática de criação

    def __str__(self):
        return f"Sugestão para {self.competencia.codigo} (Nível {self.nivel_alvo})"


# ==============================================================================
# 5. O RELATÓRIO TRIMESTRAL (A "CAPA")
# ==============================================================================
class Relatorio(models.Model):
    """
    O documento oficial que agrupa as avaliações de um trimestre.
    Funciona como uma 'pasta' que guarda as notas individuais.
    """
    TRIMESTRES = [
        ('1', '1º Trimestre'),
        ('2', '2º Trimestre'),
        ('3', '3º Trimestre'),
    ]
    
    # O Workflow (Fluxo de Trabalho) do relatório
    STATUS_FLUXO = [
        ('RASCUNHO', '📝 Rascunho (Professor Editando)'), # Só professor vê
        ('AGUARDANDO', '⏳ Aguardando Coordenação'),      # Coordenador vê e analisa
        ('APROVADO', '✅ Aprovado (Finalizado)'),         # Ninguém edita mais
        ('CORRECAO', '⚠️ Devolvido para Correção'),       # Volta para o professor editar
    ]

    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE)
    professor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    trimestre = models.CharField(max_length=1, choices=TRIMESTRES, default='1')
    ano = models.IntegerField(default=2025)
    
    # Controle do estado atual do documento
    status = models.CharField(max_length=20, choices=STATUS_FLUXO, default='RASCUNHO')
    
    # Espaço para o coordenador dizer "Melhore a observação x" caso devolva o relatório.
    feedback_coordenacao = models.TextField(blank=True, verbose_name="Feedback da Coordenação")
    
    # Datas automáticas para auditoria
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        # Regra de Ouro: O banco impede criar dois relatórios para o mesmo aluno no mesmo trimestre/ano.
        unique_together = ['aluno', 'trimestre', 'ano']

    def __str__(self):
        return f"Relatório {self.aluno} - {self.get_trimestre_display()}"


# ==============================================================================
# 6. AS AVALIAÇÕES (O "MIOLO" DO RELATÓRIO)
# ==============================================================================
class Avaliacao(models.Model):
    """
    A nota individual de cada competência dentro do relatório.
    Se o professor avaliou 5 competências, haverá 5 linhas nesta tabela ligadas ao mesmo Relatório.
    """
    NIVEIS = [
        ('1', '1 - Não desenvolvido'),
        ('2', '2 - Em desenvolvimento (início)'),
        ('3', '3 - Em desenvolvimento (parcial)'),
        ('4', '4 - Desenvolvido'),
        ('5', '5 - Plenamente desenvolvido'),
    ]
    
    # Liga essa nota ao relatório "pai"
    relatorio = models.ForeignKey(Relatorio, on_delete=models.CASCADE)
    
    # Liga essa nota à competência da BNCC (Ex: EF01MA01)
    competencia = models.ForeignKey(Competencia, on_delete=models.CASCADE)
    
    # A nota em si
    nivel = models.CharField(max_length=1, choices=NIVEIS)
    
    # Observação específica para ESTA competência (Ex: "Consegue somar, mas erra na subtração")
    observacao_especifica = models.TextField(blank=True, verbose_name="Obs. desta competência")
    
    class Meta:
        # Garante que não haja duas notas para a mesma competência dentro do mesmo relatório.
        unique_together = ('relatorio', 'competencia')