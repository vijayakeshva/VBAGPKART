from django.urls import path
from products.views import home_view, product_detail_view
urlpatterns = [
    path("", home_view),
    path("detail/<int:pk>/", product_detail_view),

]

