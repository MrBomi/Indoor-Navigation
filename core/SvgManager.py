
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

# def addGridToSvg(all_lines, coarse_to_fine, utils, spacing):
#     grid_svg = svgwrite.Drawing(size=(f"{utils.width}px", f"{utils.height}px"))
#     cell_spacing = spacing
#     cell_size_px = cell_spacing * utils.svg_scale

#     print("🟦 Drawing grid rectangles...")
#     updated_coarse_to_fine = {}
#     count = 0

#     for line in all_lines:
#         coords = [utils.scale(x, y) for x, y in line.coords]
#         grid_svg.add(grid_svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

#     for coarse_pt, fine_pts in coarse_to_fine.items():
#         x_svg, y_svg = utils.scale(coarse_pt[0], coarse_pt[1])

#         grid_svg.add(grid_svg.rect(
#             insert=(x_svg - cell_size_px / 2, y_svg - cell_size_px / 2),
#             size=(cell_size_px, cell_size_px),
#             fill='blue',
#             fill_opacity=0.1,
#             stroke='black',
#             stroke_width=0.1,
#             id=f"cell-{round(x_svg, 2)}-{round(y_svg, 2)}"
#         ))

#         updated_coarse_to_fine[(round(x_svg, 2), round(y_svg, 2))] = fine_pts
#         count += 1     
    # print(f"🟦 Done drawing {count} grid squares.")
    # return grid_svg

def addGridToSvg(all_lines, coarse_to_fine, utils, spacing):
    grid_svg = svgwrite.Drawing(size=(f"{utils.width}px", f"{utils.height}px"))
    cell_spacing = spacing
    cell_size_px = cell_spacing * utils.svg_scale

    updated_coarse_to_fine = {}
    cell_id_to_coords = {}
    count = 0

    # Draw background polylines
    for line in all_lines:
        coords = [utils.scale(x, y) for x, y in line.coords]
        grid_svg.add(grid_svg.polyline(points=coords, stroke='gray', fill='none', stroke_width=0.5))

    # Draw cells and map IDs to original coordinates
    for coarse_pt, fine_pts in coarse_to_fine.items():
        x_svg, y_svg = utils.scale(coarse_pt[0], coarse_pt[1])

        count += 1
        cell_id = str(count)

        grid_svg.add(grid_svg.rect(
            insert=(x_svg - cell_size_px / 2, y_svg - cell_size_px / 2),
            size=(cell_size_px, cell_size_px),
            fill='blue',
            fill_opacity=0.1,
            stroke='black',
            stroke_width=0.1,
            id=cell_id
        ))

        font_size = cell_size_px / max(2, len(cell_id))
        grid_svg.add(grid_svg.text(
            cell_id,
            insert=(x_svg, y_svg),
            text_anchor="middle",
            alignment_baseline="middle",
            font_size=font_size,
            fill="black"
        ))

        cell_id_to_coords[count] = coarse_pt
        updated_coarse_to_fine[(round(x_svg, 2), round(y_svg, 2))] = fine_pts

    return grid_svg, cell_id_to_coords

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

def draw_grid1(
    svg,
    graph,
    utils, 
    spacing_units = 100,       # 1m == 100 model units    
    draw_cells=False,         # draw 1m squares centered on nodes
    draw_edges=True,         # set True if you also want edges
    draw_nodes=True,         # set True if you also want node dots
    label_cells=False,        # draw a small ID inside each cell
):
    """
    Overlay a 1m visual grid derived from an UNWEIGHTED graph on top of an existing svgwrite.Drawing.
    Assumes: graph[u] is a list of coordinate tuples (x, y), without weights.
    Coordinates are placed using utils.scale(x, y) -> (px_x, px_y), same transform as the building.
    """
    # 1) Collect nodes and unique undirected edges (unweighted)
       # 1m == 100 model units
    nodes = set()
    edges = set()
    for u, nbrs in graph.items():
        nodes.add(u)
        for v in nbrs:
            nodes.add(v)
            a, b = sorted([u, v])
            edges.add((a, b))

    # 2) Optional: draw edges first
    if draw_edges and edges:
        edges_g = svg.add(svg.g(id="graph-edges", stroke="#888", fill="none", stroke_width=0.8))
        for (a, b) in edges:
            x1, y1 = utils.scale(a[0], a[1])
            x2, y2 = utils.scale(b[0], b[1])
            edges_g.add(svg.line(start=(x1, y1), end=(x2, y2)))

    # 3) Draw 1m cells centered on nodes
    cell_id_to_coords = {}
    if draw_cells and nodes:
        cell_size_px = spacing_units * utils.svg_scale
        half = cell_size_px / 2.0

        cells_g = svg.add(svg.g(id="graph-cells",
                                fill="blue", fill_opacity=0.10,
                                stroke="black", stroke_width=0.1))
        labels_g = svg.add(svg.g(id="graph-cell-labels", fill="black"))

        for idx, (x, y) in enumerate(sorted(nodes), start=1):
            cx, cy = utils.scale(x, y)
            cells_g.add(svg.rect(insert=(cx - half, cy - half),
                                 size=(cell_size_px, cell_size_px),
                                 id=str(idx)))
            if label_cells:
                font_size = max(7, cell_size_px / max(2.2, len(str(idx))))
                labels_g.add(svg.text(str(idx),
                                      insert=(cx, cy),
                                      text_anchor="middle",
                                      alignment_baseline="middle",
                                      font_size=font_size))
            cell_id_to_coords[idx] = (x, y)

    # 4) Optional: draw node dots on top
    if draw_nodes and nodes:
        nodes_g = svg.add(svg.g(id="graph-nodes", fill="#1976d2", stroke="none"))
        r = max(0.5, spacing_units * utils.svg_scale * 0.05)
        for (x, y) in nodes:
            cx, cy = utils.scale(x, y)
            nodes_g.add(svg.circle(center=(cx, cy), r=r))

    return svg, cell_id_to_coords

import math

def draw_grid(
    svg,
    graph,            # dict[(x,y)] -> list[(x,y)]  # unweighted neighbors
    utils,
    spacing_units=50, # 0.5 m == 50 model units -> 1.0 m == 100
    draw_cells=True,
    draw_edges=True,
    draw_nodes=True,
    label_cells=True,
    origin=(0.0, 0.0),   # model-units origin the grid is aligned to
):
    """
    Draws 1 m cells by merging four 0.5 m cells. Every node belongs to exactly one 1 m cell.
    Returns the same structure as the original: (svg, cell_id_to_coords).
    """

    # 1) Collect nodes and unique undirected edges (unweighted)
    nodes = set()
    edges = set()
    for u, nbrs in graph.items():
        nodes.add(u)
        for v in nbrs:
            nodes.add(v)
            if u != v:
                a, b = (u, v) if u <= v else (v, u)
                edges.add((a, b))

    # 2) Draw edges (optional)
    if draw_edges and edges:
        edges_g = svg.add(svg.g(id="graph-edges", stroke="#888", fill="none", stroke_width=0.8))
        for (a, b) in edges:
            x1, y1 = utils.scale(a[0], a[1])
            x2, y2 = utils.scale(b[0], b[1])
            edges_g.add(svg.line(start=(x1, y1), end=(x2, y2)))

    # 3) Group nodes into 1 m cells aligned to `origin`
    big = 2 * spacing_units  # size of a 1 m cell in model units
    ox, oy = origin
    cell1m_to_nodes = {}
    for (x, y) in nodes:
        ix = int(math.floor((x - ox) / big))
        iy = int(math.floor((y - oy) / big))
        cell1m_to_nodes.setdefault((ix, iy), set()).add((x, y))

    # 4) Draw 1 m cells and create cell_id_to_coords mapping
    cell_id_to_coords = {}
    if draw_cells and cell1m_to_nodes:
        cells_g  = svg.add(svg.g(id="grid-1m-cells",  fill="blue",  fill_opacity=0.10,
                                 stroke="black", stroke_width=0.1))
        labels_g = svg.add(svg.g(id="grid-1m-labels", fill="black"))

        for idx, (ix, iy) in enumerate(sorted(cell1m_to_nodes.keys()), start=1):
            # bounds in model units
            minx_mu = ox + ix * big
            miny_mu = oy + iy * big
            maxx_mu = minx_mu + big
            maxy_mu = miny_mu + big

            # pixel rectangle
            x0_px, y0_px = utils.scale(minx_mu, miny_mu)
            x1_px, y1_px = utils.scale(maxx_mu, maxy_mu)
            w_px, h_px   = abs(x1_px - x0_px), abs(y1_px - y0_px)
            left_px, top_px = min(x0_px, x1_px), min(y0_px, y1_px)

            cells_g.add(svg.rect(insert=(left_px, top_px),
                                 size=(w_px, h_px),
                                 id=str(idx)))

            if label_cells:
                cx_px, cy_px = left_px + w_px / 2.0, top_px + h_px / 2.0
                font_size = max(7, min(w_px, h_px) / max(2.2, len(str(idx))))
                labels_g.add(svg.text(str(idx),
                                      insert=(cx_px, cy_px),
                                      text_anchor="middle",
                                      alignment_baseline="middle",
                                      font_size=font_size))

            # store cell center in model units
            center_x_mu = (minx_mu + maxx_mu) / 2.0
            center_y_mu = (miny_mu + maxy_mu) / 2.0
            cell_id_to_coords[idx] = (center_x_mu, center_y_mu)

    # 5) Draw node dots (optional)
    if draw_nodes and nodes:
        nodes_g = svg.add(svg.g(id="graph-nodes", fill="#1976d2", stroke="none"))
        r = max(0.5, spacing_units * utils.svg_scale * 0.05)
        for (x, y) in nodes:
            cx, cy = utils.scale(x, y)
            nodes_g.add(svg.circle(center=(cx, cy), r=r))

    return svg, cell_id_to_coords
