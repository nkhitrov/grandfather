import pytest

from src.base import context, meta_context, _inspector_registry


@pytest.fixture(autouse=True)
def reset_global_state():
    _inspector_registry.clear()


class TestLookOutDecorator:
    @staticmethod
    def test_when_class_has_functions_with_params():
        state = []

        def hook(*args, **kwargs):
            state.append((args, kwargs))

        @context(pre_hook=hook)
        class UserService:
            @staticmethod
            def static_method(*args, **kwargs):
                return args, kwargs

            @classmethod
            def class_method(cls, *args, **kwargs):
                return cls.__name__, args, kwargs

            def instance_method(self, *args, **kwargs):
                return self.__class__.__name__, args, kwargs

        service = UserService()

        assert service.instance_method(1, 2, a=3, b="4") == (
            "UserService",
            (1, 2),
            {"a": 3, "b": "4"},
        )
        assert UserService.class_method(5, 6, c=7, d=8) == (
            "UserService",
            (5, 6),
            {"c": 7, "d": 8},
        )
        assert UserService.static_method(9, 10, a=11, d=12) == (
            (9, 10),
            {"a": 11, "d": 12},
        )

        assert state == [
            ((1, 2), {"a": 3, "b": "4"}),
            ((6,), {"c": 7, "d": 8}),
            ((10,), {"a": 11, "d": 12}),
        ]

    @staticmethod
    def test_when_class_has_functions_without_params():
        state = []

        def hook(*args, **kwargs):
            state.append((args, kwargs))

        @context(pre_hook=hook)
        class UserService:
            @staticmethod
            def empty_static_method():
                return

            @classmethod
            def empty_class_method(cls):
                return cls.__name__

            def empty_instance_method(self):
                return self.__class__.__name__

        service = UserService()

        assert service.empty_instance_method() == "UserService"
        assert UserService.empty_class_method() == "UserService"
        assert UserService.empty_static_method() is None


class TestLookOutFor:
    @staticmethod
    def test_when_class_has_functions_with_params():
        state = []

        def hook(*args, **kwargs):
            state.append((args, kwargs))

        class BaseService(metaclass=meta_context(pre_hook=hook)):
            pass

        class UserService(BaseService):
            @staticmethod
            def static_method(*args, **kwargs):
                return args, kwargs

            @classmethod
            def class_method(cls, *args, **kwargs):
                return cls.__name__, args, kwargs

            def instance_method(self, *args, **kwargs):
                return self.__class__.__name__, args, kwargs

        service = UserService()

        assert service.instance_method(1, 2, a=3, b="4") == (
            "UserService",
            (1, 2),
            {"a": 3, "b": "4"},
        )
        assert UserService.class_method(5, 6, c=7, d=8) == (
            "UserService",
            (5, 6),
            {"c": 7, "d": 8},
        )
        assert UserService.static_method(9, 10, a=11, d=12) == (
            (9, 10),
            {"a": 11, "d": 12},
        )

        assert state == [
            ((1, 2), {"a": 3, "b": "4"}),
            ((6,), {"c": 7, "d": 8}),
            ((10,), {"a": 11, "d": 12}),
        ]

    @staticmethod
    def test_when_class_has_functions_without_params():
        state = []

        def hook(*args, **kwargs):
            state.append((args, kwargs))

        class BaseService(metaclass=meta_context(pre_hook=hook)):
            pass

        class UserService(BaseService):
            @staticmethod
            def empty_static_method():
                return

            @classmethod
            def empty_class_method(cls):
                return cls.__name__

            def empty_instance_method(self):
                return self.__class__.__name__

        service = UserService()

        assert service.empty_instance_method() == "UserService"
        assert UserService.empty_class_method() == "UserService"
        assert UserService.empty_static_method() is None


def test_class_tree():
    class UserContext(metaclass=meta_context()):
        pass

    class UserService(UserContext):
        pass

    class UserRepo(UserContext):
        pass

    class User(UserContext):
        pass

    class SpecialUser(User):
        pass

    assert dict(_inspector_registry) == {
        UserContext: {"inspector": UserContext},
        UserService: {"inspector": UserContext},
        UserRepo: {"inspector": UserContext},
        User: {"inspector": UserContext},
        SpecialUser: {"inspector": UserContext},
    }


def test_class_tree_when_different_meta():
    class UserContext(metaclass=meta_context()):
        pass

    class CatalogContext(metaclass=meta_context()):
        pass

    class UserService(UserContext):
        pass

    class UserRepo(UserContext):
        pass

    class CatalogService(CatalogContext):
        pass

    class CatalogRepo(CatalogContext):
        pass

    assert dict(_inspector_registry) == {
        UserContext: {"inspector": UserContext},
        CatalogContext: {"inspector": CatalogContext},
        UserService: {"inspector": UserContext},
        UserRepo: {"inspector": UserContext},
        CatalogService: {"inspector": CatalogContext},
        CatalogRepo: {"inspector": CatalogContext},
    }


def test_collect_graf():
    class UserContext(metaclass=meta_context()):
        pass

    class CatalogContext(metaclass=meta_context()):
        pass

    class UserRepo(UserContext):
        pass

    class UserService(UserContext):
        user_repo: UserRepo

    class CatalogRepo(CatalogContext):
        pass

    class CatalogService(CatalogContext):
        def __init__(self, catalog_repo: CatalogRepo):
            self.catalog_repo = catalog_repo

    assert dict(_inspector_registry) == {
        UserContext: {"inspector": UserContext},
        CatalogContext: {"inspector": CatalogContext},
        UserService: {"inspector": UserContext},
        UserRepo: {"inspector": UserContext},
        CatalogService: {"inspector": CatalogContext},
        CatalogRepo: {"inspector": CatalogContext},
    }


class TestUsingClassFromDifferentContext:
    @staticmethod
    def test_returns_error_when_target_class_specified_in_annotations():
        class UserContext(metaclass=meta_context()):
            pass

        class CatalogContext(metaclass=meta_context()):
            pass

        class CatalogService(CatalogContext):
            pass

        with pytest.raises(TypeError) as exc_info:

            class UserService(UserContext):
                catalog_service: CatalogService

        assert (
            str(exc_info.value)
            == "Class 'CatalogService' can not be used in context 'UserContext' because it "
            "used in context 'CatalogContext'"
        )

    @staticmethod
    def test_returns_error_when_target_class_specified_in_init():
        class UserContext(metaclass=meta_context()):
            pass

        class CatalogContext(metaclass=meta_context()):
            pass

        class CatalogService(CatalogContext):
            pass

        with pytest.raises(TypeError) as exc_info:
            class UserService(UserContext):
                def __init__(self, catalog_service: CatalogService):
                    self.catalog_service = catalog_service

        assert (
            str(exc_info.value)
            == "Class 'CatalogService' can not be used in context 'UserContext' because it "
            "used in context 'CatalogContext'"
        )

    @staticmethod
    def test_returns_ok_when_target_class_():
        class UserContext(metaclass=meta_context()):
            pass

        class CatalogContext(metaclass=meta_context(subcontexts=[UserContext])):
            pass

        class UserService(UserContext):
            pass

        class CatalogService(CatalogContext):
            user_service: UserService

            def __init__(self, user_service: UserService):
                self.user_service = user_service
