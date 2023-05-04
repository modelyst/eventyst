#   Copyright 2022 Modelyst LLC
#   All Rights Reserved


def test_dependency_injection():
    def fake_dependency():
        return "fake dependency"

    def fake_handler(dependency=Dependency(fake_dependency)):
        return dependency
