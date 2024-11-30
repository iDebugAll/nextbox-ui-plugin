from django.urls import path
from . import views

urlpatterns = [
    path('site_topology/', views.SiteTopologyView.as_view(), name='site_topology'),
    path('topology/', views.TopologyView.as_view(), name='topology'),
]
