# 🛒 Django Shopping Store

A full-featured **e-commerce web application** built with Django.
It includes product browsing, cart & wishlist management, order processing, user authentication, reviews, and a custom admin dashboard.

---

## 📌 Features

* 👤 **User Authentication**

  * Login, logout, signup
  * Profile page
  * Session-based cart

* 🛍 **Product Management**

  * Categories & product listing
  * Product details with reviews
  * Search and filter functionality

* ❤️ **Wishlist**

  * Save favorite products
  * Remove when desired

* 🛒 **Shopping Cart & Checkout**

  * Add/remove items
  * Checkout form with shipping info
  * Order success page

* ⭐ **Reviews**

  * Submit and view product reviews

* 📊 **Custom Admin Dashboard**

  * Total orders & revenue
  * Orders by status
  * Low-stock product alerts

* ⚠️ **Error Pages**

  * Custom 404 (Not Found)
  * Custom 500 (Server Error)

---

## 📂 Project Structure

```
myshop/                # Django project settings
store/                 # Main e-commerce application
templates/             # Global templates (base, 404, 500)
static/                # CSS, JS, images
manage.py              # Django management script
requirements.txt       # Project dependencies
```

### Key Files

* **`myshop/settings.py`** – Project configuration
* **`myshop/urls.py`** – Root URL configuration + error handlers
* **`store/models.py`** – Database models (Products, Orders, Wishlist, Reviews)
* **`store/views.py`** – Business logic (product listing, cart, wishlist, orders)
* **`store/forms.py`** – Forms (checkout, reviews, signup)
* **`store/admin_views.py`** – Custom admin dashboard logic
* **`templates/base.html`** – Global layout with navbar & footer
* **`templates/404.html`** – Custom 404 error page
* **`templates/500.html`** – Custom 500 error page

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/shopping-store.git
cd shopping-store
2️⃣ Create Virtual Environment
bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
3️⃣ Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
4️⃣ Apply Migrations
bash
Copy
Edit
python manage.py migrate
5️⃣ Create Superuser (Admin)
To access the Django Admin Dashboard, you’ll need an admin account. Run:

bash
Copy
Edit
python manage.py createsuperuser
Follow the prompts (username, email, and password).
You can then log in at 👉 http://127.0.0.1:8000/admin/

6️⃣ Run Development Server
bash
Copy
Edit
python manage.py runserver
Now visit 👉 http://127.0.0.1:8000/
---

## 🎨 Screenshots

| Home Page                          | Product Detail                         | Cart                               |
| ---------------------------------- | -------------------------------------- | ---------------------------------- |
| ![Home](docs/screenshots/home.png) | ![Detail](docs/screenshots/detail.png) | ![Cart](docs/screenshots/cart.png) |

---

## 📊 Admin Dashboard

* View **total orders & revenue**
* Orders by **status** (pending, shipped, delivered)
* Low-stock product alerts

Accessible at 👉 `/admin-dashboard/` (staff only)

---

## 📦 Deployment

1. Collect static files:

```bash
python manage.py collectstatic
```

2. Set `DEBUG = False` in `myshop/settings.py`
3. Add your domain in `ALLOWED_HOSTS`
4. Deploy on services like **Heroku, PythonAnywhere, or Docker**

---

## 🤝 Contributing

Pull requests are welcome!
For major changes, open an issue first to discuss what you’d like to change.

---

## 📜 License

This project is licensed under the **MIT License** – free to use and modify.

---

✨ Built with ❤️ using Django 5.2.5

