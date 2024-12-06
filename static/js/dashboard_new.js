// Dashboard functionality
let updateInProgress = false;

async function updateDashboardData() {
    if (updateInProgress) {
        console.log('Update already in progress, skipping...');
        return;
    }

    console.log('Starting dashboard update...');
    updateInProgress = true;

    // Get all elements
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
        elements.refreshBtn.disabled = true;
        elements.refreshBtn.innerHTML = '<span class="loading">↻ Refreshing...</span>';
    }

    // Add loading class to values
    Object.values(elements).forEach(el => {
        if (el && el !== elements.refreshBtn && el !== elements.testModeSwitch) {
            el.classList.add('loading');
        }
    });

    try {
        // Force a small delay to make loading state visible
        await new Promise(resolve => setTimeout(resolve, 500));

        // Fetch portfolio data
        console.log('Fetching portfolio data...');
        const portfolioResponse = await fetch('/api/data');
        if (!portfolioResponse.ok) {
            throw new Error(`HTTP error! status: ${portfolioResponse.status}`);
        }
        
        const portfolioData = await portfolioResponse.json();
        console.log('Portfolio data:', portfolioData);

        if (!portfolioData.success) {
            throw new Error('Failed to fetch portfolio data');
        }

        // Update wallet balance with animation
        if (elements.walletBalance && portfolioData.data?.portfolio?.total_value != null) {
            const oldValue = parseFloat(elements.walletBalance.textContent.replace('$', ''));
            const newValue = portfolioData.data.portfolio.total_value;
            
            elements.walletBalance.textContent = `$${newValue.toFixed(2)}`;
            if (oldValue !== newValue) {
                elements.walletBalance.classList.add('value-changed');
                setTimeout(() => elements.walletBalance.classList.remove('value-changed'), 1000);
            }
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
                throw new Error('Failed to fetch test metrics');
            }

            // Update test metrics with animations
            if (metricsData.data) {
                const updates = [
                    {
                        element: elements.testROI,
                        value: metricsData.data.roi,
                        format: (v) => `${v.toFixed(2)}%`
                    },
                    {
                        element: elements.testWinRate,
                        value: metricsData.data.win_rate,
                        format: (v) => `${(v * 100).toFixed(1)}%`
                    },
                    {
                        element: elements.testBalance,
                        value: metricsData.data.balance,
                        format: (v) => `$${v.toFixed(2)}`
                    }
                ];

                updates.forEach(({element, value, format}) => {
                    if (element && value != null) {
                        const oldText = element.textContent;
                        const newText = format(value);
                        if (oldText !== newText) {
                            element.textContent = newText;
                            element.classList.add('value-changed');
                            setTimeout(() => element.classList.remove('value-changed'), 1000);
                        }
                    }
                });
            }
        }
    } catch (error) {
        console.error('Error updating dashboard:', error);
        // Show error in the UI
        if (elements.walletBalance) {
            elements.walletBalance.textContent = 'Error loading data';
            elements.walletBalance.style.color = 'var(--danger-color)';
        }
    } finally {
        // Remove loading states
        Object.values(elements).forEach(el => {
            if (el && el !== elements.testModeSwitch) {
                el.classList.remove('loading');
            }
        });

        // Reset refresh button
        if (elements.refreshBtn) {
            elements.refreshBtn.disabled = false;
            elements.refreshBtn.innerHTML = '↻ Refresh';
        }

        updateInProgress = false;
    }
}

// Initialize dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Initial update
    updateDashboardData();
    
    // Add click handler to refresh button
    const refreshBtn = document.getElementById('refreshBalance');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', (e) => {
            e.preventDefault();
            updateDashboardData();
        });
    }
    
    // Add change handler to test mode switch
    const testModeSwitch = document.getElementById('testModeSwitch');
    if (testModeSwitch) {
        testModeSwitch.addEventListener('change', updateDashboardData);
    }
    
    // Update every 30 seconds
    setInterval(updateDashboardData, 30000);
    console.log('Automatic updates configured.');
});
