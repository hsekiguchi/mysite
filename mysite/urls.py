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
    path('a1ecc3b826d01251edddf29c3e4e1e97.woff',
         RedirectView.as_view(url='/static/fin/a1ecc3b826d01251edddf29c3e4e1e97.woff', permanent=True), name='woff'),
    path('favicon.ico',
         RedirectView.as_view(url='/static/favicon.ico', ), name='favicon'),
    path('android-chrome-192x192.png',
         RedirectView.as_view(url='/static/android-chrome-192x192.png', ), name='android-chrome-192x192'),
    path('android-chrome-512x512.png',
         RedirectView.as_view(url='/static/android-chrome-512x512.png', ), name='android-chrome-512x512'),
    path('apple-touch-icon.png',
         RedirectView.as_view(url='/static/apple-touch-icon.png', ), name='apple-touch-icon'),
    path('browserconfig.xml',
         RedirectView.as_view(url='/static/browserconfig.xml', ), name='browserconfig'),
    path('favicon-16x16.png',
         RedirectView.as_view(url='/static/favicon-16x16.png', ), name='favicon-16x16'),
    path('favicon-32x32.png',
         RedirectView.as_view(url='/static/favicon-32x32.png', ), name='favicon-32x32'),
    path('mstile-70x70.png',
         RedirectView.as_view(url='/static/mstile-70x70.png', ), name='mstile-70x70'),
    path('mstile-144x144.png',
         RedirectView.as_view(url='/static/mstile-144x144.png', ), name='mstile-144x144'),
    path('mstile-150x150.png',
         RedirectView.as_view(url='/static/mstile-150x150.png', ), name='mstile-150x150'),
    path('mstile-310x150.png',
         RedirectView.as_view(url='/static/mstile-310x150.png', ), name='mstile-310x150'),
    path('mstile-310x310.png',
         RedirectView.as_view(url='/static/mstile-310x310.png', ), name='mstile-310x310'),
    path('safari-pinned-tab.svg',
         RedirectView.as_view(url='/static/safari-pinned-tab.svg', ), name='safari-pinned-tab'),
    path('site.webmanifest',
         RedirectView.as_view(url='/static/site.webmanifest', ), name='site.webmanifest'),
]
