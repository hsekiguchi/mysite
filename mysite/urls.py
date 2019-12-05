"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from fin import views

urlpatterns = [
    path('fin/', include('fin.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.movimento, name='movimento'),
    path('favicon.ico',
         RedirectView.as_view(url='/static/favicon.ico', ), name='woff'),
    path('a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),

]
