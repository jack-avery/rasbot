class OsuAPIv2Helper:
    instance = False
    """The single OsuAPIv2Helper to use to enforce credential consistency between all osu! modules."""

    def __init__(self):
        """Get the currently active instance of an `OsuAPIv2Helper`,
        or create one if one doesn't exist yet.
        """
        # enforce singleton status
        if OsuAPIv2Helper.instance:
            self = OsuAPIv2Helper.instance
            return
        OsuAPIv2Helper.instance = self
