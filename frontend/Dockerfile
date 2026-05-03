FROM node:20-alpine AS base

WORKDIR /opt/frontend

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./

RUN npm i --silent --no-progress || true

COPY . .

ARG VITE_BACKEND_URL=http://localhost:8000/api/v1
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "preview"]
