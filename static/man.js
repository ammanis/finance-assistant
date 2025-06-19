let spendingChart; // Global vars - all function can use (week/month/year-spending-data)

const categoryEmojis = { // Emoji for 'updateCategoryBreakdown' fx
    // Income
    "Salary": "💼",
    "Allowance": "💰",
    "Other Income": "🪙",
    // Expenses
    "Groceries": "🛒",
    "Dining": "🍽️",
    "Transport": "🚌",
    "Bills": "🧾",
    "Rent": "🏠",
    "Healthcare": "💊",
    "Education": "📚",
    "Shopping": "🛍️",
    "Entertainment": "🎮",
    "Subscription": "🔄",
    "Travel": "✈️",
    "Gift": "🎁",
    "Insurance": "🛡️",
    "Others": "❓"
};

// Initialize weekly stats chart
function initStatsChart() {
    fetch('/api/weekly-spending-data', {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        const ctx = document.getElementById('spendingChart').getContext('2d');
        if (spendingChart) spendingChart.destroy();

        spendingChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.days,
                datasets: [{
                    label: 'Spending ($)',
                    data: data.spending,
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
                        grid: { display: true, color: '#f5f5f5' },
                        ticks: { stepSize: 10000 }
                    },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    })
    .catch(error => console.error('Error fetching weekly transaction data:', error));
}

// Update category breakdown
function updateCategoryBreakdown(mode = 'week') {
    fetch(`/api/category-breakdown?mode=${mode}`, {
        method: 'GET',
        credentials: 'include'
    })
    .then(response => response.json())
    .then(data => {
        const categoryList = document.querySelector('.category-list');
        categoryList.innerHTML = '';
        let totalExpenses = 0;

        // For emoji display
        for (let category in data.categories) {
        const categoryItem = document.createElement('div');
        categoryItem.classList.add('transaction-item'); // Use same styling as transactions

        const emoji = categoryEmojis[category] || '❔';

        const categoryName = document.createElement('span');
        categoryName.textContent = `${emoji} ${category}`;

        const categoryAmount = document.createElement('span');
        const amount = data.categories[category].toLocaleString();
        categoryAmount.textContent = `$${amount}`;

        categoryItem.appendChild(categoryName);
        categoryItem.appendChild(categoryAmount);
        categoryList.appendChild(categoryItem);

        totalExpenses += data.categories[category];
    }

        // Print total expense
        const totalElement = document.querySelector('.total-expenses h3');
        totalElement.textContent = `Total Expenses: $${totalExpenses.toLocaleString()}`;
    })
    .catch(error => console.error('Error fetching category breakdown data:', error));
}

// Monthly pie chart update
function updateMonthlyChart() {
    fetch('/api/monthly-category-data')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('spendingChart').getContext('2d');
            if (spendingChart) spendingChart.destroy();

            spendingChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.categories,
                    datasets: [{
                        label: 'Monthly Spending',
                        data: data.amounts,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
                        ],
                        borderColor: '#ffffff',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: $${context.raw.toLocaleString()}`;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading monthly data:', error);
        });
}

function updateYearlyChart() {
    fetch('/api/yearly-spending-data')
    .then(response => response.json())
    .then(data => {
        if (!Array.isArray(data)) {
            throw new Error("Invalid data format from server");
        }

        const labels = data.map(d => d.year.toString());
        const values = data.map(d => Math.abs(d.total)); // 💡 use absolute value

        const ctx = document.getElementById('spendingChart').getContext('2d');
        if (spendingChart) spendingChart.destroy();  

        spendingChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Yearly Spending ($)',
                    data: values,
                    backgroundColor: '#FF9F40',
                    borderColor: '#FF9F40',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return `${value.toLocaleString()}`;
                            }
                        },
                        grid: { color: '#f0f0f0' }
                    },
                    x: {
                        ticks: {
                            autoSkip: false,
                            maxRotation: 45,
                            minRotation: 45
                        },
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `$${context.raw.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    })
    .catch(error => {
        console.error('Error loading yearly data:', error);
    });
}

// Tab switch logic
document.addEventListener("DOMContentLoaded", () => {
    // Default load
    initStatsChart();
    updateCategoryBreakdown('week');

    // Handle tab switching
    document.querySelectorAll('.time-tabs button').forEach((btn, idx) => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.time-tabs button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (idx === 0) {
                initStatsChart();
                updateCategoryBreakdown('week');
            } else if (idx === 1) {
                updateMonthlyChart();
                updateCategoryBreakdown('month');
            } else if (idx === 2) {
                updateYearlyChart();
                updateCategoryBreakdown('year');
            }
        });
    });
});

// Camera page logic
// Capture & Upload Logic
document.addEventListener("DOMContentLoaded", () => {
    const video = document.getElementById("video");
    const captureButton = document.getElementById("captureImage");
    const closeButton = document.getElementById("closeCamera");
    const canvas = document.getElementById("canvas");
    let stream = null;

    if (closeCamera && captureButton && video && canvas) {

        // Start camera
        navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        })
        .then((mediaStream) => {
            video.srcObject = mediaStream;
        })
        .catch((err) => {
            alert("Camera access denied: " + err.message);
            console.error(err);
        });

        // Close camera
        closeButton.addEventListener("click", () => {
                    if (stream) stream.getTracks().forEach(track => track.stop());
                    if (video) video.srcObject = null;
                    window.location.href = "/";
                });
        
         // Capture and upload image
        captureButton.addEventListener("click", () => {
            
        // Set canvas size to match video stream
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Set loading state
        captureButton.disabled = true;
        const originalText = captureButton.textContent;
        captureButton.textContent = "Loading...";

        canvas.toBlob((blob) => {
            const formData = new FormData();
            formData.append("image", blob, "receipt.jpg");

            fetch("/scan", {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(result => {
                // Display result below the video
                const resultDiv = document.getElementById("ocrResult");
                if (resultDiv) {
                    resultDiv.innerHTML = `
                        <h2>OCR Result</h2>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    `;
                }
            })
            .catch(err => {
                alert("Upload failed: " + err.message);
                console.error(err);
            })
            .finally(() => {
                // Restore button state
                captureButton.disabled = false;
                captureButton.textContent = originalText;
            });
        }, "image/jpeg");
    });

    }
});