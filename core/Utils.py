SIZE = 800
class Utils:
    def __init__(self,x_min_raw, x_max_raw, y_min_raw, y_max_raw):
        self.y_max_raw = y_max_raw
        self.y_min_raw = y_min_raw
        self.x_max_raw = x_max_raw
        self.x_min_raw = x_min_raw
        self.svg_scale  = SIZE / max(x_max_raw - x_min_raw, y_max_raw - y_min_raw)
        self.width = (x_max_raw - x_min_raw) * self.svg_scale
        self.height = (y_max_raw - y_min_raw) * self.svg_scale



    def get_x_min_raw(self):
        return self.x_min_raw
    
    def get_x_max_raw(self):
        return self.x_max_raw
    
    def get_y_min_raw(self):
        return self.y_min_raw
    
    def get_y_max_raw(self):
        return self.y_max_raw

    def scale(self,x, y):
        x_svg = (x - self.x_min_raw) * self.svg_scale
        y_svg = (self.y_max_raw - y) * self.svg_scale  # flipped Y
        return x_svg, y_svg

    def norm_x(self,x):
        norm = (x - self.x_min_raw) / (self.x_max_raw - self.x_min_raw + 1e-6)
        return norm * 800

    def norm_y(self,y):
        norm = (y - self.y_min_raw) / (self.y_max_raw - self.y_min_raw + 1e-6)
        return (1 - norm) * 800

    def unscale(self, scaled_x, scaled_y):
        raw_x = scaled_x / self.svg_scale + self.x_min_raw
        raw_y = self.y_max_raw - (scaled_y / self.svg_scale)
        return raw_x, raw_y

    def get_unit_size(self):
        return self.svg_scale
