from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.dateparse import parse_date
from django.contrib.auth.decorators import login_required

from .models import Sangria, Produto, Caderneta, Comanda, Movimento, Fornecedor
from .models import BoletoData, BoletoFornecedor
from .models import Preco, PrecoCardapio

@login_required
def sangria(request):
    context = {'titulo': 'Sangria', 'find_date': True, 'show_tot': True, 'view': 'fin:sangria' }
    #if Post, check input, keep it in session and redirect
    if request.method == "POST":
        data_ini_str = request.POST.get("data_ini","")
        try:
            data_ini = parse_date(data_ini_str)
        except:
            data_ini = datetime.now()
        submit_type = request.POST.get("submit","submit")
        if submit_type == "next":
            data_ini +=  timedelta(days=1)
        elif submit_type == "previous":
            data_ini -=  timedelta(days=1)
        prg_last_data = {'view': context['view'], 'data_ini': data_ini.strftime("%Y-%m-%d"),}
        request.session['prg_last_data'] = prg_last_data
        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data',{})
    if len(prg_last_data) > 1 and prg_last_data.get('view', '') == context['view']:
        data_ini_str = prg_last_data['data_ini']
        del request.session['prg_last_data']

        if request.user.has_perm('fin.view_sangria'):
            sg = Sangria()
            sangria_list = sg.load(data_ini_str)
            context.update(sangria_list)
    else:
        data_ini = datetime.now()
        data_ini_str = data_ini.strftime("%Y-%m-%d")
    context.update({'data_ini': data_ini_str,})

    return render(request, 'fin/sangria.html', context)


@login_required
def produto(request):
    context = {'titulo': 'Produto', 'find_text': True, 'view': 'fin:produto' }

    if request.method == "POST":
        inclui_inativo = True if request.POST.get("checkbox_inativo","") == "S" else False
        texto_pesquisa_str = request.POST.get("texto_pesquisa", "")
        try:
            codigo_produto = int(texto_pesquisa_str)
        except ValueError:
            codigo_produto = 0
        prg_last_data =  {'view': context['view'], 'texto_pesquisa': texto_pesquisa_str,
                          'codigo_produto' : codigo_produto, 'inclui_inativo': inclui_inativo, }
        request.session['prg_last_data'] = prg_last_data
        request.session['inclui_inativo'] = inclui_inativo
        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data',{})
    if len(prg_last_data) > 1 and prg_last_data['view'] == context['view']:
        pass
    else:
        prg_last_data = {'inclui_inativo': request.session.get('inclui_inativo', False),
                         'texto_pesquisa': "",}
    p = Produto()
    produto_list = p.load(prg_last_data)
    context.update(produto_list)
    context.update(prg_last_data)

    return render(request, 'fin/list.html', context)


@login_required
def caderneta(request):
    context = {'titulo': 'Caderneta', 'view': 'fin:caderneta' }
    #if Post, check input, keep it in session and redirect
    if request.method == "POST":
        codigo_cliente_str = request.POST.get("codigo_cliente","")
        data_ini_str = request.POST.get("data_ini","")
        data_fim_str = request.POST.get("data_fim","")
        try:
            data_ini=parse_date(data_ini_str)
        except:
            data_ini = datetime.now()
        try:
            data_fim=parse_date(data_fim_str)
        except:
            data_fim = datetime.now()
        prg_last_data = {'view': context['view'], 'codigo_cliente': codigo_cliente_str,
                         'data_ini': data_ini.strftime("%Y-%m-%d"),
                         'data_fim': data_fim.strftime("%Y-%m-%d"),}
        request.session['prg_last_data'] = prg_last_data
        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data',{})
    if len(prg_last_data) > 1 and prg_last_data.get('view', '') == context['view']:
        del request.session['prg_last_data']
        c = Caderneta()
        caderneta_list = c.load(prg_last_data['codigo_cliente'],
                    prg_last_data['data_ini'], prg_last_data['data_fim'])
        context.update(caderneta_list)
        context.update(prg_last_data)

    return render(request, 'fin/caderneta.html', context)


def comanda(request):
    context = {'titulo': 'Comanda', 'find_text': True, 'view': 'fin:comanda'  }
    #if Post, check input, keep it in session and redirect
    if request.method == "POST":
        texto_pesquisa_str = request.POST.get("texto_pesquisa","")
        try:
            codigo_comanda = int(texto_pesquisa_str)
        except ValueError:
            codigo_comanda = 0
        prg_last_data = {'view': context['view'], 'codigo_comanda': codigo_comanda,
                         'texto_pesquisa': texto_pesquisa_str,}
        request.session['prg_last_data'] = prg_last_data
        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data', {})
    if len(prg_last_data) > 1 and prg_last_data.get('view', '') == context['view']:
        del request.session['prg_last_data']
        codigo_comanda_str = '@' + str(prg_last_data['codigo_comanda']).zfill(4)
        p = Comanda()
        produto_list = p.load(codigo_comanda_str)
        context.update(produto_list)
        context.update(prg_last_data)

    return render(request, 'fin/list.html', context)


@login_required
def movimento(request):
    context = {'titulo': 'Movimento', 'find_date': True, 'view': 'fin:movimento'}

    #if Post, check input, keep it in session and redirect
    if request.method == "POST":
        data_ini_str = request.POST.get("data_ini","")
        try:
            data_ini = parse_date(data_ini_str)
            if data_ini == None:
                raise Exception('Invalid date format.')
        except:
            data_ini = datetime.now()

        submit_type = request.POST.get("submit","submit")
        if submit_type == "next":
            data_ini +=  timedelta(days=1)
        elif submit_type == "previous":
            data_ini -=  timedelta(days=1)

        prg_last_data = {'view': context['view'], 'data_ini': data_ini.strftime("%Y-%m-%d"),}
        request.session['prg_last_data'] = prg_last_data

        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data',{})
    if len(prg_last_data) > 1 and prg_last_data['view'] == context['view']:
        data_ini_str = prg_last_data['data_ini']

        del request.session['prg_last_data']

        mv = Movimento()
        list = mv.load(data_ini_str)
        if list['caixas'] != '0':
            if not request.user.has_perm('fin.view_movimento_especie'):
                list['lista_especie'] = []
            context.update(list)
    else:
        data_ini = datetime.now()
        data_ini_str = data_ini.strftime("%Y-%m-%d")

    context.update({'data_ini': data_ini_str,})

    return render(request, 'fin/movimento.html', context)


@login_required
def fornecedor(request):
    context = {'titulo': 'Fornecedor', 'find_text': True, 'view': 'fin:fornecedor' }
    if request.method == "POST":
        texto_pesquisa_str = request.POST.get("texto_pesquisa","")
        return_view = request.POST.get("return_view", "fin:fornecedor")
    else:
        texto_pesquisa_str = request.GET.get("texto_pesquisa","")
        return_view = request.GET.get("return_view", "fin:fornecedor")
    context.update({'texto_pesquisa': texto_pesquisa_str, 'return_view': return_view})
    if texto_pesquisa_str != "":
        try:
            codigo_fornecedor = int(texto_pesquisa_str)
        except ValueError:
            codigo_fornecedor = 0
        param = {'texto_pesquisa': texto_pesquisa_str, 'codigo_cfd' : codigo_fornecedor}
        p = Fornecedor()
        fornecedor_list = p.load(param)
        if len(fornecedor_list['list']) == 1:
            param['codigo_cfd'] = fornecedor_list['list'][0][0]
            base_url = reverse('fin:boleto')
            query_string = urlencode(param)
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
        #context.update({'header': produto_list['header'], 'list': produto_list['data']})
        context.update(fornecedor_list)
    return render(request, 'fin/list_select.html', context)



@login_required
def boleto(request):
    return_view = 'fin:boleto'
    context = {'titulo': 'Boleto', 'find_text': True, 'show_tot': True, 'view':  return_view}

    if request.method == "POST":
        inclui_baixado = True if request.POST.get("checkbox_baixado","") == "1" else False
    elif 'inclui_baixado' in request.session:
        inclui_baixado = request.session['inclui_baixado']
    else:
        inclui_baixado = False
    request.session['inclui_baixado'] = inclui_baixado

    if request.method == "POST":
        texto_pesquisa_str = request.POST.get("texto_pesquisa","")
        #obter o código do fornecedor da pesquisa anterior
        codigo_cfd_str = request.POST.get("codigo_cfd_str","")
        #se o texto_pesquisa for diferente do fornecedor anteriormente pequisado
        if texto_pesquisa_str != "" and texto_pesquisa_str != codigo_cfd_str:
            base_url = reverse('fin:fornecedor')
            query_string = urlencode({'texto_pesquisa': texto_pesquisa_str, 'return_view': return_view})
            url = '{}?{}'.format(base_url, query_string)
            return redirect(url)
    else:
        codigo_cfd_str = request.GET.get("codigo_cfd","")
        texto_pesquisa_str = codigo_cfd_str
    context.update({'texto_pesquisa': texto_pesquisa_str, 'codigo_cfd': codigo_cfd_str,})

    try:
        codigo_cfd = int(codigo_cfd_str)
    except ValueError:
        codigo_cfd = 0
    param = {'codigo_cfd' : codigo_cfd, 'inclui_baixado': inclui_baixado, }

    b = BoletoFornecedor()
    boleto_list = b.load(param)
    context.update(boleto_list)
    return render(request, 'fin/boleto.html', context)


@login_required
def boleto_data(request):
    context = {'titulo': 'Boleto', 'find_date': True, 'show_tot': True, 'view': 'fin:boleto_data' }

    if request.method == "POST":
        data_ini_str = request.POST.get("data_ini", "")
        try:
            data_ini=parse_date(data_ini_str)
            if data_ini == None:
                raise Exception('Invalid date format.')
        except:
            data_ini = datetime.now()

        data_fim_str = request.POST.get("data_fim", "")
        try:
            data_fim = parse_date(data_fim_str)
            if data_fim == None:
                raise Exception('Invalid date format.')
        except:
            data_fim = datetime.now()

        submit_type = request.POST.get("submit", "submit")
        if submit_type == "next":
            data_fim +=  timedelta(days=1)
            data_ini = data_fim
        elif submit_type == "previous":
            data_ini -=  timedelta(days=1)
            data_fim = data_ini

        prg_last_data = {'view': context['view'],
                         'data_ini': data_ini.strftime("%Y-%m-%d"), 'data_fim': data_fim.strftime("%Y-%m-%d"), }
        request.session['prg_last_data'] = prg_last_data
        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data',{})
    if len(prg_last_data) > 1 and prg_last_data['view'] == context['view']:
        data_ini_str = prg_last_data['data_ini']
        data_fim_str = prg_last_data['data_fim']
        del request.session['prg_last_data']

        b = BoletoData()
        context.update(b.load(data_ini_str, data_fim_str))
    else:
        data_ini_str = datetime.now().strftime("%Y-%m-%d")
        data_fim_str = datetime.now().strftime("%Y-%m-%d")

    context.update({'data_ini': data_ini_str,
                    'data_fim': data_fim_str,})

    return render(request, 'fin/boleto.html', context)

@login_required
def produto_atualizar_cardapio(request):
    context = {'titulo': 'Atualiza Cardápio', 'view': 'fin:atualiza_cardapio' }

    if request.method == "POST":
        submit_type = request.POST.get("submit", "submit")
        if submit_type == "submit":
            p = Preco()
            lista_preco_novo = p.load()
            request.session['lista_preco_novo'] = lista_preco_novo

        elif submit_type == "update":
            if 'lista_preco_novo' in request.session:
                lista_preco_novo = request.session['lista_preco_novo']
                pc = PrecoCardapio()
                pc.update(lista_preco_novo)
                request.session['cardapio_atualizado'] = True
        return redirect(context['view'])

    lista = []
    if 'lista_preco_novo' in request.session:
        # [0] código, [1] preço
        pc = PrecoCardapio()
        lista_preco_cardapio = pc.load()
        lista_cardapio = lista_preco_cardapio['list']

        # [0] código, [1] descrição, [2] preço
        lista_preco_novo = request.session['lista_preco_novo']

        linha = 0
        maxlinha = len(lista_cardapio)
        for linha_nova in lista_preco_novo['list']:
            if linha >= maxlinha:
                break
            if linha_nova[0] < int(lista_cardapio[linha][0]):
                continue
            while linha_nova[0] > int(lista_cardapio[linha][0]):
                lista.append([lista_cardapio[linha][0], 'Inativo', linha_nova[2], '-', '-', lista_cardapio[linha][4]])
                linha += 1
            if linha_nova[0] == int(lista_cardapio[linha][0]):
                if linha_nova[4] != lista_cardapio[linha][4]:
                    lista.append([linha_nova[0], linha_nova[1], linha_nova[2], linha_nova[3], linha_nova[4], lista_cardapio[linha][4]])
                linha += 1


        table = {'timestamp' : lista_preco_cardapio['timestamp'],
                 'header': lista_preco_novo['header'],
                 'list': lista}
        context.update(table)

    #se o cardápio foi atualizado ou se não houve alteração no preço, não mudar mais nada
    if 'cardapio_atualizado' in request.session or len(lista) == 0:
        if 'lista_preco_novo' in request.session:
            del request.session['lista_preco_novo']
        if 'cardapio_atualizado' in request.session:
            del request.session['cardapio_atualizado']

    return render(request, 'fin/atualiza_cardapio.html', context)

@login_required
def produto_desatualizado(request):
    context = {'titulo': 'Produto Desatualizado', 'find_date': True, 'view': 'fin:produto_desatualizado'}

    #if Post, check input, keep it in session and redirect
    if request.method == "POST":
        data_ini_str = request.POST.get("data_ini","")
        try:
            data_ini = parse_date(data_ini_str)
            if data_ini == None:
                raise Exception('Invalid date format.')
        except:
            data_ini = datetime.now()

        submit_type = request.POST.get("submit","submit")
        if submit_type == "next":
            data_ini +=  timedelta(days=1)
        elif submit_type == "previous":
            data_ini -=  timedelta(days=1)

        prg_last_data = {'view': context['view'], 'data_ini': data_ini.strftime("%Y-%m-%d"),}
        request.session['prg_last_data'] = prg_last_data

        return redirect(context['view'])

    prg_last_data = request.session.get('prg_last_data',{})
    if len(prg_last_data) > 1 and prg_last_data['view'] == context['view']:
        data_ini_str = prg_last_data['data_ini']
        del request.session['prg_last_data']

        # pc.load deverá receber data_ini_str + 1 para incluir todos os horários desta data
        # se data_ini_str = 04/08, para incluir todos os horários desta data, usa-se a condição
        # data < 05/08, caso contrário, data <= 04/08, só irá retornar as datas menores ou iguais
        # a 04/08 00:00
        data_ini = parse_date(data_ini_str)
        data_ini += timedelta(days=1)

        pc = Preco()
        list = pc.load(data_ini.strftime("%Y-%m-%d"))
        context.update(list)
    else:
        data_ini = datetime.now()
        data_ini_str = data_ini.strftime("%Y-%m-%d")

    context.update({'data_ini': data_ini_str,})

    return render(request, 'fin/list.html', context)