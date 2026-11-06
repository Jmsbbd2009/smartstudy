FROM node:22-alpine AS build
WORKDIR /web
COPY admin-web/package*.json ./
RUN npm ci
COPY admin-web/ ./
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build
FROM nginxinc/nginx-unprivileged:1.28-alpine
COPY infrastructure/deployment/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 8080
