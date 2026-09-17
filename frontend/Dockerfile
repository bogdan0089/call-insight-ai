# Next in standalone mode: the build emits a server plus only the packages it
# actually imports, so the runtime image carries no node_modules tree.
#
# NEXT_PUBLIC_API_URL is a build argument, not a runtime variable -- Next inlines
# every NEXT_PUBLIC_* value into the browser bundle at build time. Changing the
# API address means rebuilding this image.

FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG NEXT_PUBLIC_API_URL=http://localhost:8090
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:22-alpine AS runtime

WORKDIR /app
ENV NODE_ENV=production PORT=3100 HOSTNAME=0.0.0.0

COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static

EXPOSE 3100

CMD ["node", "server.js"]
