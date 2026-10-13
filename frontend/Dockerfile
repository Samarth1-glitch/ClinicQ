# ---- Stage 1: build the React app with Node ----
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# ---- Stage 2: serve the static files with unprivileged Nginx ----
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

# Where /api/* is proxied to (override in compose / Kubernetes)
ENV BACKEND_URL=http://backend:8000

# nginx-unprivileged already runs as this non-root user; stated explicitly for clarity
USER 101
EXPOSE 8080
