FROM nginx:latest

RUN mkdir /etc/nginx/ssl
ADD /chat-ops.key /etc/nginx/ssl/chat-ops.key
ADD /chat-ops.crt /etc/nginx/ssl/chat-ops.crt
ADD /chat-ops.nginx.conf /etc/nginx/conf.d/default.conf
ADD /.htpasswd /etc/nginx/.htpasswd
ADD /dist/chat-ops-ui /usr/share/nginx/html