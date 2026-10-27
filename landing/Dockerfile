FROM node:24-alpine AS build
WORKDIR /app
ARG NUXT_PUBLIC_CABINET_URL=http://localhost:3300
ENV NUXT_PUBLIC_CABINET_URL=$NUXT_PUBLIC_CABINET_URL
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run generate

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/.output/public /usr/share/nginx/html
EXPOSE 80
