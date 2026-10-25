FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_APP_NAME="Dwella Suite"
ARG VITE_API_BASE_URL
ARG VITE_BASE_PATH="/"
ARG VITE_HANDY_AGENT_ENABLED="false"
ARG VITE_HANDY_AGENT_URL=""
ENV VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_BASE_PATH=${VITE_BASE_PATH} \
    VITE_HANDY_AGENT_ENABLED=${VITE_HANDY_AGENT_ENABLED} \
    VITE_HANDY_AGENT_URL=${VITE_HANDY_AGENT_URL}

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine

ENV MEDIA_CSP_ORIGIN=""
COPY frontend/nginx.conf /etc/nginx/templates/default.conf.template
COPY --chmod=755 deploy/15-validate-media-origin.sh /docker-entrypoint.d/15-validate-media-origin.sh
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

