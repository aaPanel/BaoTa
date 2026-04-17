try:
    from webauthn_util import WebAuthn
except:
    class WebAuthn:
        fake = True

        @classmethod
        def is_enabled(cls) -> bool:
            return False