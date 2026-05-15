This is a development document. To deploy the Xiaozhi server, [click here for the deployment guide](../../README.md#%E9%83%A8%E7%BD%B2%E6%96%87%E6%A1%A3).

**MekongAI fork:** Independent fork (no automatic upstream sync). Datasource pool: **HikariCP**. JPA on classpath for migration away from MyBatis; schema remains **Liquibase** only (`ddl-auto: none`).

# Project Overview

manager-api is built on the SpringBoot framework.

When importing the project into your code editor, select the `manager-api` folder as the project directory.

# Development Environment
JDK 21
Maven 3.8+
MySQL 8.0+
Redis 5.0+
Vue 3.x

# API Documentation
After starting the server, open: http://localhost:8002/xiaozhi/doc.html
