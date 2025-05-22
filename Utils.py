class Utils:
    def __init__(self,x_min_raw, x_max_raw, y_min_raw, y_max_raw,scale):
        self.y_max_raw = y_max_raw
        self.y_min_raw = y_min_raw
        self.x_max_raw = x_max_raw
        self.x_min_raw = x_min_raw
        self.scale     = scale

    def normalize_point(self, x, y):
        # Flip Y-axis: invert y relative to bounding box height
        flipped_y = self.y_max_raw - y
        return (x - self.x_min_raw) * self.scale, (flipped_y - self.y_min_raw) * self.scale

    def unnormalize_point(self,x, y):
        unscaled_x = (x / self.scale) + self.x_min_raw
        unflipped_y = self.y_max_raw - ((y / self.scale) + self.y_min_raw)
        return unscaled_x, unflipped_y

    def scale(self,x, y):
        norm_x = (x - self.x_min_raw) / (self.x_max_raw - self.x_min_raw + 1e-6)
        norm_y = (y - self.y_min_raw) / (self.y_max_raw - self.y_min_raw + 1e-6)
        return norm_x * 800, (1 - norm_y) * 800  # flipped Y to match SVG view

    def norm_x(self,x):
        norm = (x - self.x_min_raw) / (self.x_max_raw - self.x_min_raw + 1e-6)
        return norm * 800

    def norm_y(self,y):
        norm = (y - self.y_min_raw) / (self.y_max_raw - self.y_min_raw + 1e-6)
        return (1 - norm) * 800

    def unscale(self, sx, sy):
        norm_x = sx / 800
        norm_y = 1 - (sy / 800)

        x = norm_x * (self.x_max_raw - self.x_min_raw + 1e-6) + self.x_min_raw
        y = norm_y * (self.y_max_raw - self.y_min_raw + 1e-6) + self.y_min_raw
        return x, y