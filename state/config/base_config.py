class BaseConfig:
    def _validate(self):
        klass = type(self)
        for name, val in vars(klass).items():
            if isinstance(val, property):
                try:
                    getattr(self, name)
                except KeyError as e:
                    raise KeyError(f"{klass.__name__}: missing key {e}") from None
