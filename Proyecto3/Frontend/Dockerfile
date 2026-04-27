FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL=http://localhost:5000
ARG VITE_MQTT_URL=ws://localhost:9001
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_MQTT_URL=$VITE_MQTT_URL

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
