// Utils Module
const Utils = {
    // Format Market Cap
    formatMarketCap: function(marketCap) {
        if (marketCap >= 1000000000000) {
            return (marketCap / 1000000000000).toFixed(2) + 'T';
        } else if (marketCap >= 1000000000) {
            return (marketCap / 1000000000).toFixed(2) + 'B';
        } else if (marketCap >= 1000000) {
            return (marketCap / 1000000).toFixed(2) + 'M';
        } else if (marketCap >= 1000) {
            return (marketCap / 1000).toFixed(2) + 'K';
        } else {
            return marketCap.toFixed(2);
        }
    },
    
    // Format Volume
    formatVolume: function(volume) {
        if (volume >= 1000000000) {
            return (volume / 1000000000).toFixed(2) + 'B';
        } else if (volume >= 1000000) {
            return (volume / 1000000).toFixed(2) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(2) + 'K';
        } else {
            return volume.toString();
        }
    },
    
    // Get Period Text
    getPeriodText: function(period) {
        const periodMap = {
            '1y': '1 Year',
            '3y': '3 Years',
            '7y': '7 Years'
        };
        return periodMap[period] || period;
    }
};