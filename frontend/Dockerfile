# build env
FROM node:21.7.1
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . ./
RUN npm run build
CMD cp -r build result_build
