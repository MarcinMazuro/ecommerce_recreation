FROM prestashop/prestashop:1.7.8.8-apache

# Instaluj wymagane narzędzia
RUN apt-get update && apt-get install -y \
    openssl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Kopiuj bazowe pliki PrestaShop z obrazu
RUN cp -n -R -T -p /tmp/data-ps/prestashop/ /var/www/html

# Kopiuj katalogi PrestaShop
COPY --chown=www-data:www-data app/config/html/modules /var/www/html/modules
COPY --chown=www-data:www-data app/config/html/themes /var/www/html/themes
COPY --chown=www-data:www-data app/config/html/app /var/www/html/app
COPY --chown=www-data:www-data app/config/html/admin58570fy2d /var/www/html/admin58570fy2d
COPY --chown=www-data:www-data app/config/html/vendor /var/www/html/vendor
COPY --chown=www-data:www-data app/config/html/src /var/www/html/src
COPY --chown=www-data:www-data app/config/html/config /var/www/html/config
COPY --chown=www-data:www-data app/config/html/img /var/www/html/img
COPY --chown=www-data:www-data app/config/html/classes /var/www/html/classes

# Kopiuj dump bazy danych
COPY app/config/db-export/dump_2026-01-24_23-10.sql /seed/prestashop.sql

# Kopiuj skrypt startowy (POPRAWIONA NAZWA!)
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# Generuj SSL certificate
RUN mkdir -p /etc/apache2/ssl \
    && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
       -keyout /etc/apache2/ssl/prestashop.key \
       -out /etc/apache2/ssl/prestashop.crt \
       -subj "/C=PL/ST=Poland/L=Warsaw/O=PrestaShop/CN=localhost"

# Konfiguruj Apache
COPY app/config/apache-ssl.conf /etc/apache2/sites-available/default-ssl.conf
RUN a2enmod ssl rewrite headers \
    && a2dissite 000-default.conf \
    && a2ensite default-ssl.conf

# Uprawnienia
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && rm -rf /var/www/html/install || true \
    && chown -R www-data:www-data /var/www/html/var 2>/dev/null || true \
    && chown -R www-data:www-data /var/www/html/cache 2>/dev/null || true \
    && chown -R www-data:www-data /var/www/html/download 2>/dev/null || true \
    && chown -R www-data:www-data /var/www/html/upload 2>/dev/null || true \
    && chown -R www-data:www-data /var/www/html/img 2>/dev/null || true


ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["apache2-foreground"]