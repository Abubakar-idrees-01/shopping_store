from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db.models import Sum, F
from django.db.models.signals import post_save

from django.contrib.auth.models import User


from .models import Product, Category, Wishlist, Review, Order, OrderItem
from .forms import ReviewForm, CheckoutForm


# -------------------------------
# Product List View
# -------------------------------
class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 8

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)

        # Search filter
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# -------------------------------
# Product Detail + Review
# -------------------------------
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all().order_by("-created_at")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "You need to log in to leave a review.")
            return redirect("login")
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Review added successfully!")
            return redirect("product_detail", slug=slug)
    else:
        form = ReviewForm()

    # ✅ Related products
    related_products = Product.objects.filter(
        category=product.category, is_active=True
    ).exclude(id=product.id)[:4]

    return render(request, "store/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "form": form,
        "related_products": related_products,
    })


# -------------------------------
# Wishlist
# -------------------------------
@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, "store/wishlist.html", {"wishlist": wishlist})


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.add(product)
    messages.success(request, f"{product.name} added to wishlist.")
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required
def remove_from_wishlist(request, product_id):
    wishlist = Wishlist.objects.get_or_create(user=request.user)[0]
    wishlist.products.remove(product_id)
    messages.info(request, "Product removed from wishlist.")
    return redirect("wishlist")


# -------------------------------
# Cart (session-based)
# -------------------------------
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except ValueError:
        quantity = 1

    if quantity < 1:
        quantity = 1
    if quantity > product.stock:
        messages.error(request, "Not enough stock available.")
        return redirect(request.META.get('HTTP_REFERER', 'product_list'))

    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity

    request.session['cart'] = cart
    messages.success(request, f"Added {quantity} x {product.name} to cart.")
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


def view_cart(request):
    cart = request.session.get('cart', {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, pk=product_id)

        # ✅ discounted price support
        price = product.discount_price if product.discount_price else product.price  
        subtotal = price * quantity
        total += subtotal

        products.append({
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
            'price': price,
        })

    return render(request, 'store/cart.html', {
        'cart_items': products,
        'total': total
    })


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
        messages.success(request, "Item removed from cart.")
    return redirect('view_cart')


# -------------------------------
# Checkout & Orders
# -------------------------------
@login_required
def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('product_list')

    cart_items = []
    total = 0

    # Build cart summary
    for product_id, quantity in cart.items():
        product = get_object_or_404(Product, pk=product_id)
        price = product.discount_price if product.discount_price else product.price
        subtotal = price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'price': price,
            'subtotal': subtotal,
        })

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data

            # ✅ Create order with all form fields
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                full_name=cd['full_name'],
                phone_number=cd['phone_number'],
                city=cd['city'],
                province=cd['province'],
                shipping_address=cd['shipping_address'],
                payment_method=cd['payment_method'],
                status="Pending",
                total_amount=0  # will update after items
            )

            # ✅ Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    price=item['price'],
                    quantity=item['quantity']
                )
                # reduce stock
                item['product'].stock -= item['quantity']
                item['product'].save()

            # ✅ Update total from cart
            order.total_amount = total
            order.save()

            # clear session cart
            request.session['cart'] = {}
            messages.success(request, f"Order #{order.id} placed successfully!")
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'store/checkout.html', {
        'form': form,
        'cart_items': cart_items,
        'total': total,
    })



@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})



# -------------------------------
# Auth (Register & My Orders)
# -------------------------------
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        # Validation
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required.")
            return redirect("login")

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect("login")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("login")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("login")

        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.save()

        # Auto-login new user
        login(request, user)
        messages.success(request, "Registration successful. You are now logged in.")
        return redirect("product_list")

    return redirect("login")  # fallback if GET request


@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})



@login_required
def profile_view(request):
    return render(request, "store/profile.html", {"user": request.user})