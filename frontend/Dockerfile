FROM node:20-slim AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

# The build output goes into /app/../backend/static/js/widgets/ per vite.config.js.
# In compose the backend's static volume is shared; the entrypoint just copies the
# built files into it so Django's collectstatic picks them up.
FROM alpine:3.19
COPY --from=builder /app/../backend/static/js/widgets /widgets
CMD ["sh", "-c", "cp -r /widgets /static/js/ && echo 'Frontend assets copied.'"]
