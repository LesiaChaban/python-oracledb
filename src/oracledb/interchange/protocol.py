# -----------------------------------------------------------------------------
# MIT License

# Copyright (c) 2025 Consortium for Python Data API Standards contributors

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# protocol.py
#
# Implement DataFrame class as documented in the standard
# https://data-apis.org/dataframe-protocol/latest/API.html
# -----------------------------------------------------------------------------

from enum import IntEnum
from typing import (
    Any,
    ClassVar,
    Literal,
    Protocol,
    Tuple,
    TypedDict,
)

from collections.abc import Iterable, Sequence


class DlpackDeviceType(IntEnum):
    """Integer enum for device type codes matching DLPack."""

    CPU = 1
    CUDA = 2
    CPU_PINNED = 3
    OPENCL = 4
    VULKAN = 7
    METAL = 8
    VPI = 9
    ROCM = 10


class DtypeKind(IntEnum):
    """
    Integer enum for data types.

    Attributes
    ----------
    INT : int
        Matches to signed integer data type.
    UINT : int
        Matches to unsigned integer data type.
    FLOAT : int
        Matches to floating point data type.
    BOOL : int
        Matches to boolean data type.
    STRING : int
        Matches to string data type (UTF-8 encoded).
    DATETIME : int
        Matches to datetime data type.
    CATEGORICAL : int
        Matches to categorical data type.
    """

    INT = 0
    UINT = 1
    FLOAT = 2
    BOOL = 20
    STRING = 21  # UTF-8
    DATETIME = 22
    CATEGORICAL = 23
    DECIMAL = 24


Dtype = Tuple[DtypeKind, int, str, str]  # see Column.dtype


class ColumnNullType(IntEnum):
    """
    Integer enum for null type representation.

    Attributes
    ----------
    NON_NULLABLE : int
        Non-nullable column.
    USE_NAN : int
        Use explicit float NaN value.
    USE_SENTINEL : int
        Sentinel value besides NaN.
    USE_BITMASK : int
        The bit is set/unset representing a null on a certain position.
    USE_BYTEMASK : int
        The byte is set/unset representing a null on a certain position.
    """

    NON_NULLABLE = 0
    USE_NAN = 1
    USE_SENTINEL = 2
    USE_BITMASK = 3
    USE_BYTEMASK = 4


class ColumnBuffers(TypedDict):
    """Buffers backing a column."""

    # first element is a buffer containing the column data;
    # second element is the data buffer's associated dtype
    data: Tuple["Buffer", "Dtype"]

    # first element is a buffer containing mask values indicating missing data;
    # second element is the mask value buffer's associated dtype.
    # None if the null representation is not a bit or byte mask
    validity: Tuple["Buffer", "Dtype"]

    # first element is a buffer containing the offset values for
    # variable-size binary data (e.g., variable-length strings);
    # second element is the offsets buffer's associated dtype.
    # None if the data buffer does not have an associated offsets buffer
    offsets: Tuple["Buffer", "Dtype"]


class CategoricalDescription(TypedDict):
    """Description of a categorical column."""

    # whether the ordering of dictionary indices is semantically meaningful
    is_ordered: bool
    # whether a dictionary-style mapping of categorical values to other objects
    # exists
    is_dictionary: Literal[True]
    # Python-level only (e.g. `{int: str}`).
    # None if not a dictionary-style categorical.
    categories: "Column"


class Buffer(Protocol):
    """Interchange buffer object."""

    @property
    def bufsize(self) -> int:
        """Buffer size in bytes."""

    @property
    def ptr(self) -> int:
        """Pointer to start of the buffer as an integer."""

    def __dlpack__(self) -> Any:
        """Represent this structure as DLPack interface."""

    def __dlpack_device__(self) -> Tuple["DlpackDeviceType", int | None]:
        """Device type and device ID for where the data in the buffer
        resides."""


class Column(Protocol):
    """Interchange column object."""

    def size(self) -> int:
        """Size of the column in elements."""

    @property
    def offset(self) -> int:
        """Offset of the first element with respect to the start
        of the underlying buffer."""  # noqa: W505

    @property
    def dtype(self) -> "Dtype":
        """Data type of the column."""

    @property
    def describe_categorical(self) -> "CategoricalDescription":
        """Description of the categorical data type of the column."""

    @property
    def describe_null(self) -> Tuple["ColumnNullType", Any]:
        """Description of the null representation the column uses."""

    @property
    def null_count(self) -> int | None:
        """Number of null elements, if known."""

    @property
    def metadata(self) -> dict[str, Any]:
        """The metadata for the column."""

    def num_chunks(self) -> int:
        """Return the number of chunks the column consists of."""

    def get_chunks(self, n_chunks: int | None = None) -> Iterable["Column"]:
        """Return an iterator yielding the column chunks."""

    def get_buffers(self) -> "ColumnBuffers":
        """Return a dictionary containing the underlying buffers."""


class DataFrame(Protocol):
    """Interchange dataframe object."""

    version: ClassVar[int]  # Version of the protocol

    def __dataframe__(
        self,
        nan_as_null: bool = False,  # noqa: FBT001
        allow_copy: bool = True,  # noqa: FBT001
    ) -> "DataFrame":
        """Convert to a dataframe object implementing the dataframe
        interchange protocol."""  # noqa: W505

    @property
    def metadata(self) -> dict[str, Any]:
        """The metadata for the dataframe."""

    def num_columns(self) -> int:
        """Return the number of columns in the dataframe."""

    def num_rows(self) -> int | None:
        """Return the number of rows in the dataframe, if available."""

    def num_chunks(self) -> int:
        """Return the number of chunks the dataframe consists of.."""

    def column_names(self) -> Iterable[str]:
        """Return the column names."""

    def get_column(self, i: int) -> "Column":
        """Return the column at the indicated position."""

    def get_column_by_name(self, name: str) -> "Column":
        """Return the column with the given name."""

    def get_columns(self) -> Iterable["Column"]:
        """Return an iterator yielding the columns."""

    def select_columns(self, indices: Sequence[int]) -> "DataFrame":
        """Create a new dataframe by selecting a subset of columns by index."""

    def select_columns_by_name(self, names: Sequence[str]) -> "DataFrame":
        """Create a new dataframe by selecting a subset of columns by name."""

    def get_chunks(self, n_chunks: int | None = None) -> Iterable["DataFrame"]:
        """Return an iterator yielding the chunks of the dataframe."""


class SupportsInterchange(Protocol):
    """Dataframe that supports conversion into an interchange
    dataframe object."""

    def __dataframe__(
        self,
        nan_as_null: bool = False,  # noqa: FBT001
        allow_copy: bool = True,  # noqa: FBT001
    ) -> "SupportsInterchange":
        """Convert to a dataframe object implementing the dataframe
        interchange protocol."""  # noqa: W505


class Endianness:
    """Enum indicating the byte-order of a data type."""

    LITTLE = "<"
    BIG = ">"
    NATIVE = "="
    NA = "|"


class CopyNotAllowedError(RuntimeError):
    """Exception raised when a copy is required,
    but `allow_copy` is set to `False`."""
