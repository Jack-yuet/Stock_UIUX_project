/**
 * Score Comparison Tool
 */

function compareScores(stockCode) {
    const scoreHistory = JSON.parse(localStorage.getItem('scoreHistory') || '{}');
    const stockScores = scoreHistory[stockCode];
    
    if (!stockScores) {
        console.log(`No score history found for stock ${stockCode}`);
        return;
    }
    
    console.log(`=== Score Details for ${stockCode} ===`);
    // Assuming stockScores is an array or object, adapt accordingly. The old code treated it as object, but api.js saves it as array.
    // Let's assume we want the latest one if it's an array.
    const latestScore = Array.isArray(stockScores) ? stockScores[stockScores.length - 1] : stockScores;

    console.log(`Final Score: ${latestScore.finalScore}`);
    console.log(`Time: ${new Date(latestScore.timestamp).toLocaleString()}`);
    console.log('');
    
    console.log('=== Component Scores ===');
    if (latestScore.details) {
        // The structure might have changed in my previous edits to be flat or nested
        // Checking score_engine.js: details contains technicalSignals, patternSignals, etc.
        // breakdown contains the scores.
        if (latestScore.breakdown) {
             console.log(`Trend: ${latestScore.breakdown.trendScore}`);
             console.log(`Technical: ${latestScore.breakdown.technicalScore}`);
             console.log(`Pattern: ${latestScore.breakdown.patternScore}`);
             console.log(`Market Env: ${latestScore.breakdown.marketEnvironmentScore}`);
             console.log(`Consistency: ${latestScore.breakdown.consistencyBonus}`);
        }
    }
}

function showAllScoreHistory() {
    const scoreHistory = JSON.parse(localStorage.getItem('scoreHistory') || '{}');
    
    console.log('=== All Stock Score History ===');
    Object.keys(scoreHistory).forEach(stockCode => {
        const scoreList = scoreHistory[stockCode];
        if (Array.isArray(scoreList)) {
            scoreList.forEach(score => {
                console.log(`${stockCode}: ${score.finalScore} (${new Date(score.timestamp).toLocaleString()})`);
            });
        }
    });
}

// Call these functions in console to debug
// compareScores('stock_code')
// showAllScoreHistory()