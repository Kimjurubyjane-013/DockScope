# ==============================================================================
# DockScope Frontend Multi-Stage Dockerfile
# ==============================================================================

# Build Stage
FROM node:22-alpine AS build

WORKDIR /app

COPY frontend/package.json ./
# Install dependencies
RUN npm install

COPY frontend/ ./
RUN npm run build

# Production Serving Stage
FROM nginx:alpine-slim AS production

# Create unprivileged directory configuration
COPY --from=build /app/dist /usr/share/nginx/html

# Custom internal Nginx configuration for SPA routing
RUN cat <<'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/javascript;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location = /healthz {
        access_log off;
        return 200 "healthy\n";
    }
}
EOF

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:80/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
