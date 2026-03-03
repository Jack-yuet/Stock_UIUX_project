// Chart Module
const Chart = {
    // Display Kline Chart
    displayKlineChart: function(klineData, stockCode) {
        if (!klineData || !klineData.daily || klineData.daily.length === 0) {
            $('#chartContent').html('<div class="chart-placeholder">No Kline Data</div>');
            return;
        }
        
        const data = klineData.daily;
        const dates = data.map(item => item.date);
        const opens = data.map(item => item.open);
        const highs = data.map(item => item.high);
        const lows = data.map(item => item.low);
        const closes = data.map(item => item.close);
        const volumes = data.map(item => item.volume);
        
        const fig = {
            data: [],
            layout: {
                grid: {
                    rows: 3,
                    columns: 1,
                    pattern: 'independent',
                    rowheight: [0.65, 0.15, 0.2]
                },
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                font: {family: 'Arial, sans-serif', size: 12},
                xaxis_rangeslider_visible: false,
                height: 800,
                showlegend: true,
                legend: {
                    orientation: "h",
                    yanchor: "bottom",
                    y: 1.02,
                    xanchor: "right",
                    x: 1
                },
                margin: {
                    l: 60,
                    r: 60,
                    t: 60,
                    b: 60
                },
                autosize: true
            }
        };
        
        // Kline
        fig.data.push({
            x: dates,
            open: opens,
            high: highs,
            low: lows,
            close: closes,
            type: 'candlestick',
            name: 'Kline',
            increasing_line_color: '#ff4444',
            decreasing_line_color: '#44ff44',
            increasing_fillcolor: '#ff4444',
            decreasing_fillcolor: '#44ff44',
            line: {width: 1},
            xaxis: 'x',
            yaxis: 'y'
        });
        
        // MA
        const ma5Data = data.filter(item => item.ma5).map(item => item.ma5);
        const ma10Data = data.filter(item => item.ma10).map(item => item.ma10);
        const ma20Data = data.filter(item => item.ma20).map(item => item.ma20);
        
        if (ma5Data.length > 0) {
            fig.data.push({
                x: dates.slice(-ma5Data.length),
                y: ma5Data,
                type: 'scatter',
                mode: 'lines',
                name: 'MA5',
                line: {color: '#ffaa00', width: 1},
                opacity: 0.8,
                xaxis: 'x',
                yaxis: 'y'
            });
        }
        
        if (ma10Data.length > 0) {
            fig.data.push({
                x: dates.slice(-ma10Data.length),
                y: ma10Data,
                type: 'scatter',
                mode: 'lines',
                name: 'MA10',
                line: {color: '#00aaff', width: 1},
                opacity: 0.8,
                xaxis: 'x',
                yaxis: 'y'
            });
        }
        
        if (ma20Data.length > 0) {
            fig.data.push({
                x: dates.slice(-ma20Data.length),
                y: ma20Data,
                type: 'scatter',
                mode: 'lines',
                name: 'MA20',
                line: {color: '#aa00ff', width: 1},
                opacity: 0.8,
                xaxis: 'x',
                yaxis: 'y'
            });
        }
        
        // Volume
        fig.data.push({
            x: dates,
            y: volumes,
            type: 'bar',
            name: 'Volume',
            marker: {
                color: '#888888',
                opacity: 0.7
            },
            xaxis: 'x2',
            yaxis: 'y2'
        });
        
        // Volume MA
        const volumeMa5Data = data.filter(item => item.volume_ma5).map(item => item.volume_ma5);
        if (volumeMa5Data.length > 0) {
            fig.data.push({
                x: dates.slice(-volumeMa5Data.length),
                y: volumeMa5Data,
                type: 'scatter',
                mode: 'lines',
                name: 'Volume MA5',
                line: {color: '#ff0000', width: 2},
                opacity: 0.8,
                xaxis: 'x2',
                yaxis: 'y2'
            });
        }
        
        // Daily Return
        const dailyReturnData = data.filter(item => item.daily_return).map(item => item.daily_return);
        if (dailyReturnData.length > 0) {
            fig.data.push({
                x: dates.slice(-dailyReturnData.length),
                y: dailyReturnData,
                type: 'bar',
                name: 'Change(%)',
                marker: {
                    color: dailyReturnData.map(val => val > 0 ? '#ff4444' : '#44ff44'),
                    opacity: 0.7
                },
                xaxis: 'x3',
                yaxis: 'y3'
            });
        }
        
        // Axes
        fig.layout.xaxis = {
            rangeslider: {visible: false},
            type: 'date'
        };
        fig.layout.yaxis = {
            title: 'Price ($)',
            side: 'left'
        };
        
        fig.layout.xaxis2 = {
            type: 'date',
            domain: [0, 1],
            range: fig.layout.xaxis.range
        };
        fig.layout.yaxis2 = {
            title: 'Volume',
            side: 'left',
            domain: [0.45, 0.65]
        };
        
        fig.layout.xaxis3 = {
            type: 'date',
            domain: [0, 1],
            range: fig.layout.xaxis.range
        };
        fig.layout.yaxis3 = {
            title: 'Change (%)',
            side: 'left',
            domain: [0, 0.25]
        };
        
        Plotly.newPlot('chartContent', fig.data, fig.layout, {
            responsive: true,
            displayModeBar: false,
            modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines'],
            scrollZoom: true
        });
        
        document.getElementById('chartContent').on('plotly_doubleclick', function() {
            return false;
        });
    }
};