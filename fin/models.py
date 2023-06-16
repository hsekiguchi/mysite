import locale
import time
import os
from enum import Enum
from django.conf import settings
from django.db import connections
from django.db import models

from django.utils.dateparse import parse_date
from google.oauth2 import service_account
import gspread

class Sangria(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_sangria", "Permite consultar sangrias"),
        ]

    sql_statement = """
               select 
	        fr.caixa ,        
	        fr.motivo ,
	        fr.valor ,
	        IF(fr.removido <> '', 'S', 'N') as estorno ,
	        fr.data,
	        fr.hora 
        from ajxfood.financeiro_retiradas fr 
        where fr.caixa in (
        select distinct
            cr.caixa
        from ajxfood.caixa_recebimento cr
        where cr.data = %s 
        order by cr.caixa
        )      
    """
    table_header = [
        'Cod',
        'Descricao',
        'Valor&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Estorno',
        'Data&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Hora'
    ]

    def load(self, data):
        cursor = connections['appdata'].cursor()
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
        select 
            p.cod_produto ,
            p.ean ,
            p.nome as descricao_produto,
            p.preco_venda ,
            p.preco_custo ,
            round (p.preco_venda / p.preco_custo - 1, 2) as margem,
            greatest(p.estoque_atual, 0) as estoque,
            p.`data` as data_alteracao_produto, 
            COALESCE(p.balanca_validade, 0) as validade_produto,
            pt.nome as tipo_produto,
            d.departamento,
            g.grupo ,
            p.ncm 
        from ajxfood.produtos p 
        left join ajxfood.produtos_tipo pt 
            on p.codigo_tipo  = pt.codigo
        left join ajxfood.grupos g 
            on p.codigo_grupo = g.codigo
        left join ajxfood.produtos_departamentos d
        	on p.codigo_departamento = d.codigo
        where (p.cod_produto = %s
            or p.ean = %s
            or p.nome like %s)
    """
    sql_orderby = """
        order by p.nome
    """
    table_header = [
        'Cod Produto',
        'Cod EAN',
        'Descricao&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Preco&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Custo',
        'Margem',
        'Estoque',
        'Alteração',
        'Validade',
        'Tipo',
        'Departamento',
        'Grupo',
        'NCM',
    ]

    def load(self, param):
        checkbox_list = [
            {'category': "Situação", 'options': [
                {'name': 'checkbox_inativo', 'label': "incluir inativo", 'value': "S", 'checked': param['inclui_inativo'], }]}
        ]
        table = {'checkbox_list': checkbox_list,}
        if param['texto_pesquisa'] != "":
            cursor = connections['appdata'].cursor()
            statement = self.sql_statement
            if not param['inclui_inativo']:
                statement += " AND p.removido = '' "
            statement += self.sql_orderby
            cursor.execute(statement, [param['codigo_produto'],
                                       "'" + param['texto_pesquisa'] + "'",
                                       '%' + param['texto_pesquisa'] + '%'])
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

class TipoEspecie (Enum):
    DINHEIRO = 1
    iFOOD = 5

class Movimento(models.Model):
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_movimento_especie", "Permite consultar movimento por espécie"),
        ]

    sql_statement_caixa = """
        select 
            cr.caixa,
            count(*) as cupom,
            cast(sum(crf.valor) as decimal(12,2)) as movimento,
            cast(sum(crf.valor)/count(*) as decimal(12,2)) as media,          
			cast(ca.valor as decimal(10,2)) as fundo_inicial,
            cast(clcd.1c as decimal)*0.01+cast(clcd.5c as decimal)*0.05+
	        	cast(clcd.10c as decimal)*0.1 +cast(clcd.25c as decimal)*0.25+
	        	cast(clcd.50c as decimal)*0.5+cast(clcd.1r as decimal)+
	        	cast(clcd.2r as decimal)*2+cast(clcd.5r as decimal)*5+
	        	cast(clcd.10r as decimal)*10+cast(clcd.20r as decimal)*20+
	        	cast(clcd.50r as decimal)*50+cast(clcd.100r as decimal)*100+
	        	cast(clcd.200r as decimal)*200 as fundo_final,
            cr.id as usuario,            
            cr.data as data,
            min(ca.hora) as hora_inicio,
            max(cr.hora) as hora_fim
        from ajxfood.caixa_recebimento cr
        left join ajxfood.caixa_recebimento_formas crf
        	on cr.codigo_online  = crf.codigo_recebimento
        left join ajxfood.caixa_abertura ca 
        	on cr.caixa = ca.caixa 
        left join ajxfood.caixa_livro_caixa_dinheiro clcd 
    		on cr.caixa = clcd.caixa
        where crf.tipo not in ('FIADO','CORTESIA')
        and cr.data = %s    
        group by cr.caixa
    """
    sql_statement_fechamento = """
        SELECT [codigo_movimento]
              ,count(*) as cupons
              ,sum(total) as movimento
              ,sum(total)/count(*) as media
              ,sum(iif(codigo_caixa = 999,total,0)) as acerto
          FROM [DTMLOCAL].[dbo].[tb_fechamento_venda]
          where codigo_tipo_movimento = 1
              and codigo_cliente not in (55)
              and codigo_movimento in (
    """
    sql_orderby_fechamento = """
        )
        group by codigo_movimento
    """

    sql_statement_tipo = """
        select 
            crf.tipo,
	        cast(sum(crf.valor) as decimal(12,2)) as movimento
        from ajxfood.caixa_recebimento cr,
             ajxfood.caixa_recebimento_formas crf 
        where cr.codigo_online  = crf.codigo_recebimento 
            and cr.caixa in (
        """
    sql_orderby_tipo = """
            )
            group by crf.tipo
        """


    sql_statement_cigarro = """
        select COALESCE(sum(total), 0)  as valor
        from (
            SELECT 
                f.total as total 
            FROM DTMLOCAL.dbo.tb_cad_produto p,
              [DTMLOCAL].[dbo].[tb_cad_subgrupo] s,
              [DTMLOCAL].[dbo].[tb_cad_grupo] g,
              DTMLOCAL.dbo."tb_fechamento_produto" f
              LEFT JOIN DTMLOCAL.dbo.tb_caderneta_consumo c
              ON f.codigo_venda = c.codigo_venda
            WHERE f.codigo_produto = p.codigo_produto
            and s.codigo_subgrupo = p.codigo_subgrupo
            and s.codigo_grupo = g.codigo_grupo
            and f.data = %s
            and f.hora > '1900-01-01 00:00'
            and g.descricao = 'CIGARRO'
        ) t
    """
    sql_statement_produto_proprio = """
        select COALESCE(sum(total), 0)  as valor
        from (
            SELECT 
                f.total as total 
            FROM DTMLOCAL.dbo.tb_cad_produto p,
              DTMLOCAL.dbo."tb_fechamento_produto" f
            WHERE f.codigo_produto = p.codigo_produto
			and p.codigo_tipo_produto = 3
            and f.data = %s
            and f.hora > '1900-01-01 00:00'
        ) t
    """
    table_header = [
        'Código',
        'Cupom',
        'Movimento',
        'Tkt&nbsp;Médio',
        'Fundo&nbsp;Ini',
        'Fundo&nbsp;Fin',
        'Usuário&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Data&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        "Início",
        'Fim',
    ]

    def load(self, data):
        cursor = connections['appdata'].cursor()
        #obter lista dos códigos de movimento a serem usados na seleção da cláusula in
        cursor.execute(self.sql_statement_caixa, [data])
        list_movimento = cursor.fetchall()

        # #obter venda de cigarros
        # cursor.execute(self.sql_statement_cigarro, [data])
        # cigarro_list = cursor.fetchall()
        # total_cigarro = cigarro_list[0][0]
        #
        # #obter venda de produtos da casa
        # cursor.execute(self.sql_statement_produto_proprio, [data])
        # produto_proprio_list = cursor.fetchall()
        # total_produto_proprio = produto_proprio_list[0][0]
        #
        # #obter quantidade de cupons e total de movimentos
        # cursor.execute(self.sql_statement_fechamento + movimentos + self.sql_orderby_fechamento)
        #
        # quantidade_list = cursor.fetchall()
        #
        #obter caixas do dia e respectivos movimentos
        locale.setlocale(locale.LC_ALL, '')
        lin=0
        lista=[]
        lista_caixas = ''
        cupons=0
        total_movimento=0
        # total_acerto=0
        for linha in list_movimento:
            # criar lista de caixas para a cláusula in
            lista_caixas = lista_caixas + str(linha[0]) + ','
            # acumular quantidade de cupons e do movimento
            cupons += linha[1]
            total_movimento += linha[2]
            #adicionar a linha para exibição, formatando valores monetários
            lista.append(list(linha))
            lista[lin][2] = locale.currency(linha[2])
            lista[lin][3] = locale.currency(linha[3])
            lin = lin + 1

        ticket_medio = 0 if cupons == 0 else total_movimento/cupons

        lista.append(['Total', cupons, locale.currency(total_movimento),
                      locale.currency(ticket_medio),
                      '','','',''])

        #obter total por tipo de pagamento
        tamanho = len(lista_caixas)
        caixas = lista_caixas[0:tamanho-1] if tamanho != 0 else '0'
        cursor.execute(self.sql_statement_tipo + caixas
                       + self.sql_orderby_tipo)
        list_especie = cursor.fetchall()

        lista_especie=[]
        lin=0
        for linha in list_especie:
            lista_especie.append(list(linha))
            lista_especie[lin][1] = locale.currency(linha[1])
            lin+=1

        table = {
            'caixas': caixas,
            # 'cupons': cupons,
            # 'total_movimento': locale.currency(total_movimento),
            # 'ticket_medio': (locale.currency(total_movimento/cupons)) if cupons > 0 else '-',
            # 'total_acerto': locale.currency(total_acerto),
            # 'total_cigarro': locale.currency(total_cigarro),
            # 'total_movimento_sem_cigarro': locale.currency(total_movimento - total_cigarro),
            # 'total_produto_proprio': locale.currency(total_produto_proprio),
            # 'total_revenda': locale.currency(total_movimento - total_produto_proprio),
            'header': self.table_header,
            'list': lista,
            # 'total_especie': locale.currency(total_especie),
            # 'total_cartao': locale.currency(total_cartao),
            # 'total_ifood': locale.currency(total_ifood),
            'lista_especie': lista_especie,
        }

        return table

    def __str__(self):
        return '(◕‿◕)'


class CadernetaCliente:
    sql_statement = """
        select 
            c.codigo ,
            c.nome_razao,
            c.nome_fantasia,
            c.tel_1,
            c.tel_2,
            c.limite_credito,
            c.cpf_cnpj 
        from ajxfood.clientes c
        where (c.codigo=%s
            or (c.nome_razao like %s or c.nome_fantasia like %s))
    """
    table_header = [
        'Código',
        'Nome',
        'Nome&nbsp;Fantasia',
        'Tel&nbsp;1',
        'Tel&nbsp;2',
        'Limite',
        'CNPJ/CPF',
    ]
    def load(self, param):
        cursor = connections['appdata'].cursor()
        cursor.execute(self.sql_statement, [param['codigo_cliente'], '%' + param['codigo_cliente_str'] + '%'
                       , '%' + param['codigo_cliente_str'] + '%'])
        table = {'header': self.table_header,
                 'list': cursor.fetchall()}
        return table

    def __str__(self):
        return ' .-. '


class Fornecedor:
    sql_statement = """
        select 
            c.codigo ,
            c.nome_razao,
            c.nome_fantasia,
            c.tel_1,
            c.tel_2,
            c.limite_credito,
            c.cpf_cnpj 
        from ajxfood.clientes c
        where (c.codigo=%s
            or (c.nome_razao like %s or c.nome_fantasia like %s))
    """
    table_header = [
        'Código',
        'Nome',
        'Nome&nbsp;Fantasia',
        'Tel&nbsp;1',
        'Tel&nbsp;2',
        'Limite',
        'CNPJ/CPF',
    ]
    def load(self, param):
        cursor = connections['appdata'].cursor()
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


class Preco:
    sql_statement = """
        select 
            codigo_produto,
            descricao, 
            FORMAT( data_alteracao, 'dd/MM/yyyy HH:mm', 'pt-BR' ),   
            FORMAT(preco_custo, 'C', 'pt-BR'),
            FORMAT(preco_venda, 'C', 'pt-BR')
        from [DTMLOCAL].[dbo].[tb_cad_produto] 
        where codigo_produto < 10000
        and ativo = 'S'
    """
    sql_orderby_produto = """
            ORDER  BY codigo_produto
    """
    sql_orderby_data_alteracao = """
            ORDER  BY data_alteracao desc
    """
    table_header_produto = [
        'Cod Produto',
        'Descrição&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Data Última Alteração',
        'Preço Custo',
        'Preço Sistema',
        'Preço Cardápio',
    ]

    table_header_data_alteracao = [
        'Cod Produto',
        'Descrição&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
        'Data Última Alteração',
        'Preço Custo',
        'Preço Sistema',
    ]

    def load(self, data_ini_str=None):

        if data_ini_str is None:
            sql_statement = self.sql_statement + self.sql_orderby_produto
            table_header = self.table_header_produto
        else:
            sql_statement = self.sql_statement + " and data_alteracao < '" + \
                            data_ini_str + "'"+ self.sql_orderby_data_alteracao
            table_header = self.table_header_data_alteracao

        cursor = connections['default'].cursor()
        cursor.execute(sql_statement)
        ts = time.localtime()
        table = {'header': table_header,
                 'list': cursor.fetchall(),
                 'timestamp': time.strftime("%d/%m/%Y %H:%M", ts)}
        return table

    def __str__(self):
        return ' .-. '

class PrecoCardapio:

    def load(self):
        module_dir = os.path.dirname(__file__)
        LOCATION = os.path.join(module_dir, getattr(settings, "GOOGLE_KEY_LOCATION", None))
        DOC_ID = getattr(settings, "CARDAPIO_DOC_ID", None)
        CURRENT_PRICE_SHEET_NAME = getattr(settings, "CURRENT_PRICE_SHEET_NAME", None)

        gc = gspread.service_account(filename = LOCATION)
        doc = gc.open_by_key(DOC_ID)
        sheet = doc.worksheet(CURRENT_PRICE_SHEET_NAME)

        list = sheet.get_all_values()
        #obter timestamp da última atualização
        ts = list[0][5]
        #eliminar primeira linha de cabeçalho
        del list[0]

        table = {'list': list,
                 'timestamp': ts}
        return table

    def update(self, param):
        module_dir = os.path.dirname(__file__)
        KEY_LOCATION = os.path.join(module_dir, getattr(settings, "GOOGLE_KEY_LOCATION", None))
        DOC_ID = getattr(settings, "CARDAPIO_DOC_ID", None)
        CURRENT_PRICE_SHEET_NAME = getattr(settings, "CURRENT_PRICE_SHEET_NAME", None)

        gc = gspread.service_account(filename = KEY_LOCATION)
        doc = gc.open_by_key(DOC_ID)
        sheet = doc.worksheet(CURRENT_PRICE_SHEET_NAME)
        doc.values_clear("'"+CURRENT_PRICE_SHEET_NAME+"'!A2:E2000")
        list = param['list']
        # for row in param['list']:
        #     list.append([row[0], row[2]])
        sheet.update('A2:E' + str(len(list)+1), list)
        sheet.update('F1', param['timestamp'])

        pass

    def __str__(self):
        return ' .-. '


# movimento
#     sql_statement_caixa = """
#         SELECT [codigo_movimento]
#               ,[codigo_caixa]
#               ,[codigo_usuario]
#               ,(convert(varchar, [data_abertura], 3)) as data
#               ,(convert(varchar, [hora_abertura], 8)) as inicio
#               ,(convert(varchar, [hora_fechamento], 8)) as fim
#           FROM [DTMLOCAL].[dbo].[tb_movimento_caixa]
#           where data_abertura=%s
#           order by codigo_movimento
#     """
#     sql_statement_fechamento = """
#         SELECT [codigo_movimento]
#               ,count(*) as cupons
#               ,sum(total) as movimento
#               ,sum(total)/count(*) as media
#               ,sum(iif(codigo_caixa = 999,total,0)) as acerto
#           FROM [DTMLOCAL].[dbo].[tb_fechamento_venda]
#           where codigo_tipo_movimento = 1
#               and codigo_cliente not in (55)
#               and codigo_movimento in (
#     """
#     sql_orderby_fechamento = """
#         )
#         group by codigo_movimento
#     """
#
#     sql_statement_especie = """
#           SELECT
#           e.codigo_especie,
#           sum(e.valor - e.valor_troco)
#           FROM [DTMLOCAL].[dbo].[tb_fechamento_venda] v,
#           [DTMLOCAL].[dbo].[tb_fechamento_especie] e
#           where v.codigo_venda = e.codigo_venda
#           and codigo_tipo_movimento = 1
#           and v.codigo_movimento in (
#         """
#     sql_orderby_especie = """
#             )
#             group by e.codigo_especie
#         """
#
#
#     sql_statement_cigarro = """
#         select COALESCE(sum(total), 0)  as valor
#         from (
#             SELECT
#                 f.total as total
#             FROM DTMLOCAL.dbo.tb_cad_produto p,
#               [DTMLOCAL].[dbo].[tb_cad_subgrupo] s,
#               [DTMLOCAL].[dbo].[tb_cad_grupo] g,
#               DTMLOCAL.dbo."tb_fechamento_produto" f
#               LEFT JOIN DTMLOCAL.dbo.tb_caderneta_consumo c
#               ON f.codigo_venda = c.codigo_venda
#             WHERE f.codigo_produto = p.codigo_produto
#             and s.codigo_subgrupo = p.codigo_subgrupo
#             and s.codigo_grupo = g.codigo_grupo
#             and f.data = %s
#             and f.hora > '1900-01-01 00:00'
#             and g.descricao = 'CIGARRO'
#         ) t
#     """
#     sql_statement_produto_proprio = """
#         select COALESCE(sum(total), 0)  as valor
#         from (
#             SELECT
#                 f.total as total
#             FROM DTMLOCAL.dbo.tb_cad_produto p,
#               DTMLOCAL.dbo."tb_fechamento_produto" f
#             WHERE f.codigo_produto = p.codigo_produto
# 			and p.codigo_tipo_produto = 3
#             and f.data = %s
#             and f.hora > '1900-01-01 00:00'
#         ) t
#     """
#     table_header = [
#         'Código',
#         'Cupom',
#         'Movimento',
#         'Média&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;&#xa0;',
#         'Acerto&#xa0;&#xa0;&#xa0;&#xa0;',
#         'Caixa',
#         'Usuário',
#         'Data',
#         "Início",
#         'Fim',
#     ]
