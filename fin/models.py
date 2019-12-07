import locale
from django.db import connections

class Sangria:
    sql_statement = """
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
    """
    table_header = [
        'Cod',
        'Data',
        'Hora',
        'Descricao',
        'Valor&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;'
    ]

    def load(self, data):
        cursor = connections['default'].cursor()
        cursor.execute(self.sql_statement, [data])
        #  adicionado '&#xa0;' para a coluna ficar com espaço suficente para
        #  evitar valores monetários ficarem com o R$ e valor em linhas distintas
        table = {'header': self.table_header,
                 'list': cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '

class Produto:
    sql_statement ="""
        SELECT TOP 100 [codigo_produto]
            ,p.[descricao]
            ,FORMAT(p.[preco_venda], 'C', 'pt-BR')
            ,p.[preco_custo]
            ,iif(p.preco_custo = 0, 0, cast((p.preco_venda/p.preco_custo - 1) as decimal(18,2)))
            ,p.[validade_dias]
            ,g.[descricao]
            ,p.[codigo_grupo]
            ,s.[descricao]
            ,p.[codigo_subgrupo]
            ,p.[ncm]
            ,p.[ativo]
        FROM [DTMLOCAL].[dbo].[tb_cad_produto] p
        JOIN [DTMLOCAL].[dbo].[tb_cad_grupo] g
          ON p.codigo_grupo = g.codigo_grupo
        JOIN [DTMLOCAL].[dbo].[tb_cad_subgrupo] s
          ON p.codigo_subgrupo = s.codigo_subgrupo
        WHERE (p.codigo_produto = %s
        OR p.descricao like %s)
    """
    sql_orderby = """
        ORDER BY p.[descricao]
    """
    table_header = [
        'Cod Produto',
        'Descricao&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Preco&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Custo',
        'Margem',
        'Validade',
        'Grupo',
        'Cod',
        'SubGrupo',
        'Cod',
        'NCM',
        'Ativo',
    ]

    def load(self, param):
        checkbox_list = [
            {'category': "Situação", 'options': [
                {'name': 'checkbox_inativo', 'label': "incluir inativo", 'value': "S", 'checked': param['inclui_inativo'], }]}
        ]
        table = {'checkbox_list': checkbox_list,}
        if param['texto_pesquisa'] != "":
            cursor = connections['default'].cursor()
            statement = self.sql_statement
            if not param['inclui_inativo']:
                statement += " AND p.[ativo] = 'S' "
            statement += self.sql_orderby
            cursor.execute(statement, [param['codigo_produto'], '%' + param['texto_pesquisa'] + '%'])
            lista_produto = cursor.fetchall()
            table.update({'header': self.table_header,
                           'list': lista_produto,})
        return table

    def __str__(self):
        return '(^o^)/ '

class Caderneta:
    def load(self, cod_cliente, data_ini, data_fim):
        cursor = connections['default'].cursor()
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
            SELECT TOP 100
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
    sql_statement = """
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
    """
    table_header = [
        'Data',
        'Hora',
        "Cod",
        'Descricao',
        'Qtd',
        'Preco',
        'Total',
        'Terminal',
        'Usuário',
    ]

    def load(self, num_comanda):
        cursor = connections['default'].cursor()
        cursor.execute(self.sql_statement, [num_comanda])
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

        if i > 0:
            lista.append(['Total','',locale.currency(total_comanda),'','','','','',''])

        table = {'header': self.table_header,
                 'list': lista}
        return table

    def __str__(self):
        return ' .-. '


class Movimento:
    sql_statement_caixa = """
        SELECT [codigo_movimento]
              ,[codigo_caixa]
              ,[codigo_usuario]
              ,(convert(varchar, [data_abertura], 3)) as data
              ,(convert(varchar, [hora_abertura], 8)) as inicio
              ,(convert(varchar, [hora_fechamento], 8)) as fim
          FROM [DTMLOCAL].[dbo].[tb_movimento_caixa]
          where data_abertura=%s
          order by codigo_movimento
    """
    sql_statement_fechamento = """
        SELECT [codigo_movimento]
              ,count(*) as cupons
              ,sum(total) as movimento
              ,sum(total)/count(*) as media
              ,sum(iif(codigo_caixa = 999,total,0)) as acerto
          FROM [DTMLOCAL].[dbo].[tb_fechamento_venda]
          where codigo_tipo_movimento = 1
              and codigo_cliente not in (55, 97, 98, 99)
              and codigo_movimento in (
    """
    sql_orderby_fechamento = """
        )
        group by codigo_movimento
    """
    table_header = [
        'Código',
        'Cupom',
        'Movimento',
        'Média&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Acerto&#xa0;&#xa0;&#xa0;&#xa0;',
        'Caixa',
        'Usuário',
        'Data',
        "Início",
        'Fim',
    ]

    def load(self, data):
        cursor = connections['default'].cursor()
        #obter lista dos códigos de movimento
        cursor.execute(self.sql_statement_caixa, [data])
        list_movimento = cursor.fetchall()
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
        cursor.execute(self.sql_statement_fechamento + movimentos + self.sql_orderby_fechamento)

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
            lista[lin][3] = locale.currency(linha[3])
            lista[lin][4] = locale.currency(linha[4])
            movimento = list_movimento[lin]
            #if linha[0] == movimento[0]:
            lista[lin].extend(movimento[1:])
            lin = lin + 1
        lista.append(['Total', cupons, locale.currency(total_movimento),
                     locale.currency(total_movimento/cupons),'','','','',''])

        table = {'header': self.table_header,
                 'list': lista}
        return table

    def __str__(self):
        return '(◕‿◕)'

class Fornecedor:
    sql_statement = """
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
    """
    table_header = [
        'Código',
        'Nome',
        'Descricao&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'CNPJ/CPF',
        'Grupo',
        'Descricao',
        'SubGrupo',
        'Descricao',
        'Ativo'
    ]
    def load(self, param):
        cursor = connections['default'].cursor()
        cursor.execute(self.sql_statement, [param['codigo_cfd'], '%' + param['texto_pesquisa'] + '%'
                       , '%' + param['texto_pesquisa'] + '%'])
        table = {'header': self.table_header,
                 'list': cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '


class Boleto:
    sql_statement = """
        SELECT TOP 50 Iif([baixado] = 0, 'AB', 'BX'), 
                        CONVERT(VARCHAR, Iif(pagamento_data IS NULL, data_vencimento, 
                                         pagamento_data), 3 
                        ) 
                        AS vencimento, 
                        CAST(Iif(pagamento_data IS NULL, valor_documento, pagamento_valor) as numeric(10,2)) 
                        AS valor, 
                        f.nome_fantasia, 
                        d.[codigo_cfd], 
                        Isnull((SELECT TOP 1 nome_titular 
                                FROM   [DTMLOCAL].[dbo].[tb_fin_contas] 
                                WHERE  codigo_conta = d.codigo_conta), '') 
                        AS Conta, 
                        d.[codigo_conta], 
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
                        ge2.descricao 
                        AS Grupo, 
                        ge1.grupo 
                        AS ID_Grupo, 
                        sg.[descricao] 
                        AS Sub_Grupo,
                        d.[codigo_grupo_fdc] 
                        AS ID_Sub_Grupo, 
                        [fin_duplicata_id] 
        FROM   [DTMLOCAL].[dbo].[tb_fin_duplicatas] d, 
               [DTMLOCAL].[dbo].[tb_fin_for_desp_cli] f, 
               [DTMLOCAL].[dbo].tb_fin_grupos_fdc sg, 
               [DTMLOCAL].[dbo].[tb_fin_grupos_estrutura] ge1, 
               [DTMLOCAL].[dbo].[tb_fin_grupos_estrutura] ge2 
        WHERE  d.codigo_cfd = f.codigo_cfd 
               AND d.codigo_grupo_fdc = sg.grupo 
               AND d.codigo_grupo_fdc = ge1.id 
               AND ge1.grupo = ge2.grupo 
               AND ge2.id = 0 
    """

    sql_orderby = """
            ORDER  BY baixado,
                      pagamento_data desc, 
                      data_vencimento
    """
    table_header = [
        'Bx',
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
        checkbox_list = [
            {'category': "Situação", 'options': [
                {'name': 'checkbox_baixado', 'label': "incluir baixado", 'value': "1", 'checked': param['inclui_baixado'], }]}
        ]
        cursor = connections['default'].cursor()
        statement = self.sql_statement
        if not param['inclui_baixado']:
            statement += " AND baixado = 0 "

        cursor.execute(statement + """
                   AND d.codigo_cfd = %s 
        """ + self.sql_orderby, [param['codigo_cfd']])
        table = {'header': self.table_header,
                 'list': cursor.fetchall(),
                 'checkbox_list': checkbox_list,}
        return table

    def __str__(self):
        return ' .-. '


class BoletoData(Boleto):
    sql_orderby = """
            ORDER  BY data_vencimento
    """

    def load(self, data_ini_str, data_fim_str):
        cursor = connections['default'].cursor()
        cursor.execute(self.sql_statement + """
              AND baixado = 0
              AND ((Data_Vencimento BETWEEN %s AND %s
                    AND Pagamento_Data IS NULL)
                   OR Pagamento_Data BETWEEN %s AND %s)
        """ + self.sql_orderby, [data_ini_str, data_fim_str,
                                 data_ini_str+" 00:00:00", data_fim_str+" 23:59:59"])
        table = {'header':self.table_header,
                 'list':cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '
