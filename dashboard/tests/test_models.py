from src.models import K8sNamespaces


class TestModels:
    def test_K8sResources(self):
        ret = K8sNamespaces(namespaces=["foo", "bar"])
        assert ret.namespaces == ["foo", "bar"]
