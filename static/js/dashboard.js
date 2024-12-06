// Dashboard functionality
async function updateDashboardData() {
    console.log('Starting dashboard update...');
    
    // Get all elements we'll update
    const elements = {
        refreshBtn: document.getElementById('refreshBalance'),
        walletBalance: document.getElementById('walletBalance'),
        testROI: document.getElementById('testROI'),
        testWinRate: document.getElementById('testWinRate'),
        testBalance: document.getElementById('testBalance'),
        testModeSwitch: document.getElementById('testModeSwitch')
    };
    
    // Show loading state
    if (elements.refreshBtn) {
        elements.refreshBtn.textContent = '↻ Refreshing...';
        elements.refreshBtn.disabled = true;
    }

    try {
        // Fetch portfolio data
        console.log('Fetching portfolio data...');
        const portfolioResponse = await fetch('/api/data');
        if (!portfolioResponse.ok) {
            throw new Error(`HTTP error! status: ${portfolioResponse.status}`);
        }
        
        const portfolioData = await portfolioResponse.json();
        console.log('Portfolio data:', portfolioData);
        
        if (!portfolioData.success) {
            throw new Error(portfolioData.error || 'Failed to fetch portfolio data');
        }

        // Update wallet balance
        if (elements.walletBalance && portfolioData.data?.portfolio?.total_value != null) {
            const value = Number(portfolioData.data.portfolio.total_value);
            elements.walletBalance.textContent = `$${value.toFixed(2)}`;
            console.log('Updated wallet balance:', value);
        }

        // Only fetch test metrics if test mode is enabled
        if (elements.testModeSwitch?.checked) {
            console.log('Test mode is enabled, fetching metrics...');
            const metricsResponse = await fetch('/api/test_metrics');
            if (!metricsResponse.ok) {
                throw new Error(`HTTP error! status: ${metricsResponse.status}`);
            }
            
            const metricsData = await metricsResponse.json();
            console.log('Test metrics:', metricsData);
            
            if (!metricsData.success) {
                throw new Error(metricsData.error || 'Failed to fetch test metrics');
            }

            // Update test metrics if they exist
            if (metricsData.data) {
                if (elements.testROI && metricsData.data.roi != null) {
                    elements.testROI.textContent = `${Number(metricsData.data.roi).toFixed(2)}%`;
                }
                
                if (elements.testWinRate && metricsData.data.win_rate != null) {
                    elements.testWinRate.textContent = `${Number(metricsData.data.win_rate).toFixed(1)}%`;
                }
                
                if (elements.testBalance && metricsData.data.balance != null) {
                    elements.testBalance.textContent = `$${Number(metricsData.data.balance).toFixed(2)}`;
                }
            }
        }
    } catch (error) {
        console.error('Error updating dashboard:', error);
        // Show error in the UI
        if (elements.walletBalance) {
            elements.walletBalance.textContent = 'Error loading data';
        }
    } finally {
        // Reset refresh button
        if (elements.refreshBtn) {
            elements.refreshBtn.textContent = '↻ Refresh';
            elements.refreshBtn.disabled = false;
        }
    }
}

// Check server status
async function checkServerStatus() {
    const serverStatus = document.getElementById('serverStatus');
    if (!serverStatus) return;
    
    try {
        const response = await fetch('/api/data');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                serverStatus.textContent = 'Running';
                serverStatus.className = 'badge bg-success';
                return;
            }
        }
        throw new Error('Server error');
    } catch (error) {
        console.error('Server status check failed:', error);
        serverStatus.textContent = 'Offline';
        serverStatus.className = 'badge bg-danger';
    }
}

// Initialize dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Initial update
    updateDashboardData();
    checkServerStatus();
    
    // Add click handler to refresh button
    const refreshBtn = document.getElementById('refreshBalance');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            updateDashboardData();
            checkServerStatus();
        });
    }
    
    // Add change handler to test mode switch
    const testModeSwitch = document.getElementById('testModeSwitch');
    if (testModeSwitch) {
        testModeSwitch.addEventListener('change', updateDashboardData);
    }
    
    // Check server status every minute
    setInterval(checkServerStatus, 60000);
    
    console.log('Dashboard initialized with manual refresh.');
});
