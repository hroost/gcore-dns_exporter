# gcore-dns_exporter

Docker image to export metrics from [G-Сore DNS](https://gcorelabs.com/dns/) to prometheus

**Parameters**

- port : http port (default : 9886)
- interval : interval between collect in seconds (default: 300)
- gcore_dns_api_key : G-Сore DNS application key


**docker compose sample**

```yml
version: "2.1"

services:

  gcore-dns_exporter:
    build: .
    container_name: gcore-dns_exporter
    ports:
      - "9886:9886"
    environment:
      - GCORE_DNS_API_KEY=xxxxxxxxxxx
```

## How to Use:

1. Generate G-Сore API token https://accounts.gcorelabs.com/profile/api-tokens

You'll want to grant an 'Engineers' role for API Token.

Further documentation on the DNS API endpoint can be found here: https://apidocs.gcorelabs.com/dns

2. Use the generated key and configure it in docker-compose.yml
3. docker-compose up
