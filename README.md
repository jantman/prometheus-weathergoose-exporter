# EXPERIMENTAL/ALPHA/UNSUPPORTED prometheus-weathergoose-exporter

[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip) [![Docker Pulls](https://img.shields.io/docker/pulls/jantman/prometheus-security-spy-exporter)](https://hub.docker.com/repository/docker/jantman/prometheus-security-spy-exporter) [![GitHub last commit](https://img.shields.io/github/last-commit/jantman/prometheus-security-spy-exporter)](https://github.com/jantman/prometheus-security-spy-exporter)

Prometheus exporter for the IT Watchdogs WeatherGoose 1 (WxGoos-1)

**WARNING** This code is to be considered experimental/alpha and essentially **unsupported**. I don't use Security Spy myself; I'm writing this for a local non-profit that does, and just wants to get notified if it stops recording or otherwise breaks. Once I get an initial version of this written and working, I will likely never touch it again. I also will have no way to test changes, as I don't run Security Spy myself. Please plan accordingly. If you'd like to take over this project, please let me know via an issue.

## Usage

### Docker

To run on port 8080:

```
docker run -p 8080:8080 \
    -e WEATHERGOOSE_XML_URL=http://WeatherGoose-IP/data.xml \
    jantman/prometheus-weathergoose-exporter:latest
```

### Environment Variables

* `WEATHERGOOSE_XML_URL` (**required**) - The full URL to the WeatherGoose XML.

## Metrics Provided

An example of the output of the `/metrics` endpoint can be seen at [example.prom](example.prom)

## Weathergoose WxGoos-1 Factory Reset

If you have an I.T. Watchdogs WxGoos-1 and don't have the credentials, you can log in as an administrator by using http://192.168.123.123 with a username of ``reset`` and a password of ``powerup`` followed by the last 4 digits of the serial number (on my unit, a 7-digit numeric found on a small barcode label on the outside of the unit).

## Development

Clone the repo, then in your clone:

```
python3 -mvenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Release Process

Tag the repo. [GitHub Actions](https://github.com/jantman/prometheus-security-spy-exporter/actions) will run a Docker build, push to Docker Hub, and create a release on the repo.
