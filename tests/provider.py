import unittest


class ProviderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from codev.provider import Provider

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
                return super(BarTestProvider, self).test()

        cls.BarTestProvider = BarTestProvider

        class SuperBarFooTestProvider(BarTestProvider, FooTestProvider):
            provider_name = 'super_bar_foo'

            def test(self):
                return super(SuperBarFooTestProvider, self).test()

        cls.SuperBarFooTestProvider = SuperBarFooTestProvider

    def test_foo_provider(self):
        test_provider = self.__class__.TestProvider('foo')
        self.assertEqual(test_provider.__class__, self.__class__.FooTestProvider)

    def test_super_foo_provider(self):
        test_provider = self.__class__.TestProvider('super_foo')
        self.assertEqual(test_provider.__class__, self.__class__.SuperFooTestProvider)

    def test_bar_provider(self):
        test_provider = self.__class__.TestProvider('bar')
        self.assertEqual(test_provider.__class__, self.__class__.BarTestProvider)

    def test_super_bar_foo_provider(self):
        test_provider = self.__class__.TestProvider('super_bar_foo')
        self.assertEqual(test_provider.__class__, self.__class__.SuperBarFooTestProvider)

if __name__ == '__main__':
    unittest.main()
