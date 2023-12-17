# Stops, updates, and restarts docker compose.
# This script is triggered by the CD pipeline.

curl https://github.com/software-students-fall2023/5-final-project-projectfive/blob/main/compose.yaml compose.yaml
docker compose down
docker compose pull
docker compose --env-file="certs/.env" up -d