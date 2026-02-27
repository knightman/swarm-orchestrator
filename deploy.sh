#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${SCRIPT_DIR}/.env" ]]; then
    set -a; source "${SCRIPT_DIR}/.env"; set +a
fi

MANAGER_HOST="${SWARM_MANAGER_SSH:?Set SWARM_MANAGER_SSH in .env (e.g. user@manager-node)}"
REGISTRY="${REGISTRY_HOST:?Set REGISTRY_HOST in .env (e.g. 192.168.1.100:5000)}"
IMAGE="${REGISTRY}/swarm-orchestrator:latest"
STACK_NAME="orchestrator"
COMPOSE_FILE="docker-compose.prod.yml"
REMOTE_COMPOSE="~/swarm-orchestrator-stack.yml"

usage() {
    cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  build       Build and push the image to the private registry
  deploy      Copy compose file and deploy the stack
  update      Force-update the running service (after a new image push)
  redeploy    Build, push, and full redeploy (remove + deploy)
  remove      Remove the stack from the swarm
  stop        Stop the service (scale to 0)
  start       Start the service (scale to 1)
  logs        Tail logs from the running service
  status      Show service status on the swarm
EOF
    exit 1
}

build() {
    echo "==> Building and pushing image: ${IMAGE}"
    docker buildx build --platform linux/amd64 -t "${IMAGE}" --push .
    echo "==> Image pushed successfully"
}

deploy() {
    echo "==> Copying ${COMPOSE_FILE} to ${MANAGER_HOST}"
    scp "${COMPOSE_FILE}" "${MANAGER_HOST}:${REMOTE_COMPOSE}"
    echo "==> Deploying stack '${STACK_NAME}'"
    ssh "${MANAGER_HOST}" "docker stack deploy -c ${REMOTE_COMPOSE} ${STACK_NAME}"
    echo "==> Stack deployed"
}

update() {
    echo "==> Updating service ${STACK_NAME}_app to latest image"
    ssh "${MANAGER_HOST}" "docker service update --force --image ${IMAGE} ${STACK_NAME}_app"
    echo "==> Service updated"
}

remove() {
    echo "==> Removing stack '${STACK_NAME}'"
    ssh "${MANAGER_HOST}" "docker stack rm ${STACK_NAME}"
    echo "==> Stack removed"
}

stop_service() {
    echo "==> Scaling ${STACK_NAME}_app to 0"
    ssh "${MANAGER_HOST}" "docker service scale ${STACK_NAME}_app=0"
    echo "==> Service stopped"
}

start_service() {
    echo "==> Scaling ${STACK_NAME}_app to 1"
    ssh "${MANAGER_HOST}" "docker service scale ${STACK_NAME}_app=1"
    echo "==> Service started"
}

logs() {
    echo "==> Tailing logs for ${STACK_NAME}_app"
    ssh "${MANAGER_HOST}" "docker service logs -f --tail 100 ${STACK_NAME}_app"
}

status() {
    echo "==> Stack services:"
    ssh "${MANAGER_HOST}" "docker stack services ${STACK_NAME}"
    echo ""
    echo "==> Service tasks:"
    ssh "${MANAGER_HOST}" "docker service ps ${STACK_NAME}_app"
}

redeploy() {
    build
    echo "==> Removing stack for full redeploy..."
    ssh "${MANAGER_HOST}" "docker stack rm ${STACK_NAME}"
    echo "==> Waiting for cleanup..."
    sleep 5
    deploy
}

[[ $# -lt 1 ]] && usage

case "$1" in
    build)      build ;;
    deploy)     deploy ;;
    update)     update ;;
    redeploy)   redeploy ;;
    remove)     remove ;;
    stop)       stop_service ;;
    start)      start_service ;;
    logs)       logs ;;
    status)     status ;;
    *)          usage ;;
esac
