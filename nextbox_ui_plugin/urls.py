from django.urls import path
from . import views

urlpatterns = [
    path('site_topology/<int:site_id>/', views.TopologyView.as_view(), name='site_topology'),
]
