
import svgwrite


def createSvgDrawing(width, height, all_lines, door_points):
    svg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))
    for coords in all_lines:
        svg.add(svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))
    for i, pt in enumerate(door_points):
        x, y = pt
        #svg.add(svg.circle(center=(x, y), r=5, fill='red', stroke='black', stroke_width=1))
        #svg.add(svg.text(str(i), insert=(x + 10, y + 10), fill='black', font_size='12px'))
    return svg


