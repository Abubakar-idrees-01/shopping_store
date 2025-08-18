from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from .models import OrderItem, Product,Order

@staff_member_required
def admin_dashboard(request):
    # Sales statistics
    total_orders = Order.objects.count()
    total_revenue = OrderItem.objects.aggregate(total=Sum('price'))['total'] or 0
    orders_by_status = Order.objects.values('status').annotate(count=Count('id'))

    # Low stock products (less than 5 in stock)
    low_stock_products = Product.objects.filter(stock__lt=5)

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'orders_by_status': orders_by_status,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'store/admin_dashboard.html', context)



