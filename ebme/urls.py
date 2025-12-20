"""
URL configuration for ebme project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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


from django.conf import settings
from django.conf.urls.static import static

# home page
from dashboard.views import DashboardTemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("assets/", include("assets.urls")),
    path("jobs/", include("jobs.urls")),
    path("users/", include("users.urls")),
    path("model_information/", include("model_information.urls")),
    path("documents/", include("documents.urls")),
    path("dashboards/", include("dashboard.urls")),
    path("parts/", include("parts.urls")),
    path('select2/', include('django_select2.urls')),
    path("procurement/", include('procurement.urls')),
    # set home page
    path('', DashboardTemplateView.as_view(), name='home')
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
