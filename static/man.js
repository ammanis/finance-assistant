document.addEventListener("DOMContentLoaded", () => {
    const closeButton = document.getElementById("closeCamera");
    const video = document.getElementById("video");
    let stream = null;
  
    // Only activate on camera page
    if (video && closeButton) {
      // Start camera when page loads (user has already clicked scan before this)
      navigator.mediaDevices.getUserMedia({ video: true })
        .then((mediaStream) => {
          stream = mediaStream;
          video.srcObject = stream;
        })
        .catch((err) => {
          alert("Camera access denied: " + err.message);
          console.error(err);
        });
  
      // Handle Close button
      closeButton.addEventListener("click", () => {
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }
  
        if (video) {
          video.srcObject = null;
        }
  
        window.location.href = "/";
      });
    }
  });


  document.addEventListener('DOMContentLoaded', function () {
    let spendingChart;

    // Function to fetch data and initialize the chart
    function initStatsChart() {
        fetch('/api/transaction-data', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('spendingChart').getContext('2d');
            spendingChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels, // Use the days of the week as labels
                    datasets: [{
                        label: 'Spending (₩)',
                        data: data.data, // Use the amount data from the API
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
                                stepSize: 10000, // Round ticks to 10,000, adjust as needed
                                max: Math.max(...data.data) + 10000, // Set max to a rounded value
                                min: 0 // Ensure it starts from 0
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
        })
        .catch(error => console.error('Error fetching transaction data:', error));
    }

    // Call to initialize the chart
    initStatsChart();

    // Tab switching functionality for stats page
    function setupStatsTabs() {
        const tabs = document.querySelectorAll('.time-tabs button');
        tabs.forEach(tab => {
            tab.addEventListener('click', function () {
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                console.log(`Showing data for: ${this.textContent}`);
                // You can implement additional logic here to fetch data for different time ranges
            });
        });
    }

    setupStatsTabs();
});
