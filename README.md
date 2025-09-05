
# Billing System

A Django-based billing system with products, purchases, and cash denominations. The project uses PostgreSQL as the database and runs inside Docker.

## Features

* Manage products with stock and pricing
* Record purchases and calculate totals, taxes, and balances
* Handle cash denominations and change
* UUID-based product IDs
* Dockerized setup for easy deployment

## Requirements

* Docker
* Docker Compose

## Project Structure

billing\_system/
├── billing/                 # App containing models, views, migrations
├── billing\_system/          # Project settings and URLs
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── manage.py

## Setup Instructions

1. **Clone the repository**

```
git clone https://github.com/Rakeshlalkn/billing-system.git
cd billing-system
```

2. **Build Docker containers**

```
docker-compose build
```

3. **Start Docker containers**

```
docker-compose up -d
```

* This will start **web (Django)** and **db (PostgreSQL)** containers.

4. **Apply migrations**

```
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
```


5. **Create a superuser (optional)**

```
docker-compose exec web python manage.py createsuperuser
```

* This allows access to the Django admin panel.

6. **Run the development server**

```
docker-compose exec web python manage.py runserver 0.0.0.0:8000
```

* Access the app at: `http://localhost:8000/`
* Access the admin at: `http://localhost:8000/admin/`

7. **Stop containers**

```
docker-compose down
```

## Troubleshooting

* **`AttributeError: module 'billing.views' has no attribute 'add_product'`**
  Make sure `billing/views.py` contains the `add_product` view:

```
from django.shortcuts import render

def add_product(request):
    return render(request, 'billing/add_product.html')
```

* **Database migration issues (`value too long`)**
  Update the column type in PostgreSQL or adjust the model `max_length` to match existing data.

## Useful Docker Commands

| Command                        | Description                       |
| ------------------------------ | --------------------------------- |
| `docker-compose ps`            | List running containers           |
| `docker-compose logs -f`       | View container logs               |
| `docker-compose exec web bash` | Open a shell in the web container |

## License

This project is open-source and free to use under the MIT License.