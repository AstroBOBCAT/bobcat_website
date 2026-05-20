# BOBcat_utils
I was planning on incorporating some of gw_utils into here for testing. 
But I never got around to that.
Instead, this app (BOBcat_utils as a whole) serves as a location to run django commands.

Django commands are a feature which allow you to run scripts in your backend application while it is running. I use it to run sync_sheets.py.
By creating a management/commands/script.py in any app you can call them on your active session.

The command I use to run sync_sheets while it is running is
`docker compose exec backend python manage.py sync_sheets`
Lets break it down:
- docker: can only be used if docker is installed (and running as a service).
- compose: Indicates that docker is targeting a Docker Swarm. Because of this keyword, you must run this command on the same visibility as the docker-compose.yml
- exec: run a command in the target Docker component.  Imagine it like you are SSH'ing into a machine and then running a command there.
- backend: The docker component we are targeting, as named by the docker-compose.yml
- python: runs the python command in  the machine
- manage.py: The management script of the backend service. 
- sync_sheets: An argument given to manage.py that tells it what to do.

sync_sheets is designed to take data in Sheets -> requests -> pandas -> Django object -> PSQL Table
