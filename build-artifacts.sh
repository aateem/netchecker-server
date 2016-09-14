#!/bin/sh
set -e
set -x

DOCKER_REPO="${DOCKER_REPO:-$DOCKER_REGISTRY}"
BUILD_IMAGE="mcp-netchecker-server/build"
BUILD_IMAGE_TAG="${BUILD_IMAGE_TAG:-$NETCHECKER_VER}"
BUILD=`git rev-parse --short HEAD`

NAME="${DOCKER_REPO}/${BUILD_IMAGE}:${BUILD_IMAGE_TAG}"

echo "Building images"
docker build -t ${NAME}-${BUILD} .

echo "Pushing images"
set +x
docker login -u "${ARTIFACTORY_LOGIN}" -p "${ARTIFACTORY_PASSWORD}" \
  -e "${ARTIFACTORY_USER_EMAIL}" "${DOCKER_REGISTRY}"
set -x
docker push ${NAME}-${BUILD}
