# saturnsync

Sync data from https://saturn.live onto any iCalendar compatible service.

## Installation

Use docker to install. See docker-compose.yml.

#### Environment Variables

* `SATURN_TOKEN` - Saturn API token
* `SATURN_REFRESH_TOKEN` - Saturn API refresh token
* `SATURN_DB` - MongoDB database name
* `SATURN_URI` - MongoDB URI
* `SATURN_PORT` - Webserver port
* `SATURN_HOST` - Webserver host
