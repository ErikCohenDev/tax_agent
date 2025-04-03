"""
Tests for the Tax Agent implementation.
"""

from unittest.mock import patch, Mock
import pytest

from src.agent import TaxAgent


@pytest.fixture
def mock_tax_code():
    """Fixture for mock tax code content."""
    return """
# Title 26 - Internal Revenue Code

## §63 Taxable Income Defined

### §63(c) Standard Deduction

**(c) Standard deduction** For purposes of this subtitle—

**(1) In general** Except as otherwise provided in this subsection, the term "standard deduction" means the sum of—
**(A)** the basic standard deduction, and
**(B)** the additional standard deduction.

**(2) Basic standard deduction** For purposes of paragraph (1), the basic standard deduction is—
**(A)** $5,000 in the case of—
**(i)** a joint return, or
**(ii)** a surviving spouse (as defined in section 2(a)),
**(B)** $4,400 in the case of a head of household (as defined in section 2(b)), or
**(C)** $3,000 in the case of an individual who is not married and who is not a surviving spouse or head of household or
**(D)** $2,500 in the case of a married individual filing a separate return.
    """


@pytest.fixture
def tax_agent(mock_tax_code):
    """Create a tax agent with mock tax code for testing."""
    with patch("builtins.open", Mock()):
        with patch("os.path.exists", return_value=True):
            agent = TaxAgent()
            agent.tax_code_content = mock_tax_code
            return agent


def test_extract_key_terms():
    """Test extraction of key terms from a question."""
    agent = TaxAgent()

    # Test with tax-specific terms
    terms = agent._extract_key_terms("What is the standard deduction amount?")
    assert "deduction" in terms

    # Test with non-tax terms
    terms = agent._extract_key_terms("How do I calculate this?")
    assert len(terms) > 0
    assert "calculate" in terms


def test_find_relevant_sections(tax_agent):
    """Test finding relevant sections in the tax code."""
    sections = tax_agent._find_relevant_sections("What is the standard deduction amount?")

    assert len(sections) > 0
    assert any("§63" in section["heading"] for section in sections)


def test_extract_citation():
    """Test extraction of citations from headings."""
    agent = TaxAgent()

    citation = agent._extract_citation("## §63 Taxable Income Defined")
    assert citation == "26 USC §63 [Taxable Income Defined]"

    citation = agent._extract_citation("### §63(c) Standard Deduction")
    assert citation == "26 USC §63(c) [Standard Deduction]"


@patch("ollama.chat")
def test_query(mock_ollama, tax_agent):
    """Test the query functionality."""
    # Mock the LLM response
    mock_response = {
        "message": {
            "content": """
The standard deduction depends on your filing status.

Source: 26 USC §63(c) [Standard Deduction]"""
        }
    }
    mock_ollama.return_value = mock_response

    response = tax_agent.query("What is the standard deduction?")

    # Verify response contains citation
    assert "standard deduction" in response.lower()
    assert "source:" in response.lower()
