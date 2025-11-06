# Multi-stage build para produção
FROM node:20-alpine AS builder

WORKDIR /app

# Argumento para API base URL
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Copia arquivos de dependências
COPY package*.json ./

# Instala dependências
RUN npm ci

# Copia o código fonte
COPY . .

# Build da aplicação
RUN npm run build

# Stage de produção
FROM nginx:alpine

# Copia os arquivos buildados
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia configuração do nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

