FROM python:3.13-alpine
WORKDIR /priviblur

RUN apk add --no-cache git tini && \
    addgroup -g 1000 -S priviblur && \
    adduser -u 1000 -S priviblur -G priviblur && \
    git clone --depth=1 https://github.com/syeopite/priviblur.git . && \
    pip3 install --no-cache-dir --break-system-packages -r requirements.txt && \
    pip3 cache purge && \
    pybabel compile -d locales -D priviblur && \
    chown -R priviblur:priviblur /priviblur && \
    git config --global --add safe.directory /priviblur

EXPOSE 8000
USER priviblur
ENTRYPOINT [ "/sbin/tini", "--"]
CMD [ "python", "-m", "src.server" ]
