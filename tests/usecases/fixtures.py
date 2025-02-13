import pytest
from unittest.mock import MagicMock
from usecases.telegram.get_content_tg_usecase import GetContentTgUseCase


@pytest.fixture
def mock_gateway():
    return MagicMock()


@pytest.fixture
def mock_nlp_processor():
    return MagicMock()


@pytest.fixture
def usecase(mock_gateway, mock_nlp_processor):
    return GetContentTgUseCase(gateway=mock_gateway, nlp_processor=mock_nlp_processor)
