FROM grafana/grafana:10.4.0

USER root

RUN mkdir -p /var/lib/grafana/plugins && \
    chmod -R 777 /var/lib/grafana/plugins

COPY marcusolsson-json-datasource /var/lib/grafana/plugins/marcusolsson-json-datasource

RUN chmod -R 777 /var/lib/grafana/plugins/marcusolsson-json-datasource

USER grafana

ENV GF_PLUGINS_ALLOW_LOADING_UNSIGNED_PLUGINS=marcusolsson-json-datasource

EXPOSE 3000

CMD ["grafana-server"]