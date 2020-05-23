from copy import copy, deepcopy
from dataclasses import dataclass
from typing import Optional

from typing_extensions import TypedDict
import pytest

from dynamo_query.data_table import DataTable, DataTableError
from dynamo_query.dynamo_record import DynamoRecord


@dataclass
class UserRecord(DynamoRecord):
    name: str
    age: Optional[int] = None


class TestDataTable:
    @staticmethod
    def test_init() -> None:
        base_dict = {"a": [1, 2, 3], "b": [1, 2]}
        data_table = DataTable.create(base_dict)
        assert data_table["a"] is not base_dict["a"]
        assert data_table["a"] == [1, 2, 3]
        assert data_table["b"] == [1, 2]
        with pytest.raises(KeyError):
            _ = data_table["c"]
        assert data_table == {"a": [1, 2, 3], "b": [1, 2]}

        assert not DataTable.create()
        assert not DataTable.create({"a": []})
        assert DataTable.create({"a": [1]})

        with pytest.raises(DataTableError):
            DataTable.create({"a": "b"})

        with pytest.raises(DataTableError):
            DataTable.create([1, 2, 3])

    @staticmethod
    def test_builtin_copy() -> None:
        base_dict = {"a": [[1, 2, 3]]}
        data_table = DataTable.create(base_dict)

        data_table_copy = copy(data_table)
        assert isinstance(data_table_copy, DataTable)
        assert data_table_copy is not data_table
        assert data_table_copy["a"] is not data_table["a"]
        assert data_table_copy["a"][0] is base_dict["a"][0]

        data_table_deepcopy = deepcopy(data_table)
        assert isinstance(data_table_deepcopy, DataTable)
        assert data_table_deepcopy is not data_table
        assert data_table_deepcopy["a"] is not data_table["a"]
        assert data_table_deepcopy["a"][0] is not base_dict["a"][0]

    @staticmethod
    def test_extend() -> None:
        data_table = DataTable.create({"a": [1], "b": [], "c": [2, 3]})
        assert data_table.extend({"a": [2], "b": [1]}, {"d": [1]}) is data_table
        assert data_table == {"a": [1, 2], "b": [1], "c": [2, 3], "d": [1]}

        data_table = DataTable.create({})
        data_table.extend({"a": [2], "b": [1]}, {"d": [1]}, {})
        assert data_table == {"a": [2], "b": [1], "d": [1]}

        data_table = DataTable.create({})
        with pytest.raises(DataTableError):
            data_table.extend({"d": None})

        with pytest.raises(DataTableError):
            data_table.extend([])

    @staticmethod
    def test_append() -> None:
        data_table = DataTable.create({"a": [1], "b": [], "c": [2, 3]})
        assert data_table.append("a", [2, 3]) is data_table
        assert data_table == {"a": [1, 2, 3], "b": [], "c": [2, 3]}

        data_table = DataTable.create({"a": [1]})
        data_table.append("b", [2, 3])
        assert data_table == {"a": [1], "b": [2, 3]}

        data_table = DataTable({"a": [1]})
        with pytest.raises(DataTableError):
            data_table.append("b", None)

    @staticmethod
    def test_get_lenghts() -> None:
        data_table = DataTable.create({"a": [1, 2, 3], "b": [1, 2]})
        assert data_table["a"] == [1, 2, 3]
        assert data_table["b"] == [1, 2]
        assert data_table.max_length == 3
        assert data_table.min_length == 2
        assert data_table.get_lengths() == [3, 2]
        assert DataTable.create().get_lengths() == []
        assert DataTable.create({"a": [None]}).get_lengths() == [1]

    @staticmethod
    def test_is_normalized() -> None:
        assert DataTable.create({"a": [1, 2], "b": [3, 4]}).is_normalized()
        assert not DataTable.create({"a": [1, 2], "b": [3]}).is_normalized()
        assert not DataTable.create({"a": [1, 2], "b": [3, 4], "c": []}).is_normalized()

    @staticmethod
    def test_resolve_not_set_value() -> None:
        data_table = DataTable.create({"a": [1, 2, 3], "b": [3, 4], "c": []})
        assert data_table.resolve_not_set_value("a", 0) is None

    @staticmethod
    def test_normalize() -> None:
        data_table = DataTable.create({"a": [1, 2, 3], "b": [3, 4], "c": []})
        data_table.normalize()
        assert data_table == {
            "a": [1, 2, 3],
            "b": [3, 4, data_table.NOT_SET],
            "c": [data_table.NOT_SET, data_table.NOT_SET, data_table.NOT_SET],
        }
        assert data_table.get_record(0) == {"a": 1, "b": 3, "c": None}

        data_table = DataTable.create({"a": [1, 2], "b": [3, 4]})
        data_table.normalize()
        assert data_table == {"a": [1, 2], "b": [3, 4]}

    @staticmethod
    def test_filter_keys() -> None:
        data_table = DataTable.create({"a": [1], "b": [2]})
        assert data_table.filter_keys(["a", "b"]) is not data_table
        assert data_table.filter_keys(["a", "b", "c"]) == {"a": [1], "b": [2]}
        assert data_table.filter_keys([]) == {}
        assert data_table.filter_keys(["d"]) == {}

    @staticmethod
    def test_as_defaultdict() -> None:
        data_table = DataTable.create({"a": [1], "b": [2]})
        data_table_as_defaultdict = data_table.as_defaultdict()
        assert data_table_as_defaultdict == {"a": [1], "b": [2]}
        assert data_table_as_defaultdict is not data_table

    @staticmethod
    def test_get_record() -> None:
        data_table = DataTable.create({"a": [1, 2], "b": [3, 4]})
        assert data_table.get_record(0) == {"a": 1, "b": 3}
        assert data_table.get_record(1) == {"a": 2, "b": 4}

        with pytest.raises(DataTableError):
            data_table.get_record(2)

        with pytest.raises(DataTableError):
            DataTable({"a": [1, 2], "b": [3]}).get_record(2)

    @staticmethod
    def test_get_records() -> None:
        data_table = DataTable.create({"a": [1, 2], "b": [3, 4]})
        records = data_table.get_records()
        assert next(records) == {"a": 1, "b": 3}
        assert next(records) == {"a": 2, "b": 4}

        with pytest.raises(StopIteration):
            next(records)

    @staticmethod
    def test_filter_records() -> None:
        data_table = DataTable.create({"a": [1, 2, 1], "b": [3, 4, 5]})
        assert data_table.filter_records({"a": 1}) == {"a": [1, 1], "b": [3, 5]}
        assert data_table.filter_records({"a": 2, "b": 4}) == {"a": [2], "b": [4]}

        assert data_table.filter_records({"a": 1, "b": 4}) == {"a": [], "b": []}

        with pytest.raises(DataTableError):
            DataTable.create({"a": [1, 2, 1], "b": [3, 4]}).filter_records({"a": 1})

    @staticmethod
    def test_add_record() -> None:
        data_table = DataTable.create({"a": [1], "b": [3]})
        result = data_table.add_record({"a": 5, "c": 4}, {"c": 5})
        assert result is data_table
        assert data_table == {
            "a": [1, 5, data_table.NOT_SET],
            "b": [3, data_table.NOT_SET, data_table.NOT_SET],
            "c": [data_table.NOT_SET, 4, 5],
        }

        with pytest.raises(DataTableError):
            DataTable({"a": [1], "b": []}).add_record({"a": 1})

    @staticmethod
    def test_get_column() -> None:
        data_table = DataTable.create({"a": [1, 2], "b": [3, DataTable.NOT_SET]})
        assert data_table.get_column("a") == [1, 2]
        assert data_table.get_column("b") == [3, None]
        assert data_table.get_column("c") == [None, None]

        with pytest.raises(DataTableError):
            DataTable.create({"a": [1], "b": []}).get_column("a")

    @staticmethod
    def test_has_column() -> None:
        data_table = DataTable.create({"a": [1, 2], "b": [3, 4]})
        assert data_table.has_column()
        assert data_table.has_column("a")
        assert data_table.has_column("b")
        assert data_table.has_column("b", "a")
        assert not data_table.has_column("c")
        assert not data_table.has_column("a", "c")

    @staticmethod
    def test_has_set_column() -> None:
        data_table = DataTable.create({"a": [1, 2], "b": [DataTable.NOT_SET, 3]})
        assert data_table.has_set_column()
        assert data_table.has_set_column("a")
        assert not data_table.has_set_column("b")
        assert not data_table.has_set_column("c")
        assert not data_table.has_set_column("b", "a")
        assert not data_table.has_set_column("c")
        assert not data_table.has_set_column("a", "c")

    @staticmethod
    def test_add_table() -> None:
        data_table = DataTable.create({"a": [5], "b": [6]})
        assert DataTable.create({"a": [1, 2], "b": [3, 4]}).add_table(data_table) == {
            "a": [1, 2, 5],
            "b": [3, 4, 6],
        }
        assert DataTable({"a": [1, 2], "b": [3, 4]}).add_table(
            data_table, data_table
        ) == {"a": [1, 2, 5, 5], "b": [3, 4, 6, 6],}

        with pytest.raises(DataTableError):
            DataTable.create({"a": [1, 2], "b": [3, 4]}).add_table(
                DataTable.create({"a": [5], "b": []})
            )

        with pytest.raises(DataTableError):
            DataTable({"a": [5], "b": []}).add_table(data_table)

    @staticmethod
    def test_get_set_column_names() -> None:
        data_table = DataTable.create({"a": [1], "b": [DataTable.NOT_SET], "c": []})
        assert data_table.get_set_column_names() == ["a", "c"]
        data_table.normalize()
        assert data_table.get_set_column_names() == ["a"]

    @staticmethod
    def test_get_column_names() -> None:
        data_table = DataTable.create({"a": [1], "b": [DataTable.NOT_SET], "c": []})
        assert data_table.get_column_names() == ["a", "b", "c"]

    @staticmethod
    def test_set() -> None:
        data_table = DataTable.create({"a": [1, 2], "b": [DataTable.NOT_SET]})
        result = data_table.set("a", 1, "value_a").set("b", 0, "value_b")
        assert result is data_table
        assert data_table == DataTable({"a": [1, "value_a"], "b": ["value_b"]})

        with pytest.raises(DataTableError):
            data_table.set("b", 1, "value_b")

        with pytest.raises(DataTableError):
            data_table.set("c", 0, "value_c")

    @staticmethod
    def test_typed() -> None:
        class MyRecord(TypedDict):
            key: str

        data_table = DataTable[MyRecord]()
        data_table.add_record({"key": "value"})
        data_table.add_record({"wrong_key": "value"})
        assert data_table

    def test_custom_record(self):
        data_table = DataTable[UserRecord](record_type=UserRecord)
        data_table.add_record({"name": "Jon"})
        data_table.add_record(UserRecord(name="test", age=12))
        assert isinstance(data_table.get_record(0), UserRecord)
        assert list(data_table.get_records()) == [
            UserRecord(name="Jon"),
            UserRecord(name="test", age=12),
        ]

        with pytest.raises(TypeError):
            data_table.add_record({"unknown": "Jon"})

        with pytest.raises(TypeError):
            data_table.add_record({})

        with pytest.raises(ValueError):
            data_table.add_record({"name": 12})
