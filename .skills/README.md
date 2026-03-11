# Claude Skills - Usage Guide for Tamaai

This directory contains Claude Skills that enhance the development and design of the Tamaai project.

## Available Skills

### 1. Canvas Design
**Location**: `.skills/canvas-design/`
**Purpose**: Create beautiful visual art in PNG and PDF documents

**Use When**:
- Creating Rex the dinosaur character designs
- Designing achievement badges/certificates
- Making educational posters about responsibility
- Generating visual assets for the app

**How to Use**:
When you need visual design, I'll reference the `SKILL.md` file to:
1. Create a design philosophy (aesthetic vision)
2. Express it visually as PNG or PDF

**Example Request**: "Create a cute dinosaur character sheet for Rex showing different emotional expressions (happy, sad, hungry, sleepy)"

---

### 2. Theme Factory
**Location**: `.skills/theme-factory/`
**Purpose**: Apply professional color and font themes to documents and artifacts

**Available Themes**:
1. Ocean Depths - Professional and calming
2. Sunset Boulevard - Warm and vibrant
3. Forest Canopy - Natural earth tones
4. Modern Minimalist - Clean grayscale
5. Golden Hour - Rich autumnal
6. Arctic Frost - Cool winter-inspired
7. Desert Rose - Soft sophisticated
8. Tech Innovation - Bold modern
9. Botanical Garden - Fresh organic
10. Midnight Galaxy - Dramatic cosmic

**Use When**:
- Styling parent dashboard reports
- Creating presentation slides
- Applying consistent branding to HTML pages

**How to Use**:
View `theme-showcase.pdf` to see all themes, then apply to any artifact.

**Example Request**: "Apply the Forest Canopy theme to the parent dashboard"

---

### 3. D3.js Visualization
**Location**: `.skills/d3js-visualization/`
**Purpose**: Create sophisticated, interactive data visualizations

**Use When**:
- Building interactive charts for parent dashboard
- Visualizing pet stats over time (health, mood, energy trends)
- Creating network diagrams or custom visualizations
- Adding responsive, animated charts

**Best For**:
- Line charts (stats over time)
- Bar charts (action frequency)
- Heatmaps (activity by time of day)
- Force-directed graphs (relationship networks)

**How to Use**:
I'll reference the skill to create D3.js code following best practices:
- Proper scales and axes
- Smooth transitions
- Responsive sizing
- Interactive tooltips

**Example Request**: "Create a D3.js line chart showing Rex's health, mood, and energy over the last 7 days"

---

## Integration with Tamaai

### For Visual Assets
Use **Canvas Design** to create:
- `static/images/rex-expressions/` - Character art
- `static/images/badges/` - Achievement icons
- Parent dashboard header graphics

### For Dashboard Styling
Use **Theme Factory** for:
- Parent HTML report templates
- Dashboard color schemes
- Consistent branding across views

### For Analytics
Use **D3.js Visualization** for:
- `static/js/parent-charts.js` - Interactive charts
- Real-time stat monitoring
- Historical data visualization

---

## How It Works

These skills are **instruction sets** that I (Antigravity) read and follow when you request relevant work. They're not installed like MCP servers - instead, they guide my approach to specific tasks.

**Workflow**:
1. You request visual design / theme / chart
2. I read the relevant SKILL.md file
3. I follow its best practices and patterns
4. I create the output (PNG, themed HTML, D3.js code, etc.)

---

## Next Steps

Try requesting:
- "Design a badge for '7 Days of Great Care' achievement"
- "Create a health trend chart for the parent dashboard using D3.js"
- "Apply the Ocean Depths theme to parent.html"
