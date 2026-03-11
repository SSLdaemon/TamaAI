/**
 * D3.js Interactive Charts for TamaAI Parent Dashboard
 * Professional time-series visualization with Ocean Depths theme
 */

// Ocean Depths Theme Colors
const COLORS = {
    primary: '#2d8b8b',
    primaryDark: '#1a5f5f',
    accent: '#a8dadc',
    text: '#1a2332',
    textLight: '#457b9d',
    health: '#2d8b8b',
    hunger: '#f4a261',
    mood: '#457b9d',
    energy: '#e9c46a'
};

/**
 * Create multi-line time series chart for pet stats
 * @param {string} containerId - DOM element ID
 * @param {Array} data - Array of {timestamp, health, hunger, mood, energy}
 */
function createStatsChart(containerId, data) {
    // Clear existing
    d3.select(`#${containerId}`).select('svg').remove();

    // Dimensions
    const margin = { top: 20, right: 80, bottom: 40, left: 50 };
    const container = document.getElementById(containerId);
    const width = container.clientWidth - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    // SVG
    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Parse data
    const parseTime = d3.timeParse('%Y-%m-%d %H:%M:%S');
    data.forEach(d => {
        d.date = typeof d.timestamp === 'string' ? parseTime(d.timestamp) : new Date(d.timestamp * 1000);
        d.health = +d.health;
        d.hunger = +d.hunger;
        d.mood = +d.mood;
        d.energy = +d.energy;
    });

    // Scales
    const x = d3.scaleTime()
        .domain(d3.extent(data, d => d.date))
        .range([0, width]);

    const y = d3.scaleLinear()
        .domain([0, 100])
        .range([height, 0]);

    // Line generators
    const lineHealth = d3.line().x(d => x(d.date)).y(d => y(d.health)).curve(d3.curveMonotoneX);
    const lineHunger = d3.line().x(d => x(d.date)).y(d => y(100 - d.hunger)).curve(d3.curveMonotoneX);
    const lineMood = d3.line().x(d => x(d.date)).y(d => y(d.mood)).curve(d3.curveMonotoneX);
    const lineEnergy = d3.line().x(d => x(d.date)).y(d => y(d.energy)).curve(d3.curveMonotoneX);

    // Grid lines
    svg.append('g')
        .attr('class', 'grid')
        .attr('opacity', 0.1)
        .call(d3.axisLeft(y).ticks(5).tickSize(-width).tickFormat(''));

    // Axes
    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x).ticks(6))
        .style('color', COLORS.textLight)
        .style('font-size', '12px');

    svg.append('g')
        .call(d3.axisLeft(y).ticks(5))
        .style('color', COLORS.textLight)
        .style('font-size', '12px');

    // Lines
    svg.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', COLORS.health)
        .attr('stroke-width', 2.5)
        .attr('d', lineHealth);

    svg.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', COLORS.hunger)
        .attr('stroke-width', 2.5)
        .attr('d', lineHunger);

    svg.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', COLORS.mood)
        .attr('stroke-width', 2.5)
        .attr('d', lineMood);

    svg.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', COLORS.energy)
        .attr('stroke-width', 2.5)
        .attr('d', lineEnergy);

    // Legend
    const legend = svg.append('g')
        .attr('transform', `translate(${width - 70}, 10)`);

    const legendData = [
        { label: 'Health', color: COLORS.health },
        { label: 'Fullness', color: COLORS.hunger },
        { label: 'Mood', color: COLORS.mood },
        { label: 'Energy', color: COLORS.energy }
    ];

    legendData.forEach((item, i) => {
        const g = legend.append('g')
            .attr('transform', `translate(0, ${i * 20})`);

        g.append('line')
            .attr('x1', 0)
            .attr('x2', 20)
            .attr('y1', 0)
            .attr('y2', 0)
            .attr('stroke', item.color)
            .attr('stroke-width', 2.5);

        g.append('text')
            .attr('x', 25)
            .attr('y', 4)
            .text(item.label)
            .style('font-size', '11px')
            .style('fill', COLORS.text);
    });

    // Tooltip
    const tooltip = d3.select('body').append('div')
        .attr('class', 'd3-tooltip')
        .style('position', 'absolute')
        .style('background', COLORS.card || '#f1faee')
        .style('padding', '8px 12px')
        .style('border-radius', '8px')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.15)')
        .style('pointer-events', 'none')
        .style('opacity', 0)
        .style('font-size', '12px')
        .style('color', COLORS.text);

    // Overlay for mouse tracking
    svg.append('rect')
        .attr('width', width)
        .attr('height', height)
        .style('fill', 'none')
        .style('pointer-events', 'all')
        .on('mousemove', function (event) {
            const [xPos] = d3.pointer(event);
            const x0 = x.invert(xPos);
            const bisect = d3.bisector(d => d.date).left;
            const i = bisect(data, x0, 1);
            const d = data[i];

            if (d) {
                tooltip
                    .style('opacity', 1)
                    .html(`
                        <strong>${d3.timeFormat('%b %d, %H:%M')(d.date)}</strong><br/>
                        <span style="color: ${COLORS.health}">●</span> Health: ${d.health.toFixed(0)}<br/>
                        <span style="color: ${COLORS.hunger}">●</span> Fullness: ${(100 - d.hunger).toFixed(0)}<br/>
                        <span style="color: ${COLORS.mood}">●</span> Mood: ${d.mood.toFixed(0)}<br/>
                        <span style="color: ${COLORS.energy}">●</span> Energy: ${d.energy.toFixed(0)}
                    `)
                    .style('left', (event.pageX + 15) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            }
        })
        .on('mouseout', () => {
            tooltip.style('opacity', 0);
        });
}

/**
 * Create character development radar chart
 * @param {string} containerId - DOM element ID  
 * @param {Object} outcomes - {punctuality, empathy, responsibility}
 */
function createCharacterGauge(containerId, outcomes) {
    d3.select(`#${containerId}`).select('svg').remove();

    const margin = 40;
    const container = document.getElementById(containerId);
    const size = Math.min(container.clientWidth, 250);
    const radius = (size - 2 * margin) / 2;

    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', size)
        .attr('height', size)
        .append('g')
        .attr('transform', `translate(${size / 2}, ${size / 2})`);

    const attributes = ['Punctuality', 'Empathy', 'Responsibility'];
    const values = [
        outcomes.punctuality || 50,
        outcomes.empathy || 50,
        outcomes.responsibility || 50
    ];

    const angleSlice = (Math.PI * 2) / attributes.length;

    // Scales
    const rScale = d3.scaleLinear().domain([0, 100]).range([0, radius]);

    // Circular grid
    [20, 40, 60, 80, 100].forEach(level => {
        svg.append('circle')
            .attr('r', rScale(level))
            .style('fill', 'none')
            .style('stroke', COLORS.accent)
            .style('stroke-width', 1)
            .style('opacity', 0.3);

        if (level === 100 || level === 50) {
            svg.append('text')
                .attr('x', 5)
                .attr('y', -rScale(level))
                .text(level)
                .style('font-size', '10px')
                .style('fill', COLORS.textLight);
        }
    });

    // Axes
    attributes.forEach((attr, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        const x = rScale(100) * Math.cos(angle);
        const y = rScale(100) * Math.sin(angle);

        svg.append('line')
            .attr('x1', 0)
            .attr('y1', 0)
            .attr('x2', x)
            .attr('y2', y)
            .style('stroke', COLORS.textLight)
            .style('stroke-width', 1)
            .style('opacity', 0.5);

        const labelX = rScale(110) * Math.cos(angle);
        const labelY = rScale(110) * Math.sin(angle);

        svg.append('text')
            .attr('x', labelX)
            .attr('y', labelY)
            .attr('text-anchor', 'middle')
            .attr('dy', '0.35em')
            .text(attr)
            .style('font-size', '12px')
            .style('font-weight', '600')
            .style('fill', COLORS.text);
    });

    // Data area
    const dataPoints = values.map((value, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        return {
            x: rScale(value) * Math.cos(angle),
            y: rScale(value) * Math.sin(angle),
            value
        };
    });

    const radarLine = d3.lineRadial()
        .angle((d, i) => angleSlice * i)
        .radius(d => rScale(d))
        .curve(d3.curveLinearClosed);

    svg.append('path')
        .datum(values)
        .attr('d', radarLine)
        .style('fill', COLORS.primary)
        .style('fill-opacity', 0.2)
        .style('stroke', COLORS.primary)
        .style('stroke-width', 2.5);

    // Data points
    svg.selectAll('.data-point')
        .data(dataPoints)
        .enter()
        .append('circle')
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)
        .attr('r', 4)
        .style('fill', COLORS.primaryDark)
        .style('stroke', '#fff')
        .style('stroke-width', 2);
}
