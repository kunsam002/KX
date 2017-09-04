upstream web_cluster {

  #least_conn;
  server  188.226.164.109;
}

server {
        listen 80;
        server_name *.kampusxchange www.kampusxchange.com m.kampusxchange.com kampusxchange.com;

  location ~ ^/(img|js|css|fonts)/ {  # |pi||ext|theme
        root                    /opt/kx/kx/static;
        add_header              Cache-Control public;
        expires                 30d;
        #access_log              off;
        access_log                            /var/log/nginx/kx/main.access.log;
        error_log                             /var/log/nginx/kx/main.error.log;
  }

  location / { try_files $uri @yourapplication; }

  location /static {
    alias                    /opt/kx/kx/static;
    add_header              Cache-Control public;
    expires                 30d;
  }

  location /robots.txt {
    deny        all;
  }

  location /favicon.ico {
    deny        all;
  }

  location @yourapplication {
    include uwsgi_params;
    uwsgi_pass unix:///tmp/main.sock;
  }


}



server {
	listen 80;
    server_name admin.kampusxchange.com;

  location ~ ^/(img|js|css|fonts)/ {  # |pi||ext|theme
    root                    /opt/kx/kx/static;
    add_header              Cache-Control public;
    expires                 30d;
    #access_log              off;
    access_log                            /var/log/nginx/kx/admin.access.log;
    error_log                             /var/log/nginx/kx/admin.error.log;
  }

  location / { try_files $uri @yourapplication; }

  location /static {
    alias                    /opt/kx/kx/static;
    add_header              Cache-Control public;
    expires                 30d;
  }

  location /robots.txt {
    deny        all;
  }

  location /favicon.ico {
    deny        all;
  }

  location @yourapplication {
    include uwsgi_params;
    uwsgi_pass unix:///tmp/admin.sock;
  }

}




server {
        listen 80;
        server_name *.singaempire.com www.singaempire.com m.singaempire.com singaempire.com;

  location / {
        root /opt/singaempire/;
  	index index.html;
	try_files $uri $uri/ $uri.html;
  }

  location /robots.txt {
    deny        all;
  }

  location /favicon.ico {
    deny        all;
  }
  location /mp3 {
    sendfile           on;
    sendfile_max_chunk 1m;
  }
}
