var ctx = document.getElementById('myChart').getContext('2d');
var chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'Temperatura',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1,
                yAxisID: 'y'
            },
            {
                label: 'Umidade',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1,
                yAxisID: 'y'
            },
            {
                label: 'Tensão Elétrica',
                data: [],
                borderColor: '#ff9800',
                tension: 0.1,
                yAxisID: 'y2'
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Temperatura (°C) / Umidade (%)'
                }
            },
            y2: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'Tensão (V)'
                },
                grid: {
                    drawOnChartArea: false
                }
            }
        }
    }
});

function fetchData() {
    fetch('/api/dados')
        .then(response => response.json())
        .then(data => {
            // Atualiza os valores nos cards
            document.getElementById('temperature').textContent = data.temperature + '°C';
            document.getElementById('humidity').textContent = data.humidity + '%';
            document.getElementById('presence').textContent = data.presence ? 'Presente' : 'Ausente';
            document.getElementById('voltage').textContent = data.voltage + 'V';

            // Adiciona novos pontos ao gráfico
            const now = new Date();
            chart.data.labels.push(now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds());
            
            chart.data.datasets[0].data.push(data.temperature);
            chart.data.datasets[1].data.push(data.humidity);
            chart.data.datasets[2].data.push(data.voltage);

            // Mantém apenas os últimos 15 pontos
            if (chart.data.labels.length > 15) {
                chart.data.labels.shift();
                chart.data.datasets.forEach(dataset => {
                    dataset.data.shift();
                });
            }

            chart.update();
        });
}

// Atualiza a cada 5 segundos
setInterval(fetchData, 5000);
fetchData(); // Primeira chamada