<div align="center">
  <img src="custom_components/ghostfolio/icon.png" alt="Ghostfolio Logo" width="120" height="120">
</div>

# Ghostfolio Home Assistant Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MichelFR&repository=hacs_ghostfolio&category=integration)

A Home Assistant Custom Component (HACS integration) for monitoring your [Ghostfolio](https://github.com/ghostfolio/ghostfolio) portfolio performance.

## Features

This integration provides the following sensors for your Ghostfolio portfolio:

- **Current Value**: The current total value of your portfolio
- **Net Performance**: The absolute net performance of your portfolio
- **Net Performance Percentage**: The net performance as a percentage
- **Total Investment**: The total amount you have invested
- **Net Performance With Currency Effect**: Net performance including currency effects
- **Net Performance Percentage With Currency Effect**: Net performance percentage including currency effects

## Installation

### HACS (Recommended)

1. Make sure you have [HACS](https://hacs.xyz/) installed
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations
   - Click the three dots in the top right corner
   - Select "Custom repositories"
   - Add this repository URL and select "Integration" as the category
3. Install the integration from HACS
4. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `custom_components/ghostfolio` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "Add Integration" and search for "Ghostfolio"
3. Enter your Ghostfolio instance details:
   - **Base URL**: The URL of your Ghostfolio instance (e.g., `https://your-ghostfolio.com`)
   - **Access Token**: Your Ghostfolio access token

### Getting Your Access Token

1. Log in to your Ghostfolio instance
2. Go to your account settings
3. Generate or copy your access token
4. Use this token in the Home Assistant integration setup

## API Endpoints Used

This integration uses the following Ghostfolio API endpoints:

- `POST /api/v1/auth/anonymous` - For authentication using the access token
- `GET /api/v2/portfolio/performance?range=max` - For retrieving portfolio performance data

## Data Update Frequency

The integration updates portfolio data every 15 minutes by default. This can be customized if needed.

## Support

For issues with this integration, please open an issue on the GitHub repository.

For issues with Ghostfolio itself, please refer to the [Ghostfolio GitHub repository](https://github.com/ghostfolio/ghostfolio).

## License

This project is licensed under the MIT License - see the LICENSE file for details.