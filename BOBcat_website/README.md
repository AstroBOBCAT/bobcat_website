# backend
This is the folder where the backend ticks. All of the django apps are here.

Important files:
- Dockerfile: Dictates how the service is booted up in the Docker Swarm. (shouldn't need any changes until deployment)
- requirements.txt: The necessary packages pip needs to install when the backend runs.
- manage.py: The entrypoint and how the backend runs.
- 