FROM node:18-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY tailwind.config.js postcss.config.js ./


COPY public ./public
COPY src ./src

CMD ["npm", "start"]