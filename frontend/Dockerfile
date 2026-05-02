FROM node:20-alpine AS base

WORKDIR /opt/frontend

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./

RUN npm i --silent --no-progress || true

COPY . .

# Default to preview (built) for smaller runtime; switch to `npm run dev` if you prefer HMR.
RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview"]
