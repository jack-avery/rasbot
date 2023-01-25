class OsuAPIv2Helper:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(OsuAPIv2Helper, cls).__new__(cls)
        return cls.instance
