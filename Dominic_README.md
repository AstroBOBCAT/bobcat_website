# Dominic's readme
This branch represents the website inside of a docker container.
Docker containers provide deterministic repeatable environments that are good for debugging and development.
Usually these docker layers are shed once the project is deployed as they slow down the application.

I decided to use docker containers for this project primarily so that the Postgresql server did not run on my
local machine. Everything is neatly contained away from all of the rest of the projects I have on my device.


## How to use docker compose
All `docker compose` commands must be done on the same level as the docker-compose.yml file.

Starting the docker swarm:`docker compose up`

Starting the docker swarm after changing something: `docker compose up --build`

Starting the docker swarm as a background process: `docker compose up -d` or `docker compose up --build -d`

Stopping the docker swarm: `docker compose down` or CTRL-c

### Troubleshooting
Could not bind to port.  
Some of the docker container ports must be bound to an outside port.
If you have something running on one of those already, it cannot start. To fix this, either 
track down the running process or change the outside port of the specific container.

For example pgadmin's "8080:80" to "8081:80"in the docker-compose

## Other commands
Django syncs its models with the PSQL server through the use of migrations. These commands should suffice
unless you change a primary/foreign key or introduce a new table. 

Enumerate schema changes: `docker compose exec backend python manage.py makemigrations`

Apply schema changes: `docker compose exec backend python manage.py migrate`

Pull data from google sheets via sync_sheets: `docker compose exec backend python manage.py sync_sheets`

Enter psql server (use values in .dbinfo): `docker compose exec db psql -U <user> -d <database`

FULL HARD RESET psql server: `docker compose down --volumes`  
Remove broken migrations: `rm BOBcat_website/<app_name(usually mainpage)>/migrations/00*`  
Migrations are a record of changes you've made to models.py. If something weird is changed in models.py 
migrations will try to replicate that and store it in your history until you delete it.  
Then run the enumerate and apply schema commands: `see above`

## FAQ

I modified something and its not showing up when I run the docker compose?  
The docker compose needs to be rebuilt, run `docker compose up --build`

I closed my terminal and now it won't run?  
The old session might still be running. Try `docker compose down`

I added some new methods but it is giving me long python errors? It works locally.  
Update the requirements.txt file and then run `docker compose up --build` to apply the changes.

I changed one of the models.py and rebuilt it but the changes aren't applying?  
Run the `makemigrations and migrate` commands. Should apply your changes.

Same thing as above but I changed a foreign key, primary key, or added/removed a table. Migrations don't work.  
You can do FULL HARD RESET and then migrate. If you want to keep your data, strap in and find a good guide that is going to be a long ride.
