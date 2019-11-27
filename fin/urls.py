from django.urls import path
from django.views.generic.base import RedirectView
import locale

from . import views

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

app_name = 'fin'
urlpatterns = [
    path('', views.movimento, name='movimento'),
    path('sangria/', views.sangria, name='sangria'),
    path('produto/', views.produto, name='produto'),
    path('caderneta/', views.caderneta, name='caderneta'),
    path('comanda/', views.comanda, name='comanda'),
    path('movimento/', views.movimento, name='movimento'),
    path('fornecedor/', views.fornecedor, name='fornecedor'),
    path('boleto/', views.boleto, name='boleto'),
    path('boleto_data/', views.boleto_data, name='boleto_data'),
    path('sangria/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('produto/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('movimento/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('caderneta/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('comanda/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('fornecedor/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('boleto/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('boleto_data/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),

]