document.addEventListener('DOMContentLoaded', function() {
    // Die folgenden Variablen werden im Template gesetzt!
    if (typeof window.chartData !== "undefined") {
        // Tischbelegung-Chart
        const tableCtx = document.getElementById('tableOccupationChart');
        if (tableCtx) {
            new Chart(tableCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Belegt', 'Frei'],
                    datasets: [{
                        data: window.chartData.tableData,
                        backgroundColor: ['#2563eb', '#e5e7eb'],
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        },
                        title: {
                            display: true,
                            text: 'Tischbelegung'
                        }
                    }
                }
            });
        }

        // Top Vereine Chart
        const vereinsCtx = document.getElementById('topVereinsChart');
        if (vereinsCtx && window.chartData.vereinsLabels && window.chartData.vereinsData) {
            new Chart(vereinsCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: window.chartData.vereinsLabels,
                    datasets: [{
                        label: 'Anzahl Personen',
                        data: window.chartData.vereinsData,
                        backgroundColor: '#0d9488',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false,
                        },
                        title: {
                            display: true,
                            text: 'Top Vereine nach Personen'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    }
});