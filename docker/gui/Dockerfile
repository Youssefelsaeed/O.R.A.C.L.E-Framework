FROM node:20-alpine AS build

WORKDIR /app
ARG VITE_ORACLE_API_BASE_URL=http://127.0.0.1:8000
ENV VITE_ORACLE_API_BASE_URL=${VITE_ORACLE_API_BASE_URL}

COPY O.R.A.C.L.E_GUi_V1_Figma/package*.json ./
RUN npm ci

COPY O.R.A.C.L.E_GUi_V1_Figma/ ./
RUN npm run build

FROM nginx:1.27-alpine

COPY docker/gui/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 4173
HEALTHCHECK --interval=15s --timeout=5s --retries=12 CMD wget -qO- http://127.0.0.1:4173/ >/dev/null || exit 1
CMD ["nginx", "-g", "daemon off;"]
