FROM stacscan/stacs:0.4.3-r1b4c85b

# Default environment variables.
ENV FAIL_BUILD=true

# Allow build-time specification of version.
ARG VERSION

# Keep things friendly.
LABEL org.opencontainers.image.title="STACS-CI"
LABEL org.opencontainers.image.description="Static Token And Credential Scanner CI"
LABEL org.opencontainers.image.url="https://www.github.com/stacscan/stacs-ci"
LABEL org.opencontainers.image.version=$VERSION

# Install STACS into the container.
WORKDIR /opt/stacs-ci
COPY requirements.txt setup.py setup.cfg ./
COPY stacs ./stacs
COPY wrapper/stacs-ci /usr/bin/stacs-ci
RUN apk add --no-cache jq && pip install --no-cache-dir .

# Default to the generic STACS CI integration.
ENTRYPOINT ["stacs-ci"]
