// Initialize the chart when stats page loads
function initStatsChart() {
    const ctx = document.getElementById('spendingChart').getContext('2d');
    const spendingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Spending ($)',
                data: [90, 70, 85, 60, 95, 75, 120],
                backgroundColor: '#6a5acd',
                borderColor: '#6a5acd',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        display: true,
                        color: '#f5f5f5'
                    },
                    ticks: {
                        stepSize: 20
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Tab switching functionality for stats page
function setupStatsTabs() {
    const tabs = document.querySelectorAll('.time-tabs button');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            console.log(`Showing data for: ${this.textContent}`);
        });
    });
}

// Page navigation
function showPage(pageId) {
    // Hide all pages
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    
    // Show the selected page
    document.getElementById(pageId).classList.add('active');
    
    // Update active nav button
    document.querySelectorAll('.bottom-nav button').forEach(btn => {
        btn.classList.remove('active');
    });
    event.currentTarget.classList.add('active');
    
    // Initialize chart if stats page is shown
    if (pageId === 'statsPage') {
        initStatsChart();
        setupStatsTabs();
    }
}

// Button event listeners
document.getElementById('homeBtn').addEventListener('click', (e) => {
    showPage('homePage');
    e.currentTarget.classList.add('active');
});

document.getElementById('statsBtn').addEventListener('click', (e) => {
    showPage('statsPage');
    e.currentTarget.classList.add('active');
});

document.getElementById('aiBtn').addEventListener('click', (e) => {
    showPage('aiPage');
    e.currentTarget.classList.add('active');
});

document.getElementById('profileBtn').addEventListener('click', (e) => {
    showPage('profilePage');
    e.currentTarget.classList.add('active');
});

document.getElementById('addTransactionBtn').addEventListener('click', () => {
    alert("Feature to add a new transaction coming soon!");
});

document.getElementById('logoutBtn').addEventListener('click', () => {
    alert("Logged out successfully!");
});

// Initialize home page by default
window.onload = function() {
    document.getElementById('homePage').classList.add('active');
    document.getElementById('homeBtn').classList.add('active');
};