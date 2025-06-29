
import svgwrite
import xml.etree.ElementTree as ET
from core.Utils import Utils


def createSvgDrawing(width, height, all_lines, door_points):
    svg = svgwrite.Drawing(size=(f"{width}px", f"{height}px"))
    for coords in all_lines:
        svg.add(svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))
    for i, pt in enumerate(door_points):
        x, y = pt
        #svg.add(svg.circle(center=(x, y), r=5, fill='red', stroke='black', stroke_width=1))
        #svg.add(svg.text(str(i), insert=(x + 10, y + 10), fill='black', font_size='12px'))
    return svg

def addGridToSvg(all_lines, coarse_to_fine, utils, spacing):
    grid_svg = svgwrite.Drawing(size=(f"{utils.width}px", f"{utils.height}px"))
    cell_spacing = spacing
    cell_size_px = cell_spacing * utils.svg_scale

    print("🟦 Drawing grid rectangles...")
    updated_coarse_to_fine = {}
    count = 0

    for line in all_lines:
        coords = [utils.scale(x, y) for x, y in line.coords]
        grid_svg.add(grid_svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

    for coarse_pt, fine_pts in coarse_to_fine.items():
        x_svg, y_svg = utils.scale(coarse_pt[0], coarse_pt[1])

        grid_svg.add(grid_svg.rect(
            insert=(x_svg - cell_size_px / 2, y_svg - cell_size_px / 2),
            size=(cell_size_px, cell_size_px),
            fill='blue',
            fill_opacity=0.1,
            stroke='black',
            stroke_width=0.1,
            id=f"cell-{round(x_svg, 2)}-{round(y_svg, 2)}"
        ))

        updated_coarse_to_fine[(round(x_svg, 2), round(y_svg, 2))] = fine_pts
        count += 1
         
    print(f"🟦 Done drawing {count} grid squares.")
    return grid_svg

def update_svg_door_names(svg, doors_data, x_min_raw, x_max_raw, y_min_raw, y_max_raw, radius=4, color='blue'):
    SVG_NS = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NS)

    svg_root = ET.fromstring(svg)
    utils = Utils(x_min_raw, x_max_raw, y_min_raw, y_max_raw)
    for door in doors_data:
        x, y = utils.scale(door["x"], door["y"])
        name = door.get("name", f"Door {door['id']}")

        circle = ET.SubElement(svg_root, f"{{{SVG_NS}}}circle", {
            'cx': str(x),
            'cy': str(y),
            'r': str(radius),
            'fill': color,
            'stroke': 'black',
            'stroke-width': '0.8',
            'id': f'door-{door["id"]}'
        })

        text = ET.SubElement(svg_root, f"{{{SVG_NS}}}text", {
            'x': str(x),
            'y': str(y - radius - 2),
            'font-size': "8",
            'fill': "black",
            'text-anchor': "middle"
        })
        text.text = name

    return ET.tostring(svg_root, encoding='utf-8', xml_declaration=True).decode('utf-8')

def draw_path_in_svg(svg, path, x_min_raw, x_max_raw, y_min_raw, y_max_raw, color='red', stroke_width=2):
    SVG_NS = "http://www.w3.org/2000/svg"
    ET.register_namespace("", SVG_NS)

    utils = Utils(x_min_raw, x_max_raw, y_min_raw, y_max_raw)
    scaled_path = [utils.scale(x, y) for x, y in path]
    svg_root = ET.fromstring(svg)

    points_str = " ".join(f"{x},{y}" for x, y in scaled_path)
    path_element = ET.Element(f"{{{SVG_NS}}}polyline", {
        'points': points_str,
        'stroke': color,
        'stroke-width': str(stroke_width),
        'fill': 'none',
        'id': 'path'
    })

    svg_root.append(path_element)
    return ET.tostring(svg_root, encoding='utf-8', xml_declaration=True).decode('utf-8')