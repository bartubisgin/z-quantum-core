"""Test cases for serialization module."""
import json
import numpy as np
import os

import pytest

from .history.recorder import HistoryEntry, HistoryEntryWithArtifacts
from .utils import convert_array_to_dict, ValueEstimate, SCHEMA_VERSION
from .interfaces.optimizer import optimization_result
from .serialization import ZapataEncoder, ZapataDecoder, save_optimization_results
from .bitstring_distribution import BitstringDistribution


def history_entries_equal(entry_1, entry_2):
    """Compare entry_1 and entry_2 assuming theyir params are of np.array type."""
    if entry_1.call_number != entry_2.call_number:
        return False
    elif entry_1.value != entry_2.value:
        return False
    elif not np.array_equal(entry_1.params, entry_2.params):
        return False
    elif hasattr(entry_1, "artifacts") != hasattr(entry_2, "artifacts"):
        return False
    else:
        return getattr(entry_1, "artifacts", None) == getattr(entry_2, "artifacts", None)


def test_zapata_encoder_can_handle_numpy_arrays():
    dict_to_serialize = {
        "array_1": np.array([1, 2, 3]),
        "array_2": np.array([0.5 + 1j, 0.5 - 0.25j]),
        "list_of_arrays": [np.array([0.5, 0.4, 0.3]), np.array([1, 2, 3])],
    }

    deserialized_dict = json.loads(json.dumps(dict_to_serialize, cls=ZapataEncoder))
    expected_deserialized_dict = {
        "array_1": convert_array_to_dict(dict_to_serialize["array_1"]),
        "array_2": convert_array_to_dict(dict_to_serialize["array_2"]),
        "list_of_arrays": [
            convert_array_to_dict(arr) for arr in dict_to_serialize["list_of_arrays"]
        ],
    }
    assert deserialized_dict == expected_deserialized_dict


def test_zapata_encoder_can_handle_optimization_result():
    # The result constructed below does not make sense.
    # It does not matter though, as we are only testing serialization and it contains variety
    # of data to be serialized.
    result_to_serialize = optimization_result(
        opt_value=0.5,
        opt_params=np.array([0, 0.5, 2.5]),
        nit=3,
        fev=10,
        history=[
            HistoryEntry(
                call_number=0,
                params=np.array([0.1, 0.2, 0.3j]),
                value=ValueEstimate(0.5, precision=6),
            ),
            HistoryEntry(call_number=1, params=np.array([1, 2, 3]), value=-10.0),
            HistoryEntryWithArtifacts(
                call_number=2,
                params=np.array([-1, -0.5, -0.6]),
                value=-20.0,
                artifacts={
                    "bitstring": "0111",
                    "bitstring_distribution": BitstringDistribution(
                        {"111": 0.25, "010": 0.75}
                    ),
                },
            ),
        ],
    )

    expected_deserialized_result = {
        "opt_value": 0.5,
        "opt_params": convert_array_to_dict(np.array([0, 0.5, 2.5])),
        "nit": 3,
        "fev": 10,
        "history": [
            {
                "call_number": 0,
                "params": convert_array_to_dict(np.array([0.1, 0.2, 0.3j])),
                "value": ValueEstimate(0.5, precision=6).to_dict(),
            },
            {
                "call_number": 1,
                "params": convert_array_to_dict(np.array([1, 2, 3])),
                "value": -10.0,
            },
            {
                "call_number": 2,
                "params": convert_array_to_dict(np.array([-1, -0.5, -0.6])),
                "value": -20.0,
                "artifacts": {
                    "bitstring": "0111",
                    "bitstring_distribution": {"111": 0.25, "010": 0.75},
                },
            },
        ],
    }

    deserialized_result = json.loads(json.dumps(result_to_serialize, cls=ZapataEncoder))

    assert deserialized_result == expected_deserialized_result


def test_optimization_result_serialization_io():
    # The result constructed below does not make sense.
    # It does not matter though, as we are only testing serialization and it contains variety
    # of data to be serialized.
    result_to_serialize = optimization_result(
        opt_value=0.5,
        opt_params=np.array([0, 0.5, 2.5]),
        nit=3,
        fev=10,
        history=[
            HistoryEntry(
                call_number=0,
                params=np.array([0.1, 0.2, 0.3j]),
                value=ValueEstimate(0.5, precision=6),
            ),
            HistoryEntry(call_number=1, params=np.array([1, 2, 3]), value=-10.0),
            HistoryEntryWithArtifacts(
                call_number=2,
                params=np.array([-1, -0.5, -0.6]),
                value=-20.0,
                artifacts={
                    "bitstring": "0111",
                    "bitstring_distribution": BitstringDistribution(
                        {"111": 0.25, "010": 0.75}
                    ),
                },
            ),
        ],
    )

    expected_deserialized_result = {
        "schema": SCHEMA_VERSION + "-optimization_result",
        "opt_value": 0.5,
        "opt_params": convert_array_to_dict(np.array([0, 0.5, 2.5])),
        "nit": 3,
        "fev": 10,
        "history": [
            {
                "call_number": 0,
                "params": convert_array_to_dict(np.array([0.1, 0.2, 0.3j])),
                "value": ValueEstimate(0.5, precision=6).to_dict(),
            },
            {
                "call_number": 1,
                "params": convert_array_to_dict(np.array([1, 2, 3])),
                "value": -10.0,
            },
            {
                "call_number": 2,
                "params": convert_array_to_dict(np.array([-1, -0.5, -0.6])),
                "value": -20.0,
                "artifacts": {
                    "bitstring": "0111",
                    "bitstring_distribution": {"111": 0.25, "010": 0.75},
                },
            },
        ],
    }

    optimization_result_filename = "test-optimization-result-io.json"

    # When
    save_optimization_results(result_to_serialize, optimization_result_filename)

    # Then
    with open(optimization_result_filename, "r") as f:
        loaded_data = json.load(f)

    assert loaded_data == expected_deserialized_result

    os.remove(optimization_result_filename)


def test_zapata_decoder_can_load_numpy_arrays():
    dict_of_arrays = {
        "array_1": {"real": [1, 2, 3, 4]},
        "array_2": {"real": [0.5, 0.25, 0], "imag": [0, 0.25, 0.5]},
        "array_3": {"real": [[1.5, 2.5], [0.5, 0.5]], "imag": [[0.5, -0.5], [1.0, 2.0]]}
    }

    expected_deserialized_object = {
        "array_1": np.array([1, 2, 3, 4]),
        "array_2": np.array([0.5, 0.25 + 0.25j, 0.5j]),
        "array_3": np.array([[1.5 + 0.5j, 2.5 - 0.5j], [0.5 + 1.0j, 0.5 + 2.0j]])
    }
    deserialized_object = json.loads(json.dumps(dict_of_arrays), cls=ZapataDecoder)

    for key in dict_of_arrays:
        assert np.array_equal(deserialized_object[key], expected_deserialized_object[key])


@pytest.mark.parametrize(
    "value_estimate",
    [
        ValueEstimate(-2.5, 0.125),
        ValueEstimate(0.5)
    ]
)
def test_zapata_decoder_can_load_value_estimate(value_estimate):
    serialized_value_estimate = json.dumps(value_estimate.to_dict())
    assert value_estimate == json.loads(serialized_value_estimate, cls=ZapataDecoder)


@pytest.mark.parametrize(
    "history_entry",
    [
        HistoryEntry(call_number=9, value=-20.0, params=np.array([0.2, 0.3])),
        HistoryEntry(call_number=1, value=-15.5, params=np.array([0.5, 0.4, 0.1])),
        HistoryEntryWithArtifacts(
            call_number=10,
            value=0.25,
            params=np.array([-0.1, 0.2, -1.2]),
            artifacts={
                "bitstring": "111010",
                "bitstring_distribution": {"111": 0.25, "010": 0.75}
            }
        )
    ]
)
def test_zapata_decoder_successfully_loads_history_entry_objects(history_entry):
    serialized_history_entry = json.dumps(history_entry, cls=ZapataEncoder)
    deserialized_history_entry = json.loads(serialized_history_entry, cls=ZapataDecoder)
    assert history_entry.call_number == deserialized_history_entry.call_number
    assert history_entry.value == deserialized_history_entry.value
    assert np.array_equal(history_entry.params, deserialized_history_entry.params)
    assert history_entries_equal(history_entry, deserialized_history_entry)
