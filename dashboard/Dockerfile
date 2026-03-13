FROM node:20-slim AS build

WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
ARG VITE_AGENT_A_URL=http://localhost:8001
ARG VITE_AGENT_B_URL=http://localhost:8002
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
