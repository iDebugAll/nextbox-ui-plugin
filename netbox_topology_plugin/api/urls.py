from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.APIRootView = views.NetBoxTopologyPluginRootView

router.register(r'savedtopologies', views.SavedTopologyViewSet)

app_name = "netbox_topology_plugin-api"
urlpatterns = router.urls
