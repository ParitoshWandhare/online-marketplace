# STAGE 1: Build the React application
# We use a specific version of Node.js for consistency. 'alpine' is a lightweight version.
FROM node:20-alpine AS build

# Set the working directory inside the container.
WORKDIR /app

# Copy 'package.json' and 'package-lock.json' first to take advantage of Docker's caching.
# This step will only be re-run if these files change.
COPY package*.json ./

# Install all the project dependencies.
RUN npm install

# Copy the rest of your application's source code into the container.
COPY . .

# Run the build script defined in your package.json (e.g., for Vite/Create React App).
# This creates a static, optimized version of your site in the '/app/dist' folder.
RUN npm run build

# STAGE 2: Serve the application with Nginx
# Nginx is a lightweight, high-performance web server.
FROM nginx:stable-alpine

# Copy the static build files from the 'build' stage to Nginx's public web directory.
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80. Nginx listens on this port by default inside the container.
EXPOSE 80

# The default command for the Nginx image is to start the server.
# This line ensures it runs in the foreground, which is necessary for Docker.
CMD ["nginx", "-g", "daemon off;"]

