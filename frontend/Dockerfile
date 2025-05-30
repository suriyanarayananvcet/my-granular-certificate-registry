FROM node:20-bullseye-slim

WORKDIR /app

# ENV REACT_APP_API_URL=https://api-dot-rich-store-445612-c6.ew.r.appspot.com
ENV REACT_APP_API_URL=http://localhost:8001

COPY . .

RUN mkdir -p dist && chmod 777 dist

RUN npm install

RUN npm run build

EXPOSE 8080

RUN npm install -g serve

CMD ["serve", "-s", "dist", "-l", "8080"]
