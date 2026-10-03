FROM node:20-alpine

WORKDIR /app

# Copy package descriptors first for Docker layer caching
COPY package.json package-lock.json* ./

# Install npm dependencies
RUN npm install

# Copy application source code
COPY . .

# Expose Vite development server port
EXPOSE 3000

# Start Vite in development mode binding to all interfaces
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
