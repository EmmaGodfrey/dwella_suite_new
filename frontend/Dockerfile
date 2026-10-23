FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_APP_NAME="Dwella Suite"
ARG VITE_API_BASE_URL
ARG VITE_BASE_PATH="/"
ARG VITE_HANDY_AGENT_ENABLED="false"
ENV VITE_APP_NAME=${VITE_APP_NAME} \
    VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_BASE_PATH=${VITE_BASE_PATH} \
    VITE_HANDY_AGENT_ENABLED=${VITE_HANDY_AGENT_ENABLED}

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

