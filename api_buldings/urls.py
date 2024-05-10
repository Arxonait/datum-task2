from django.urls import path, include
from rest_framework import routers

from api_buldings.views import BuildingViewSet

router = routers.SimpleRouter()
router.register(r"buildings", BuildingViewSet)


urlpatterns = [
    path("", include(router.urls), name="buildings"),
]