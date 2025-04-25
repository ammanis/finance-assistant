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
    // Function to fetch and initialize the weekly spending chart
    function initStatsChart() {
        fetch('/api/weekly-spending-data', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('spendingChart').getContext('2d');
            const spendingChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.days,  // x-axis: Mon-Sun
                    datasets: [{
                        label: 'Spending (₩)',
                        data: data.spending,  // y-axis: Spending for each day
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
                                stepSize: 10000 // Adjust to your needs
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
        .catch(error => console.error('Error fetching weekly transaction data:', error));
    }

    // Function to fetch and update the category breakdown
    function updateCategoryBreakdown() {
        fetch('/api/category-breakdown', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            const categoryList = document.querySelector('.category-list');
            categoryList.innerHTML = '';  // Clear existing items
            let totalExpenses = 0;

            // Loop through the categories and create the category items dynamically
            for (let category in data.categories) {
                const categoryItem = document.createElement('div');
                categoryItem.classList.add('category-item');

                const categoryName = document.createElement('span');
                categoryName.classList.add('category-name');
                categoryName.textContent = category;

                const categoryAmount = document.createElement('span');
                categoryAmount.classList.add('category-amount');
                const amount = data.categories[category].toLocaleString();  // Format the amount
                categoryAmount.textContent = `₩${amount}`;

                categoryItem.appendChild(categoryName);
                categoryItem.appendChild(categoryAmount);
                categoryList.appendChild(categoryItem);

                totalExpenses += data.categories[category];
            }

            // Display total expenses at the bottom
            const totalElement = document.querySelector('.total-expenses h3');
            totalElement.textContent = `Total Expenses: ₩${totalExpenses.toLocaleString()}`;
        })
        .catch(error => console.error('Error fetching category breakdown data:', error));
    }

    // Initialize chart and category breakdown when the page loads
    initStatsChart();
    updateCategoryBreakdown();
});
