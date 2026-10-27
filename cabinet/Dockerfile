FROM node:24-alpine AS build
WORKDIR /app
ARG NUXT_PUBLIC_LANDING_URL=http://localhost:8080
ARG NUXT_PUBLIC_BOT_USERNAME=
ENV NUXT_PUBLIC_LANDING_URL=$NUXT_PUBLIC_LANDING_URL
ENV NUXT_PUBLIC_BOT_USERNAME=$NUXT_PUBLIC_BOT_USERNAME
COPY package*.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=80
COPY --from=build /app/.output ./.output
EXPOSE 80
CMD ["node", ".output/server/index.mjs"]
