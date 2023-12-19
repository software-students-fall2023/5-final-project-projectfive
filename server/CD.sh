# Stops, updates, and restarts docker compose.
# This script is triggered by the CD pipeline.

wget "https://raw.githubusercontent.com/software-students-fall2023/5-final-project-projectfive/main/compose.yaml"
docker compose down
docker compose pull
docker compose --env-file="certs/.env" up -d