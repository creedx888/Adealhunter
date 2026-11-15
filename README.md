# DealHunter — self-hosted deal ranking dashboard

A small Flask + SQLite application packaged for Docker/Portainer. It ranks imported product listings by discount percentage (largest first), with filters for category, retailer and minimum discount. It also supports sorting by dollars saved, lowest sale price and product name.

## Important: Amazon source limitation

The supplied source is Amazon's [Device Deals event page](https://www.amazon.com/events/devicedeals/). This project deliberately does **not** crawl or scrape Amazon's page. Amazon's Associates program license expressly restricts data-mining, robots and similar extraction tools, and access to its product data is governed by its program/API terms. The event page also may be inaccessible to automated clients. Do not add proxy rotation, CAPTCHA bypass, stealth browser automation or other anti-bot circumvention.

For Amazon product data, check eligibility and use Amazon's current **Creators API** under its terms:
- Onboarding: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/onboarding
- API reference: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference
- PA-API 5 is deprecated; use Creators API for new integrations.

Creators API access requires an Amazon Associates account and registered API credentials. Confirm that your intended display, caching and ranking use is permitted by the current agreement before connecting it. This dashboard currently accepts CSV data from an authorized export/feed or manual entries. The Amazon event page link is included for reference, not scraped.

## Run locally

```bash
cp .env.example .env
# Change SECRET_KEY in .env
docker compose up -d --build
```

Open `http://localhost:8080`.

## Deploy in Portainer

1. Push this folder to a Git repository.
2. In Portainer, choose **Stacks → Add stack → Repository**.
3. Enter your repository URL and the compose file path `docker-compose.yml`.
4. Set `HOST_PORT` (default `8080`) and a long random `SECRET_KEY` in the stack environment variables.
5. Deploy the stack. The named volume `dealhunter_data` persists your SQLite database across container updates.

If port 8080 is already in use, set `HOST_PORT` to another available host port (for example `8090`).

## CSV import format

Required columns: `title`, `original_price`, `sale_price`.

Optional columns: `product_url`, `image_url`, `retailer`, `category`.

Example:

```csv
title,original_price,sale_price,product_url,image_url,retailer,category
Wireless headphones,199.99,129.99,https://www.amazon.com/dp/ASIN,,Amazon,Electronics
```

Prices may include `$` and commas. Rows with invalid prices or sale prices above original price are skipped and reported. CSV upload is limited to 5 MB by default.

## Ranking

Discount percentage = `(original price - sale price) / original price × 100`.

Default order is:
1. Highest percentage discount
2. Lowest current sale price as a tie-breaker
3. Product name

The dashboard also offers sort modes for total dollars saved, lowest sale price and A–Z. Discount math is only as reliable as the original and sale prices in the imported data. Verify prices at the retailer before purchasing.

## Security notes

- Put this behind HTTPS and preferably an authentication/reverse-proxy layer before exposing it to the public internet.
- Change `SECRET_KEY`; do not commit `.env`.
- This starter is intended for personal/private hosting and does not include user accounts or public multi-tenant access.
