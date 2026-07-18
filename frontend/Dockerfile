# Production image for the Next.js frontend (standalone output).
# Build context is frontend/. Multi-arch (amd64/arm64) via buildx in CI.

FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -S argus && adduser -S argus -G argus
COPY --from=build --chown=argus:argus /app/.next/standalone ./
COPY --from=build --chown=argus:argus /app/.next/static ./.next/static
COPY --from=build --chown=argus:argus /app/public ./public
USER argus

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
    CMD wget -q --spider http://localhost:3000/ || exit 1

CMD ["node", "server.js"]
