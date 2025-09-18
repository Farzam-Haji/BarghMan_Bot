# BarghMan Telegram Bot

BarghMan is a Telegram bot with a Django backend that fetches blackout reports from a public API and serves them to users.

## Features

- Fully asynchronous Telegram bot as the user interface.
- Uses SQLite to store Telegram users and their bills.
- Add, delete, or alias bills via the Telegram bot.
- Fetch single or multiple bill reports and return them through the bot.
- Parse API JSON responses into a readable format for users.
- Support for multiple bills per user with combined results.
- Store reports in Redis with regular updates for faster response times.
- Automatically send today’s and tomorrow’s outages to users, with an option to disable this feature.
- Track the number of reports each user has received.
- Uses watchdog and auto-restart to ensure the bot remains active even with unstable network connections.
- Six custom Django management commands:
  - `get_stats` – Show the total number of users and reports sent.
  - `check_outages` – Update Redis with new reports for each bill.
  - `manual_fetch` – Fetch and parse a specific bill from the API.
  - `send_all_outages` – Send the full report for all user bills through Telegram.
  - `send_near_outages` – Send near outages for all user bills through Telegram.
  - `send_custom_message` – Send a custom message to all users via Telegram.

## Deployment

BarghMan is optimized for Debian/Ubuntu servers. A `deploy.sh` script in the project root automates setup:

- Install OS dependencies.
- Create a Python virtual environment and install project dependencies.
- Create a SQLite database and run initial Django migrations.
- Create a `.env` file in the project root.
- Add two cron jobs to:
  - Update Redis with new reports.
  - Send daily near-outage messages to users.
- Create a folder in `/var/log/` to store cron job logs.
- Add a systemd service to run the Telegram bot continuously.

### Customization Before Deployment

- **Service Name:** Modify line 5 of `deploy.sh` to set your service name (default is `barghman-bot`). This name is used for the systemd service, cron job name, and log folder in `/var/log/`.
- **Environment Variables:** Lines 48–50 allow you to set your `.env` values, including API tokens and the Telegram bot token.
- **Cron Job Logs:** If you want a custom log path, comment out the LOG FOLDER section in `deploy.sh` and adjust the cron job paths accordingly.

### Running the Deployment Script

```bash
chmod +x deploy.sh
./deploy.sh
```
**Note:** On non-Debian-based servers, additional adjustments may be required for the systemd service. The bot can run without watchdog if needed.

## Usage

Once the bot is deployed and running, users can interact with it via Telegram.

### Commands

- `/add <bill_number>` – Add a bill to your account.
- `/delete` – Remove a bill from your account.
- `/name` – Assign a custom name to a bill.
- `/check` – Fetch the latest report for a single or multiple bills.
- `/auto` – Enable or disable daily outage notifications.
- `/help` – Receive help about bot commands.

### Bot Features

- The bot automatically sends today’s and tomorrow’s near outages to users who have auto-updates enabled.
- Each report is stored in Redis for faster access.
- Provides tooltips (help text) for commands to improve usability. 