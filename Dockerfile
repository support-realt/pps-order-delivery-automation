FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Firefox + dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    wget \
    curl \
    ca-certificates \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    libxt6 \
    libxrender1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# Install fixed GeckoDriver version (safer than dynamic)
ENV GECKO_VERSION=v0.36.0

RUN wget -q https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux64.tar.gz \
    && tar -xzf geckodriver-${GECKO_VERSION}-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm geckodriver-${GECKO_VERSION}-linux64.tar.gz

WORKDIR /app

# Copy everything from current folder into container
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
