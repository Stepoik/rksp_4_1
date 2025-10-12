FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create logs directory
RUN mkdir -p /var/log/nginx

# Create directories for custom configurations
RUN mkdir -p /etc/nginx/conf.d
RUN mkdir -p /etc/nginx/snippets

# Install additional tools for debugging (optional)
RUN apk add --no-cache curl

# Expose ports
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
