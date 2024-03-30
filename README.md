# Build

docker compose -f deploy/docker-compose.yml --project-directory . build

# Push

docker compose -f deploy/docker-compose.yml --project-directory . push

# Run

TGBOT_TOKEN="YOUR_TOKEN_HERE" TGBOT_ADMIN_USERNAME="YOUR_USERNAME_HERE" docker compose -f deploy/docker-compose.yml --project-directory . up
