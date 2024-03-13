FROM nginx

# copy our nginx configuration template to templates folder, so it will create
# default.conf at /etc/nginx/conf.d/ with environment variables replacement
COPY default.conf.template /etc/nginx/templates/
# link nginx logs to container stdout
RUN ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log