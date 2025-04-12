// Constants
const API_BASE_URL = 'http://localhost:5000/api';
const UPDATE_INTERVAL = 5000; // 5 seconds

// Chart configurations and instances
let priceChart;
let performanceChart;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    setupEventListeners();
    startDataUpdates();
});

// Set up event listeners
function setupEventListeners() {
    document.getElementById('startTradingBtn').addEventListener('click', startTrading);
    document.getElementById('stopTradingBtn').addEventListener('click', stopTrading);
}

// Initialize charts
function initializeCharts() {
    // Price Chart
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'GOLD Price',
                data: [],
                borderColor: '#F59E0B',
                borderWidth: 2,
                fill: false,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });

    // Performance Chart
    const performanceCtx = document.getElementById('performanceChart').getContext('2d');
    performanceChart = new Chart(performanceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cumulative Profit/Loss',
                data: [],
                borderColor: '#10B981',
                borderWidth: 2,
                fill: true,
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: true
                }
            }
        }
    });
}

// Start automated trading
async function startTrading() {
    try {
        const response = await fetch(`${API_BASE_URL}/trade/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('Trading started successfully', 'success');
            document.getElementById('startTradingBtn').disabled = true;
            document.getElementById('stopTradingBtn').disabled = false;
        } else {
            throw new Error('Failed to start trading');
        }
    } catch (error) {
        showNotification('Failed to start trading: ' + error.message, 'error');
    }
}

// Stop automated trading
async function stopTrading() {
    try {
        const response = await fetch(`${API_BASE_URL}/trade/stop`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            showNotification('Trading stopped successfully', 'success');
            document.getElementById('startTradingBtn').disabled = false;
            document.getElementById('stopTradingBtn').disabled = true;
        } else {
            throw new Error('Failed to stop trading');
        }
    } catch (error) {
        showNotification('Failed to stop trading: ' + error.message, 'error');
    }
}

// Update dashboard data
async function updateDashboard() {
    try {
        const [accountData, tradeData, performanceData] = await Promise.all([
            fetch(`${API_BASE_URL}/trade/account`).then(res => res.json()),
            fetch(`${API_BASE_URL}/trade/recent`).then(res => res.json()),
            fetch(`${API_BASE_URL}/trade/performance`).then(res => res.json())
        ]);

        updateAccountInfo(accountData);
        updateTradeHistory(tradeData);
        updateCharts(performanceData);
    } catch (error) {
        console.error('Failed to update dashboard:', error);
    }
}

// Update account information
function updateAccountInfo(data) {
    document.getElementById('accountBalance').textContent = formatCurrency(data.balance);
    document.getElementById('profitLoss').textContent = formatCurrency(data.profitLoss);
    document.getElementById('winRate').textContent = `${data.winRate}%`;
    document.getElementById('openTrades').textContent = data.openTrades;

    // Update profit/loss color based on value
    const profitLossElement = document.getElementById('profitLoss');
    profitLossElement.className = data.profitLoss >= 0 ? 'text-green-500' : 'text-red-500';
}

// Update trade history table
function updateTradeHistory(trades) {
    const tbody = document.getElementById('recentTradesBody');
    tbody.innerHTML = '';

    trades.forEach(trade => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatDateTime(trade.timestamp)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-semibold rounded-full 
                    ${trade.type === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                    ${trade.type}
                </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatPrice(trade.entryPrice)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                ${formatPrice(trade.exitPrice)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm ${trade.profitLoss >= 0 ? 'text-green-500' : 'text-red-500'}">
                ${formatCurrency(trade.profitLoss)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <span class="px-2 py-1 text-xs font-semibold rounded-full 
                    ${getStatusColor(trade.status)}">
                    ${trade.status}
                </span>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Update charts with new data
function updateCharts(data) {
    // Update price chart
    priceChart.data.labels = data.timestamps;
    priceChart.data.datasets[0].data = data.prices;
    priceChart.update();

    // Update performance chart
    performanceChart.data.labels = data.timestamps;
    performanceChart.data.datasets[0].data = data.performance;
    performanceChart.update();
}

// Start periodic data updates
function startDataUpdates() {
    updateDashboard(); // Initial update
    setInterval(updateDashboard, UPDATE_INTERVAL);
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(price);
}

function formatDateTime(timestamp) {
    return new Date(timestamp).toLocaleString();
}

function getStatusColor(status) {
    const statusColors = {
        'OPEN': 'bg-blue-100 text-blue-800',
        'CLOSED': 'bg-gray-100 text-gray-800',
        'PENDING': 'bg-yellow-100 text-yellow-800',
        'ERROR': 'bg-red-100 text-red-800'
    };
    return statusColors[status] || 'bg-gray-100 text-gray-800';
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    } text-white`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Error handling
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    showNotification('An error occurred. Please check the console.', 'error');
});
