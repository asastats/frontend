"""Testing module for :py:mod:`api.serializers` module."""

import inspect

import pytest
from rest_framework.relations import ManyRelatedField
from rest_framework.serializers import (
    BooleanField,
    CharField,
    ChoiceField,
    DecimalField,
    IntegerField,
    ListField,
    ListSerializer,
    Serializer,
    StringRelatedField,
    URLField,
)

import api.serializers
import api.structs


def _get_serializers():
    for name, obj in inspect.getmembers(api.serializers):
        if inspect.isclass(obj) and name.endswith("Serializer"):
            yield obj


class TestApiSerializers:
    """Testing class for :py:mod:`api.serializers` serializer classes."""

    # # Serializer
    @pytest.mark.parametrize(
        "klass",
        _get_serializers(),
    )
    def test_api_serializer_is_subclass_of_serializer(self, klass):
        assert issubclass(klass, Serializer)

    @pytest.mark.parametrize(
        "name",
        [
            "AccountInfo",
            "AsaItem",
            "AsaItemProgram",
            "AsaProgram",
            "AsaLink",
            "Distribution",
            "DistributionLink",
            "Entities",
            "NftCollection",
            "NftItem",
            "Nft",
            "NftCurrency",
            "NftListing",
            "NftPurchase",
            "NftTrait",
            "NftUrl",
            "Provider",
            "SystemInfo",
            "Total",
        ],
    )
    def test_api_serializer_has_all_fields_from_related_named_tuple(self, name):
        serializer = getattr(api.serializers, f"{name}Serializer")
        named_tuple = getattr(api.structs, name)
        assert all(
            field in serializer._declared_fields for field in named_tuple._fields
        )

    @pytest.mark.parametrize("klass", _get_serializers())
    def test_api_serializer_assigns_valid_field_type(self, klass):
        assert all(
            issubclass(
                instance.__class__,
                (
                    BooleanField,
                    CharField,
                    ChoiceField,
                    DecimalField,
                    IntegerField,
                    ListField,
                    ListSerializer,
                    ManyRelatedField,
                    Serializer,
                    StringRelatedField,
                    URLField,
                ),
            )
            for _, instance in klass._declared_fields.items()
        )


class TestApiSerializersProvider:
    """Testing class for :py:class:`api.serializers.ProviderSerializer`."""

    def test_api_serializers_providerserializer_to_representation_filters_none(
        self, mocker
    ):
        mocker.patch.object(
            Serializer, "to_representation", return_value={"a": 1, "b": None}
        )
        returned = api.serializers.ProviderSerializer().to_representation(object())
        assert returned == {"a": 1}


class TestApiSerializersRepresentation:
    """Testing class for :py:mod:`api.serializers` serializer representation."""

    # # AsaProgramSerializer
    def test_api_serializer_asaprogramserializer_omits_empty_values(self):
        struct = api.structs.AsaProgram(code="code")
        serializer = api.serializers.AsaProgramSerializer(struct)
        assert serializer.data == {"code": "code"}
        assert all(
            field in api.serializers.AsaProgramSerializer._declared_fields
            for field in (
                "type",
                "name",
                "provider",
                "url",
                "code",
            )
        )

    # # LinkedDataSerializer
    def test_api_serializer_linkeddataserializer_omits_empty_values(self):
        struct = api.structs.LinkedData(text="Available", value=50.0)
        serializer = api.serializers.LinkedDataSerializer(struct)
        assert serializer.data == {"text": "Available", "value": "50.000000"}
        assert all(
            field in api.serializers.LinkedDataSerializer._declared_fields
            for field in (
                "provider",
                "text",
                "link",
                "value",
                "amount",
                "balance",
                "info",
                "id",
            )
        )

    # # AsaItemProgramSerializer
    def test_api_serializer_asaitemprogramserializer_omits_empty_values(self):
        program_struct = api.structs.AsaProgram(code="programcode")
        struct = api.structs.AsaItemProgram(
            program=program_struct, value=100.0, amount=5
        )
        serializer = api.serializers.AsaItemProgramSerializer(struct)
        assert serializer.data == {
            "program": {"code": "programcode"},
            "value": "100.000000",
            "amount": 5,
        }
        assert all(
            field in api.serializers.AsaItemProgramSerializer._declared_fields
            for field in (
                "program",
                "value",
                "amount",
                "proxy",
                "distribution",
                "linked",
            )
        )

    # # NftSerializer
    def test_api_serializer_nftserializer_omits_empty_values(self):
        struct = api.structs.Nft(
            id=505,
            name="name",
            unit=None,
            total=None,
            decimals=None,
            creator=None,
            image=None,
            thumbnail=None,
            urls=None,
            listings=None,
            floor=None,  # TODO: will be removed
            last_purchase=None,
            max_purchase=None,
            title=None,
            description=None,
            rarity=None,
            traits=None,
        )
        serializer = api.serializers.NftSerializer(struct)
        assert serializer.data == {
            "id": 505,
            "name": "name",
            "unit": None,
        }
        assert all(
            field in api.serializers.NftSerializer._declared_fields
            for field in (
                "id",
                "name",
                "unit",
                "total",
                "decimals",
                "creator",
                "image",
                "thumbnail",
                "urls",
                "listings",
                "floor",  # TODO: will be removed
                "last_purchase",
                "max_purchase",
                "title",
                "description",
                "traits",
            )
        )

    # # SystemInfoSerializer
    def test_api_serializer_systeminfoserializer_omits_empty_values(self):
        struct = api.structs.SystemInfo()
        serializer = api.serializers.SystemInfoSerializer(struct)
        assert serializer.data == {}
        assert all(
            field in api.serializers.SystemInfoSerializer._declared_fields
            for field in ("warning", "information")
        )

    def test_api_serializer_systeminfoserializer_omits_empty_value(self):
        struct = api.structs.SystemInfo(warning="warning")
        serializer = api.serializers.SystemInfoSerializer(struct)
        assert serializer.data == {"warning": "warning"}
        assert all(
            field in api.serializers.SystemInfoSerializer._declared_fields
            for field in ("warning", "information")
        )
