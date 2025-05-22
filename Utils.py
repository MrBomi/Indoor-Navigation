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