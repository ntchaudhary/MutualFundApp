
function generateDoughnutChart(jsonData, transaction_type, tag_id) {
    const categories = jsonData.reduce((acc, transaction) => {
        if (transaction.income_expense === transaction_type) {
            acc[transaction.category] = (acc[transaction.category] || 0) + transaction.amount;
        }
        return acc;
    }, {});


    var accordionMap = {
        "dummy": "dummy"
    }

    jsonData.forEach(item => {
        if (item.income_expense === transaction_type) {
            accordionMap[item.category] = "collapse" + item.category.replaceAll(' ', '_') + '_' + item.income_expense; // Extracting the category
        }
    });

    // Prepare data for Chart.js
    const labels = Object.keys(categories);
    const amounts = Object.values(categories);

    // Generate random colors for each category
    const generateColor = () => {
        const random = () => Math.floor(Math.random() * 255);
        return `rgb(${random()}, ${random()}, ${random()})`;
    };
    const backgroundColors = labels.map(generateColor);
    const borderColors = backgroundColors.map(color => color);

    // Calculate total amount for percentage calculation
    const totalAmount = amounts.reduce((sum, value) => sum + value, 0);

    // Get the context of the canvas element once
    var ctx = document.getElementById(tag_id).getContext('2d')

    // Create a new Chart object
    var chartRef


    chartRef = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                label: tag_id,
                data: amounts,
                backgroundColor: backgroundColors,
                borderColor: borderColors,
                borderWidth: 1
            }]
        },
        options: {
            onClick: (evt, elements) => {
                
                if (elements.length > 0) {

                    const chartIndex = elements[0].index;
                    const clickedLabel = labels[chartIndex];

                    // Scroll to the corresponding accordion
                    const accordionId = accordionMap[clickedLabel];
                    
                    if (accordionId) {
                        const accordionElement = document.getElementById(accordionId);
                        if (accordionElement) {
                            // Collapse all other accordion sections
                            const allAccordions = document.querySelectorAll('.accordion-collapse');
                            allAccordions.forEach(acc => acc.classList.remove('show'));
        
                            // Scroll to the accordion section and expand it
                            accordionElement.classList.add('show');
                            // document.getElementById(accordionId).scrollIntoView({ behavior: 'smooth' });
                            accordionElement.scrollIntoView({ behavior: 'smooth' });
                        }
                    }
                }
            },
            responsive: true,
            plugins: {
                legend: {
                    position: '', //use 'top' if needed
                },
                tooltip: {
                    callbacks: {
                        label: function (tooltipItem) {
                            const value = tooltipItem.raw;
                            const percentage = ((value / totalAmount) * 100).toFixed(2);
                            return `${tooltipItem.label}: ${percentage}%   Amount: ${value.toLocaleString('en-IN')}`;
                        }
                    }
                },
                centerText: {
                    display: true,
                    text: new Intl.NumberFormat('en-IN').format(totalAmount.toFixed())
                }
            }
        },
        plugins: [{
            id: 'centerText',
            beforeDraw(chart) {
                if (chart.config.options.plugins.centerText.display) {
                    const { width, height, ctx } = chart;
                    ctx.save();
                    const fontSize = (height / 250).toFixed(2);
                    ctx.font = `${fontSize}em sans-serif`;
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = 'white';
                    const text = chart.config.options.plugins.centerText.text;
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = height / 2;
                    ctx.fillText(text, textX, textY);
                    ctx.restore();
                }
            }
        }]
    });

    return chartRef
}