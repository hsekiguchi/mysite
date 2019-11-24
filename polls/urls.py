from django.urls import path
from django.views.generic.base import RedirectView

from . import views

app_name = 'polls'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),
    path('sangria/', views.sangria, name='sangria'),
    path('produto/', views.produto, name='produto'),
    path('caderneta/', views.caderneta, name='caderneta'),
    path('comanda/', views.comanda, name='comanda'),
    path('movimento/', views.movimento, name='movimento'),
    path('fornecedor/', views.fornecedor, name='fornecedor'),
    path('boleto/', views.boleto, name='boleto'),
    path('sangria/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('produto/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('movimento/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('caderneta/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('comanda/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('fornecedor/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('boleto/a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/polls/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),

]