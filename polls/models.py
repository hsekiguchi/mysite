import datetime
import locale
from django.db import models
from django.utils import timezone
from django.db import connections


# Create your models here.
class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')

    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now

    def __str__(self):
        return str(self.id) + ' - ' + self.question_text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return str(self.id) + ' - ' + self.choice_text

class Sangria:
    def load(self, data):
        cursor = connections['myapp'].cursor()
        cursor.execute("""
            SELECT [codigo_movimento]
                  ,convert(varchar, [data], 3)
                  ,convert(varchar, [hora], 8)
                  ,[descricao]
                  ,FORMAT([total], 'C', 'pt-BR')
              FROM [DTMLOCAL].[dbo].[tb_fechamento_venda]
              where codigo_movimento in (select distinct codigo_movimento 
                  from [DTMLOCAL].[dbo].[tb_fechamento_venda] 
                  where data = %s
                  and hora > '03:00')
              and codigo_tipo_movimento=4
              order by codigo_movimento, data, hora        
        """, [data])
        #  adicionado '&#xa0;' para a coluna ficar com espaço suficente para
        #  evitar valores monetários ficarem com o R$ e valor em linhas distintas
        table = {'header':['Cod',
                           'Data',
                           'Hora',
                           'Descricao',
                           'Valor&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;'
                           ],
                 'list':cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '

class Produto:
    def load(self, param):
        cursor = connections['myapp'].cursor()
        cursor.execute("""
            SELECT TOP 1000 [codigo_produto]
                ,p.[descricao]
                ,FORMAT(p.[preco_venda], 'C', 'pt-BR')
                ,p.[preco_custo]
                ,iif(p.preco_custo = 0, 0, cast((p.preco_venda/p.preco_custo - 1) as decimal(18,2)))
                ,p.[validade_dias]
                ,p.[codigo_grupo]
                ,g.[descricao]
                ,p.[codigo_subgrupo]
                ,s.[descricao]
                ,p.[ncm]
                ,p.[ativo]
            FROM [DTMLOCAL].[dbo].[tb_cad_produto] p
            JOIN [DTMLOCAL].[dbo].[tb_cad_grupo] g
              ON p.codigo_grupo = g.codigo_grupo
            JOIN [DTMLOCAL].[dbo].[tb_cad_subgrupo] s
              ON p.codigo_subgrupo = s.codigo_subgrupo
            WHERE p.codigo_produto = %s
            OR p.descricao like %s
        """, [param['codigo_produto'], '%' + param['texto_pesquisa_str'] + '%'])
        table = {'header':['Cod Produto',
                           'Descricao&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
                           'Preco&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
                           'Custo',
                           'Margem',
                           'Validade',
                           'Grupo',
                           'Descricao',
                           'SubGrupo',
                           'Descricao',
                           'NCM',
                           'Ativo'
                           ],
                 'list':cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '

class Caderneta:
    def load(self, cod_cliente, data_ini, data_fim):
        cursor = connections['myapp'].cursor()
        cursor.execute("""
            SELECT nome
              FROM [DTMLOCAL].[dbo].[tb_cad_cliente]
              WHERE codigo_cliente = %s
        """, [cod_cliente])
        nome_cliente = cursor.fetchall()[0][0]
        if nome_cliente is None:
            nome_cliente = ""

        #saldo_anterior é o saldo anterior à data inicial da consulta
        #total_debito é o total de débios no período
        #total_credito é o total de créditos no período
        #saldo_periodo é o saldo anterior - total de débitos + total de créditos
        #saldo_atual é o saldo mais recente no momento da consulta
        #para otimizar a consulta, supondo que a consulta é feita em relação à período mais recente
        #calcularemos os saldos acima iniciando pelo saldo atual

        #obter o último saldo e a soma dos movimentos a partir da data final até o momento
        cursor.execute("""
            SELECT AVG([saldo])
                   ,SUM([valor])
                   ,SUM([credito])
            FROM [DTMLOCAL].[dbo].[tb_caderneta_consumo] c,
                [DTMLOCAL].[dbo].[tb_caderneta_saldo] s
            WHERE c.codigo_cliente = %s
            and s.codigo_cliente=c.codigo_cliente
            AND data > %s   
        """, [cod_cliente, data_fim])

        lista_saldo = cursor.fetchall()
        saldo_atual = lista_saldo[0][0]

        #se naõ houve movimentação entre a data_fim até o momento a query retorna vazia
        if saldo_atual is None:
            #obter o saldo autal da tabela de saldos
            cursor.execute("""
                SELECT [saldo]
                FROM [DTMLOCAL].[dbo].[tb_caderneta_saldo]
                WHERE codigo_cliente = %s 
            """, [cod_cliente])
            lista_saldo = cursor.fetchall()
            saldo_atual = lista_saldo[0][0]
            if saldo_atual is None:
                saldo_atual = 0
            saldo_periodo = saldo_atual
        else:
            saldo_periodo = saldo_atual + lista_saldo[0][1] - lista_saldo[0][2]

        #obter soma dos debitos e creditos do período
        cursor.execute("""
            SELECT SUM([valor])
                    ,SUM([credito])
            FROM [DTMLOCAL].[dbo].[tb_caderneta_consumo]
            WHERE codigo_cliente = %s
            AND data between %s and %s    
        """, [cod_cliente, data_ini, data_fim])

        lista_saldo = cursor.fetchall()
        total_debito = lista_saldo[0][0]
        if total_debito is None:
            total_debito = 0
            total_credito = 0
        else:
            total_credito = lista_saldo[0][1]
        saldo_anterior = saldo_periodo + total_debito - total_credito

        # obter os movimentos de debitos e creditos do período
        cursor.execute("""
            SELECT TOP 1000
                convert(varchar, [data], 3)
                ,convert(varchar, [hora], 8)
                ,FORMAT([valor], 'C', 'pt-BR')
                ,FORMAT([credito], 'C', 'pt-BR')
            FROM [DTMLOCAL].[dbo].[tb_caderneta_consumo]
            WHERE codigo_cliente = %s
            AND data between %s and %s       
        """, [cod_cliente, data_ini, data_fim])

        table = {
            'nome_cliente': nome_cliente,
            'saldo_anterior': locale.currency(saldo_anterior),
            'total_debito': locale.currency(total_debito),
            'total_credito': locale.currency(total_credito),
            'saldo_periodo': locale.currency(saldo_periodo),
            'saldo_atual': locale.currency(saldo_atual),
            'header': ['Data',
                       'Hora',
                       'Debito',
                       'Credito'
                       ],
             'list': cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '

class Comanda:
    def load(self, num_comanda):
        cursor = connections['myapp'].cursor()
        cursor.execute("""
            SELECT TOP 1000 
                convert(varchar, [data], 3)
                ,convert(varchar, [hora], 8)
                ,m.[codigo_produto]
                ,p.[descricao]
                ,[qtde]
                ,[valor_unitario]
                ,[total]
                ,[codigo_terminal]
                ,[usuario]
                FROM [DTMLOCAL].[dbo].[tb_movimento_venda] m,
				[DTMLOCAL].[dbo].[tb_cad_produto] p
                where m.codigo_produto = p.codigo_produto
				and num_cartao=%s
        """, [num_comanda])
        lista_itens = cursor.fetchall()
        lista=[]
        i=0
        total_comanda=0
        locale.setlocale(locale.LC_ALL, '')
        for item in lista_itens:
            lista.append(list(item))
            lista[i][5]=locale.currency(item[5])
            total_comanda += lista[i][6]
            lista[i][6]=locale.currency(item[6])
            i+=1

        lista.append(['Total','',locale.currency(total_comanda),'','','','','',''])


        table = {'header':['Data',
                           'Hora',
                           "Cod",
                           'Descricao',
                           'Qtd',
                           'Preco',
                           'Total',
                           'Terminal',
                           'Usuário',
                           ],
                 'list': lista}
        return table

    def __str__(self):
        return ' .-. '


class Movimento:
    def load(self, data):
        cursor = connections['myapp'].cursor()
        cursor.execute("""
            SELECT 
                   [codigo_movimento]
                  ,[codigo_caixa]
                  ,[codigo_usuario]
                  ,(convert(varchar, [data_abertura], 3)) as data
                  ,(convert(varchar, [hora_abertura], 8)) as inicio
                  ,(convert(varchar, [hora_fechamento], 8)) as fim
              FROM [DTMLOCAL].[dbo].[tb_movimento_caixa]
              where data_abertura=%s
              order by codigo_movimento
        """, [data])

        list_movimento = cursor.fetchall()

        #obter lista dos códigos de movimento
        movimentos = ''
        first_time = True
        for movimento in list_movimento:
            if first_time:
                movimentos = str(movimento[0])
                first_time = False
            else:
                movimentos= movimentos + ', ' + str(movimento[0])

        if first_time:
            return {}

        #obter quantidade de cupos e total de movimentos
        cursor.execute("""
            SELECT 
                   [codigo_movimento]
                  ,count(*) as cupons
                  ,sum(total) as movimento
              FROM [DTMLOCAL].[dbo].[tb_fechamento_venda]
              where codigo_movimento in (""" + movimentos + """)
              and num_cartao !=''
              and codigo_cliente not in (55, 97, 98, 99)
              group by codigo_movimento
        """)

        quantidade_list = cursor.fetchall()

        #merge das listas
        locale.setlocale(locale.LC_ALL, '')
        lin=0
        lista=[]
        cupons=0
        total_movimento=0
        for linha in quantidade_list:
            cupons += linha[1]
            total_movimento += linha[2]
            lista.append(list(linha))
            lista[lin][2] = locale.currency(linha[2])
            movimento = list_movimento[lin]
            #if linha[0] == movimento[0]:
            lista[lin].extend(movimento[1:])
            lin = lin + 1
        lista.append(['Total', cupons, locale.currency( total_movimento ),'','','',''])

        table = {'header': ['Código',
                            'Cupons',
                            'Movimento',
                            'Caixa',
                            'Usuário',
                            'Data',
                            "Início",
                            'Fim',
                            ],
                 'list': lista}
        return table

    def __str__(self):
        return ' .-. '

class Fornecedor:
    def load(self, param):
        cursor = connections['myapp'].cursor()
        cursor.execute("""
            SELECT TOP 1000 f.[Codigo_CFD]
                  ,f.[Nome_Fantasia]
                  ,f.[Descricao]
                  ,f.[CGC_CPF]
                  ,ge1.grupo as ID_Grupo
                  ,ge2.descricao as Grupo
                  ,f.[Grupo] as ID_Sub_Grupo
                  ,sg.[DESCRICAO] as Sub_Grupo
                  ,f.[inativo]
              FROM [DTMLOCAL].[dbo].[tb_fin_for_desp_cli] f,
              [DTMLOCAL].[dbo].tb_fin_grupos_fdc sg,
              [DTMLOCAL].[dbo].[tb_fin_grupos_estrutura] ge1,
              [DTMLOCAL].[dbo].[tb_fin_grupos_estrutura] ge2
              where f.Grupo = sg.GRUPO
              and f.Grupo = ge1.id
              and ge1.grupo = ge2.grupo
              and ge2.id = 0
              and (f.Codigo_CFD =%s
                or (f.nome_fantasia like %s or f.Descricao like %s))
              order by f.Descricao
        """, [param['codigo_cfd'], '%' + param['texto_pesquisa'] + '%'
                       , '%' + param['texto_pesquisa'] + '%'])
        table = {'header':['Código',
                           'Nome',
                           'Descricao&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
                           'CNPJ/CPF',
                           'Grupo',
                           'Descricao',
                           'SubGrupo',
                           'Descricao',
                           'Ativo'
                           ],
                 'list':cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '


class Boleto:
    sql_statement = """
            SELECT TOP 1000 [baixado], 
                            CONVERT(VARCHAR, Iif(pagamento_data IS NULL, data_vencimento, 
                                             pagamento_data), 3 
                            ) 
                            AS vencimento, 
                            CAST(Iif(pagamento_data IS NULL, valor_documento, pagamento_valor) as numeric(10,2)) 
                            AS valor, 
                            d.[codigo_cfd], 
                            f.nome_fantasia, 
                            d.[codigo_conta], 
                            Isnull((SELECT TOP 1 nome_titular 
                                    FROM   [DTMLOCAL].[dbo].[tb_fin_contas] 
                                    WHERE  codigo_conta = d.codigo_conta), '') 
                            AS Descricao, 
                            [numero_documento], 
                            LEFT(f.descricao, 25), 
                            CONVERT(VARCHAR, [data_emissao], 3) 
                            AS Data_Emissao, 
                            CONVERT(VARCHAR, [data_vencimento], 3) 
                            AS Vencimento, 
                            Iif(pagamento_data IS NULL, valor_documento, 
                            [valor_documento] + [pagamento_desconto] - [pagamento_acrescimo] 
                            ) AS Valor_Nota, 
                            CONVERT(VARCHAR, [pagamento_data], 3) 
                            AS Data_Pagamento, 
                            [pagamento_valor] 
                            AS Valor_Pagamento, 
                            [pagamento_desconto] 
                            AS Desconto, 
                            [pagamento_acrescimo] 
                            AS Acrescimo, 
                            ge1.grupo 
                            AS ID_Grupo, 
                            ge2.descricao 
                            AS Grupo, 
                            f.[grupo] 
                            AS ID_Sub_Grupo, 
                            sg.[descricao] 
                            AS Sub_Grupo,
                            [fin_duplicata_id] 
            FROM   [DTMLOCAL].[dbo].[tb_fin_duplicatas] d, 
                   [DTMLOCAL].[dbo].[tb_fin_for_desp_cli] f, 
                   [DTMLOCAL].[dbo].tb_fin_grupos_fdc sg, 
                   [DTMLOCAL].[dbo].[tb_fin_grupos_estrutura] ge1, 
                   [DTMLOCAL].[dbo].[tb_fin_grupos_estrutura] ge2 
            WHERE  d.codigo_cfd = f.codigo_cfd 
                   AND f.grupo = sg.grupo 
                   AND f.grupo = ge1.id 
                   AND ge1.grupo = ge2.grupo 
                   AND ge2.id = 0 
                   AND baixado = 0 
    """

    sql_orderby = """
            ORDER  BY pagamento_data, 
                      data_vencimento 
    """

    table_header = ['Bx',
                   'Vencimento',
                   'Valor',
                   'Código',
                   'Identificação',
                   'Conta',
                   'Descricao',
                   'Documento',
                   'Razão&#xa0;Social&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
                   'Emissão',
                   'Vencimento',
                   'Valor&#xa0;Nota',
                   'Pagamento',
                   'Valor Pago',
                   'Desconto',
                   'Acréscimo',
                   'Grupo',
                   'Descrição',
                   'Subgrupo',
                   'Descrição',
                   'ID',
                   ]


class BoletoFornecedor(Boleto):
    def load(self, param):
        cursor = connections['myapp'].cursor()
        cursor.execute(self.sql_statement + """
                   AND d.codigo_cfd = %s 
        """ + self.sql_orderby, [param['codigo_cfd']])
        table = {'header':self.table_header,
                 'list':cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '


class BoletoData(Boleto):
    def load(self, data_ini, data_fim):
        cursor = connections['myapp'].cursor()
        cursor.execute(self.sql_statement + """
              AND ((Data_Vencimento BETWEEN %s AND %s
                    AND Pagamento_Data IS NULL)
                   OR Pagamento_Data BETWEEN %s AND %s)
        """ + self.sql_orderby, [data_ini, data_fim,
                                 data_ini+" 00:00:00", data_fim+" 23:59:59"])
        table = {'header':self.table_header,
                 'list':cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '
