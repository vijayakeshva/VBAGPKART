from django.shortcuts import render

def home_view(request):
    return render(request, 'public/index.html')

def product_detail_view(request, pk):
    return render(request, 'public/product_detail.html')