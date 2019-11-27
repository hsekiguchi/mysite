from datetime import datetime, timedelta

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views import generic
from django.utils.dateparse import parse_date

from .models import Sangria, Produto, Caderneta, Comanda, Movimento, Fornecedor, BoletoData
from .models import BoletoFornecedor


# class IndexView(generic.ListView):
#     template_name = 'fin/index.html'
#     context_object_name = 'latest_question_list'
#
#     def get_queryset(self):
#         """Return the last five published questions."""
#         return Question.objects.order_by('-pub_date')[:5]
#
#
# class DetailView(generic.DetailView):
#     model = Question
#     template_name = 'fin/detail.html'
#
#
# class ResultsView(generic.DetailView):
#     model = Question
#     template_name = 'fin/results.html'
#
#
# def vote(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     try:
#         selected_choice = question.choice_set.get(pk=request.POST['choice'])
#     except (KeyError, Choice.DoesNotExist):
#         # Redisplay the question voting form.
#         return render(request, 'fin/detail.html', {
#             'question': question,
#             'error_message': "You didn't select a choice.",
#         })
#     else:
#         selected_choice.votes += 1
#         selected_choice.save()
#         # Always return an HttpResponseRedirect after successfully dealing
#         # with POST data. This prevents data from being posted twice if a
#         # user hits the Back button.
#         return HttpResponseRedirect(reverse('fin:results', args=(question.id,)))


def sangria(request):
    context = {'titulo': 'Sangria', 'find_date': True, 'view': 'fin:sangria' }

    data_ini_str = request.POST.get("data_ini","")
    if data_ini_str == "":
        data_ini=datetime.now()
    else:
        data_ini=parse_date(data_ini_str)

    submit_type = request.POST.get("submit","submit")
    if submit_type == "next":
        data_ini +=  timedelta(days=1)
    elif submit_type == "previous":
        data_ini -=  timedelta(days=1)

    data_ini_str = data_ini.strftime("%Y-%m-%d")
    context.update({'data_ini': data_ini_str,})

    if request.method == "POST":
        sg = Sangria()
        sangria_list = sg.load(data_ini_str)
        context.update(sangria_list)

    return render(request, 'fin/list.html', context)


def produto(request):
    context = {'titulo': 'Produto', 'find_text': True, 'view': 'fin:produto' }
    texto_pesquisa_str = request.POST.get("texto_pesquisa","")
    context.update({'texto_pesquisa': texto_pesquisa_str})
    if texto_pesquisa_str != "":
        try:
            codigo_produto = int(texto_pesquisa_str)
        except ValueError:
            codigo_produto = 0
        param = {'texto_pesquisa_str': texto_pesquisa_str, 'codigo_produto' : codigo_produto}
        p = Produto()
        produto_list = p.load(param)
        #context.update({'header': produto_list['header'], 'list': produto_list['data']})
        context.update(produto_list)
    return render(request, 'fin/list.html', context)

def caderneta(request):
    context = {'titulo': 'Caderneta', 'view': 'fin:caderneta' }
    codigo_cliente_str = request.POST.get("codigo_cliente","")
    context.update({'codigo_cliente': codigo_cliente_str})

    data_ini_str = request.POST.get("data_ini","")
    data_ini=parse_date(data_ini_str)
    context.update({'data_ini': data_ini_str})

    data_fim_str = request.POST.get("data_fim","")
    data_fim=parse_date(data_fim_str)
    context.update({'data_fim': data_fim_str})

    if codigo_cliente_str != "":
        c = Caderneta()
        context.update(c.load(codigo_cliente_str, data_ini.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d")))
    return render(request, 'fin/caderneta.html', context)

def comanda(request):
    context = {'titulo': 'Comanda', 'find_text': True, 'view': 'fin:comanda'  }
    texto_pesquisa_str = request.POST.get("texto_pesquisa","")
    context.update({'texto_pesquisa': texto_pesquisa_str})
    if texto_pesquisa_str != "":
        try:
            codigo_comanda = int(texto_pesquisa_str)
        except ValueError:
            codigo_comanda = 0
        codigo_comanda_str = '@' + str(codigo_comanda).zfill(4)
        p = Comanda()
        produto_list = p.load(codigo_comanda_str)
        context.update(produto_list)

    return render(request, 'fin/list.html', context)

def movimento(request):
    context = {'titulo': 'Movimento', 'find_date': True, 'view': 'fin:movimento' }

    data_ini_str = request.POST.get("data_ini","")
    if data_ini_str == "":
        data_ini=datetime.now()
    else:
        data_ini=parse_date(data_ini_str)

    submit_type = request.POST.get("submit","submit")
    if submit_type == "next":
        data_ini +=  timedelta(days=1)
    elif submit_type == "previous":
        data_ini -=  timedelta(days=1)

    data_ini_str = data_ini.strftime("%Y-%m-%d")
    context.update({'data_ini': data_ini_str,})

    if request.method == "POST":
        mv = Movimento()
        list = mv.load(data_ini_str)
        context.update(list)

    return render(request, 'fin/list.html', context)


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


def boleto(request):
    return_view = 'fin:boleto'
    context = {'titulo': 'Boleto', 'find_text': True, 'show_tot': True, 'view':  return_view}
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
    if codigo_cfd_str != "":
        try:
            codigo_cfd = int(codigo_cfd_str)
        except ValueError:
            codigo_cfd = 0
        param = {'codigo_cfd' : codigo_cfd}
        b = BoletoFornecedor()
        boleto_list = b.load(param)
        context.update(boleto_list)
    return render(request, 'fin/boleto.html', context)


def boleto_data(request):
    context = {'titulo': 'Boleto', 'find_date': True, 'show_tot': True, 'view': 'fin:boleto_data' }

    data_ini_str = request.POST.get("data_ini","")
    if data_ini_str == "":
        data_ini=datetime.now()
    else:
        data_ini=parse_date(data_ini_str)

    data_fim_str = request.POST.get("data_fim", "")
    if data_fim_str == "":
        data_fim = datetime.now()
    else:
        data_fim = parse_date(data_fim_str)

    submit_type = request.POST.get("submit","submit")
    if submit_type == "next":
        data_ini +=  timedelta(days=1)
        data_fim = data_ini
    elif submit_type == "previous":
        data_ini -=  timedelta(days=1)
        data_fim = data_ini

    data_ini_str = data_ini.strftime("%Y-%m-%d")
    data_fim_str = data_fim.strftime("%Y-%m-%d")
    context.update({'data_ini': data_ini_str,
                    'data_fim': data_fim_str,})

    if request.method == "POST":
        b = BoletoData()
        context.update(b.load(data_ini_str, data_fim_str))
    return render(request, 'fin/boleto.html', context)




