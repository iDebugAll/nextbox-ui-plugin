from django.urls import path
from . import views

urlpatterns = [
    path('topology/', views.TopologyView.as_view(), name='topology'),
]
