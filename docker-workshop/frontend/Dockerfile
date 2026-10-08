FROM node:24-alpine AS builder
WORKDIR /workshop/frontend
COPY vendor/workshop-front-end-components /workshop/vendor/workshop-front-end-components
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
COPY student/ /workshop/student/
COPY workbench/ /workshop/workbench/
ENV VUE_APP_BASE_PATH=/guide/
RUN npm test && npm run typecheck && npm run build
RUN node --test /workshop/workbench/tests/*.test.cjs

FROM nginx:alpine
COPY --from=builder /workshop/frontend/dist /usr/share/nginx/html/guide
COPY workbench/ /usr/share/nginx/html/
COPY docs/ /usr/share/nginx/html/docs/
COPY frontend/public/preview-not-started.html /usr/share/nginx/html/preview-not-started.html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
