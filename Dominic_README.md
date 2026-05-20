# Dominic's readme
## Docker introduction
When people started developing applications (especially websites) they ran into the issue of 
establishing the same environment in multiple locations. Docker containers solved this issue by providing 
easily deployable, repeatable, and deterministic environments. As these containers became more popular, 
people began using many containers at once. So Docker created Docker Swarms, collections of related containers
that could be booted up and down in unison. This swarm of container(s) is dictated by the 
docker-compose.yml which dictates the services and their relationship with each other.

I am using one such docker swarm which has a service for the PSQL server as well as one for the backend service.
There is also pgadmin which I couldn't figure out how to get to work. But you might find it useful.

## How to use docker compose
All commands must be done on the same level as the docker-compose.yml file.

Starting the docker swarm:`docker compose up`

Starting the docker swarm after changing something: `docker compose up --build`

Starting the docker swarm as a background process: `docker compose up -d` or `docker compose up --build -d`

Stopping the docker swarm: `docker compose down` or CTRL-c

## Other commands
Django syncs its models with the PSQL server through the use of migrations. These commands should suffice
unless you change a primary/foreign key or introduce a new table. 

Enumerate schema changes: `docker compose exec backend python manage.py makemigrations`

Apply schema changes: `docker compose exec backend python manage.py migrate`

Pull data from google sheets via sync_sheets: `docker compose exec backend python manage.py sync_sheets`