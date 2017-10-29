import pytest


class TestProvider:
    """
    Testing basic provider function and inheritance
    """
    @classmethod
    def setup_class(cls):
        from codev.core.provider import Provider

        class TestProvider(Provider):
            def test(self):
                return 'test'

        cls.TestProvider = TestProvider

        class FooTestProvider(TestProvider):
            provider_name = 'foo'

            def test(self):
                return 'Foo'
        cls.FooTestProvider = FooTestProvider

        class SuperFooTestProvider(FooTestProvider):
            provider_name = 'super_foo'

            def test(self):
                return 'SuperFoo'

        cls.SuperFooTestProvider = SuperFooTestProvider

        class BarTestProvider(TestProvider):
            provider_name = 'bar'

            def test(self):
                return super().test()

        cls.BarTestProvider = BarTestProvider

        class SuperBarFooTestProvider(BarTestProvider, FooTestProvider):
            provider_name = 'super_bar_foo'

            def test(self):
                return super().test()

        cls.SuperBarFooTestProvider = SuperBarFooTestProvider

    def test_foo_provider(self):
        test_provider = self.__class__.TestProvider('foo')
        assert test_provider.__class__, self.__class__.FooTestProvider

    def test_super_foo_provider(self):
        test_provider = self.__class__.TestProvider('super_foo')
        assert test_provider.__class__, self.__class__.SuperFooTestProvider

    def test_bar_provider(self):
        test_provider = self.__class__.TestProvider('bar')
        assert test_provider.__class__, self.__class__.BarTestProvider

    def test_super_bar_foo_provider(self):
        test_provider = self.__class__.TestProvider('super_bar_foo')
        assert test_provider.__class__, self.__class__.SuperBarFooTestProvider


class TestAnotherProvider:
    """
    Testing two distinct providers with same provider_name
    """
    @classmethod
    def setup_class(cls):
        from codev.core.provider import Provider

        class TestProvider(Provider):
            pass

        cls.TestProvider = TestProvider

        class SuperTestProvider(TestProvider):
            provider_name = 'same'

        cls.SuperTestProvider = SuperTestProvider

        class AnotherProvider(Provider):
            pass

        cls.AnotherProvider = AnotherProvider

        class SuperAnotherProvider(AnotherProvider):
            provider_name = 'same'

        cls.SuperAnotherProvider = SuperAnotherProvider

    def test_super_test_provider(self):
        super_test_provider = self.__class__.TestProvider('same')
        assert super_test_provider.__class__, self.__class__.SuperTestProvider

    def test_super_another_provider(self):
        super_another_provider = self.__class__.AnotherProvider('same')
        assert super_another_provider.__class__, self.__class__.SuperAnotherProvider


class TestNotAllowedProvider:
    def test_named_provider(self):
        """
        Testing provider with not allowed set up provider_name
        """
        from codev.core.provider import Provider
        with pytest.raises(ImportError):
            class NamedProvider(Provider):
                provider_name = 'named'

    # def test_not_named_provider(self):
    #     """
    #     Testing provider with not named provider
    #     """
    #     from codev.core.provider import Provider
    #
    #     class TestProvider(Provider):
    #         pass
    #
    #     with pytest.raises(ImportError):
    #         class NotNamedProvider(TestProvider):
    #             pass

    def test_same_named_providers(self):
        """
        Testing providers with same provider_names
        """
        from codev.core.provider import Provider

        class TestProvider(Provider):
            pass

        class FirstProvider(TestProvider):
            provider_name = 'name'

        with pytest.raises(ImportError):
            class SecondProvider(TestProvider):
                provider_name = 'name'

    def test_bad_named_provider(self):
        """
        Testing provider with not named provider
        """
        from codev.core.provider import Provider

        class TestProvider(Provider):
            pass

        with pytest.raises(TypeError):
            class NotNamedProvider(TestProvider):
                provider_name = None
