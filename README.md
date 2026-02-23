# library-service

API service for Library managment written with the help of DRF

## Installing
  ```bash
  git clone https://github.com/Konstantin-Svt/library-service.git
  cd library-service
  create .env file and populate it with your variables from .env.sample skeleton file (A mandatory one to start the app is only POSTGRES_PASSWORD)
  ```
  - Although you can set other enviroment variables, like ```POSTGRES_DB, DJANGO_SECRET_KEY, STRIPE_SECRET_KEY``` etc., a mandatory one is only ```POSTGRES_PASSWORD```. Others shall be default value if not specified.
  - Install and run Docker.
  ```bash
  docker-compose build
  docker-compose up
  ```
  - If you want to load some sample data:
  ```bash
  docker exec -it library-service-app-1 python manage.py loaddata fixtures/data.json
  ```
  - Create user at ```127.0.0.1:8000/api/users/``` or use default profile if you loaded sample data:
  ```bash
  admin:
    email: admin@admin.com
    password: admin

  default user:
    email: test@test.com
    password: tester12345
  ```
  - Documentation ```127.0.0.1:8000/api/schema/swagger-ui/```
  - Obtain JWT token at ```127.0.0.1:8000/api/users/token/```
  - Other API is available at ```127.0.0.1:8000/api/borrowings/``` or ```127.0.0.1:8000/api/books/``` or ```127.0.0.1:8000/api/payments/```
  - Implemented tasks 1-15 from https://docs.google.com/document/d/1wkWketx6ROKlrfpUqKJEJhS8EzVe3BOX (without "Coding Optional")