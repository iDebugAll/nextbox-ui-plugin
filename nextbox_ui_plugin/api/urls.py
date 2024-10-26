from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.APIRootView = views.NextBoxUIPluginRootView

app_name = "nextbox_ui_plugin-api"
urlpatterns = router.urls
