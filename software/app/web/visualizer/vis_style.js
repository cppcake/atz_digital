function sawtooth(teeth, depth) {
    const points = [];
    points.push('0% 0%', '100% 0%', `100% ${100 - depth}%`);

    for (let i = teeth; i >= 1; i--) {
        const x = (i / teeth) * 100;
        const y = i % 2 === 0 ? 100 - depth : 100;
        points.push(`${x.toFixed(2)}% ${y}%`);
    }

    points.push(`0% ${100 - depth}%`);
    
    return `polygon(${points.join(', ')})`;
}


function setup_vis_style(t, d)
{
    document.getElementById("bg-upper").style.clipPath = sawtooth(t, d);
}


document.addEventListener("DOMContentLoaded", () => setup_vis_style(80, 2));
