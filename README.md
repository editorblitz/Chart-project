# Chart Project

Echarts ideas for displaying prices, other data.

## Project Structure

```
fix-charts/
│
├── original/                  # Original HTML files (before proxy implementation)
│   ├── FL_tableheatmaps.html   # Testing a concept for a chart that we used to run 
│   ├── midday generator final.html  # Generates price chart that mimics our style with logo
│   ├── original_pricehistory.html   # Main tool I use for pulling price histories
│   └── spreads price chart.html     # I like to check price spreads
│
├── proxy/                     # Proxy-enabled versions
│   ├── fourpricechart.html     # Above four-price comparison chart
│   ├── middaypricechart.html   # Above midday price chart
│   ├── pricehistory_proxy.html # Above price history with proxy
│   └── LNG.html               # Another idea to visualize LNG data history, but having issues
│
├── proxy_server.py           # Python proxy server 
├── requirements.txt          
└── README.md                 
```

## Prerequisites

- Python 3.7 or higher (for proxy server) I guess I should use a more recent version

## Setup

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd fix-charts
   ```

2. Create a `.env` file in the project root with your NGI API credentials:
   ```
   NGI_API_USERNAME=your_username@example.com
   NGI_API_PASSWORD=your_password
   ```

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Proxy Server

1. Start the proxy server:
   ```bash
   python proxy/proxy_server.py
   ```

2. The server will start on `http://localhost:8081`

## Notes

1. Open any HTML file from the `proxy` directory in a web browser
2. Original files aren't working with CORS policy
3. Uses [Apache ECharts](https://echarts.apache.org/) that is open source. It has a large community behind it and matches up well with paid options like Highcharts.