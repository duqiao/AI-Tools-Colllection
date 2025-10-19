# Use Node.js 18 LTS image
FROM node:18-alpine

# Set work directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S vueuser -u 1001

# Use development mode for hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3007"]