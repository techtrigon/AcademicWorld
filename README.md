# ACADEMICWORLD

Developed a robust REST API using Python's fastest Litestar framework with features like dependency injection, middlewares, and lifespan hooks.

Implemented JWT Cookie-based authentication with HS256 algorithm, single username/email login, SHA256 password hash ,data validations & Exception handlers.

Allowed Users to view colleges, courses, exams, academic details and filter various academic informations based on exams, rank, course fees, courses and various other parameters. 

Enabled Users to comment and reply, add items to lists, and like top-rated Colleges, Courses & Exams.

Empowered Admins with CRUD operations on all academic details, leveraging Dependency Injection, Middlewares, lazy-loading SQL relationships and Multiple SQL Joins 


**SETUP**

1- Install PgAdmin (Postgresql)

2- Go to db_connection.py and setup the database connection for configuration ⬇️

////CHANGE BASED ON UR SETUP

server_name = "postgres"
server_password = "1"
host_address = "localhost"
port = "5432"
database_name = "academicworld"

3- In main.py ⬇️ & RUN main.py

////CHANGE BASED ON UR SETUP
uvicorn.run(app="main:app", host="localhost", port=8080, reload=True)

4- Go to localhost:8080/schema/

