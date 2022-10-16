# Fit Star Utilization

Python script for pulling utilization data from the
[Fit Star website](https://www.fit-star.de), paired with
[Grafana](https://grafana.com/)
dashboard for visualization.

![Fit Star Utilization Dashboard](dashboard.png)

## Python Script
The script uses [Selenium](https://www.selenium.dev/)
to automatically retrieve the utilization data from the Fit Star studio
websites (e.g. https://www.fit-star.de/fitnessstudio/muenchen-neuhausen).
This has certain implications for its dependencies and usage.

### Dependencies
Selenium requires a compatible browser together with the corresponding driver.
A good choice is [Chromium](https://www.chromium.org),
which can be installed with the driver by:
```bash
sudo apt install -y chromium chromium-driver
```
The required Python modules are listed in the
[`requirements.txt`](requirements.txt)
file. To install them execute:
```bash
sudo python3 -m pip install -r requirements.txt
```

### Usage
To fetch the data for all studios in Munich and insert them into a given
[InfluxDB](https://www.influxdata.com/) the script is used as follows:
```bash
./fitstar-utilization.py --host influxdb.example.net --port 8086 --ssl --verify-ssl --username admin --password supersecretpassword --filter muenchen
```
For further information refer to the `-h/--help` option.

## Grafana Dashboard
The Grafana dashboard can be directly imported from the Grafana webpage:
https://grafana.com/grafana/dashboards/17192

## License
This project is distributed under [MIT](LICENSE) license.
