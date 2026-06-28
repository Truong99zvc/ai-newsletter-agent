# ==============================================================================
# Multi-stage Dockerfile for React + Vite Frontend
# ==============================================================================

# Build stage: Install dependencies and compile Vite build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files
COPY package.json ./

# Install packages
RUN npm install

# Copy source code
COPY . .

# Compile application
RUN npm run build

# Production stage: Serve compiled HTML/JS/CSS assets via Nginx
FROM nginx:alpine AS runner

# Copy customized Nginx configuration to support SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
