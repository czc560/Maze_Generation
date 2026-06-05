"""MoveAnimation: helper for smooth grid-based movement between cells."""

from __future__ import annotations


class MoveAnimation:
    """Linearly interpolates a position from one grid cell to another.

    The interpolation is done in grid-coordinate space (float row, float col),
    which the caller maps to screen pixels via cell_size.
    """

    def __init__(
        self,
        from_pos: tuple[int, int],
        to_pos: tuple[int, int],
        duration: float = 0.12,
    ) -> None:
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.duration = duration
        self.elapsed = 0.0
        self.finished = False

    def update(self, dt: float) -> bool:
        """Advance the animation. Returns True when finished."""
        if self.finished:
            return True
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.finished = True
        return self.finished

    def current_pos(self) -> tuple[float, float]:
        """Return the interpolated (row, col) as floats."""
        t = self.elapsed / self.duration if self.duration > 0 else 1.0
        # Smooth-step easing
        t = t * t * (3 - 2 * t)
        fr, fc = self.from_pos
        tr, tc = self.to_pos
        return (fr + (tr - fr) * t, fc + (tc - fc) * t)
