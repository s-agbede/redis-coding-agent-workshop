FROM node:24-alpine AS builder
WORKDIR /workshop/docker-workshop/frontend
COPY docker-workshop/vendor/workshop-front-end-components /workshop/docker-workshop/vendor/workshop-front-end-components
COPY docker-workshop/frontend/package.json docker-workshop/frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY docker-workshop/frontend/ ./
COPY agent.py /workshop/agent.py
COPY docker-workshop/workbench/ /workshop/docker-workshop/workbench/
ENV VUE_APP_BASE_PATH=/guide/
RUN npm test && npm run typecheck && npm run build
RUN node --test /workshop/docker-workshop/workbench/tests/*.test.cjs

FROM nginx:alpine
COPY --from=builder /workshop/docker-workshop/frontend/dist /usr/share/nginx/html/guide
COPY docker-workshop/workbench/ /usr/share/nginx/html/
COPY docker-workshop/docs/ /usr/share/nginx/html/docs/
COPY docker-workshop/frontend/public/preview-not-started.html /usr/share/nginx/html/preview-not-started.html
COPY docker-workshop/frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
