"""
Tax Agent implementation - handles tax-related queries and information retrieval.
Uses the US Tax Code to provide accurate answers with citations.
"""

import logging
import os
import re
from typing import Dict, List

import ollama


class TaxAgent:
    """
    AI-powered tax assistant that answers questions by referencing the US Tax Code.
    """

    def __init__(
        self,
        tax_code_path: str = "data/output/usc26_formatted.md",
        model_name: str = "llama3.1:8b",
        log_level: int = logging.INFO,
    ):
        """
        Initialize the tax agent with references to tax code documents.

        Args:
            tax_code_path: Path to the formatted tax code markdown file
            model_name: Name of the Ollama model to use
            log_level: Logging level
        """
        self.logger = self._setup_logging(log_level)
        self.model_name = model_name
        self.tax_code_path = tax_code_path
        self.tax_code_content = self._load_tax_code()
        self.conversation_history = []
        self.logger.info(f"Tax Agent initialized with model {model_name}")

    def _setup_logging(self, log_level: int) -> logging.Logger:
        """Set up logging for the tax agent."""
        logger = logging.getLogger("tax_agent")
        logger.setLevel(log_level)

        # Create handler if not already configured
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_tax_code(self) -> str:
        """Load the tax code document from file."""
        if not os.path.exists(self.tax_code_path):
            self.logger.error(f"Tax code file not found: {self.tax_code_path}")
            return "Tax code document not available."

        try:
            with open(self.tax_code_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.logger.info(f"Loaded tax code: {len(content)} characters")
            return content
        except Exception as e:
            self.logger.error(f"Error loading tax code: {str(e)}")
            return "Error loading tax code document."

    def query(self, question: str) -> str:
        """
        Process a tax-related query and return a response with citations.

        Args:
            question: The tax-related question from the user

        Returns:
            Response with relevant tax information and citations
        """
        self.logger.info(f"Received query: {question}")

        # Add question to conversation history
        self.conversation_history.append({"role": "user", "content": question})

        # Find relevant sections in tax code (simplified retrieval for now)
        relevant_sections = self._find_relevant_sections(question)

        # Generate response using LLM
        response = self._generate_response(question, relevant_sections)

        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})

        return response

    def _find_relevant_sections(self, question: str) -> List[Dict[str, str]]:
        """
        Find sections of the tax code relevant to the question.

        Args:
            question: The user's tax question

        Returns:
            List of relevant sections with their content and citations
        """
        # This is a simplified implementation
        # In a real system, this would use vector embeddings or a more sophisticated retrieval method

        # Extract key terms from the question (simplified)
        key_terms = self._extract_key_terms(question)

        # Search for sections containing key terms (simplified regex approach)
        relevant_sections = []

        # Simple pattern matching for headers and content
        section_pattern = r"(#{1,4}\s[^\n]+)(?:\n\n)((?:.+?)(?=\n#{1,4}\s|\Z))"
        sections = re.findall(section_pattern, self.tax_code_content, re.DOTALL)

        for heading, content in sections:
            relevance_score = 0
            for term in key_terms:
                if term.lower() in content.lower() or term.lower() in heading.lower():
                    relevance_score += 1

            if relevance_score > 0:
                citation = self._extract_citation(heading)
                relevant_sections.append(
                    {
                        "heading": heading,
                        "content": content[:500],  # Truncate long sections
                        "citation": citation,
                        "relevance": relevance_score,
                    }
                )

        # Sort by relevance
        relevant_sections.sort(key=lambda x: x["relevance"], reverse=True)

        # Return top sections (max 3 for simplicity)
        return relevant_sections[:3]

    def _extract_key_terms(self, question: str) -> List[str]:
        """Extract key tax-related terms from the question."""
        # This is very simplified - would use NLP in a real implementation
        # Common tax-related terms to look for
        tax_terms = [
            "deduction",
            "credit",
            "income",
            "tax",
            "filing",
            "return",
            "dependent",
            "exemption",
            "liability",
            "asset",
            "charitable",
            "business",
            "expense",
            "capital",
            "gain",
            "loss",
            "dividend",
            "interest",
            "retirement",
            "IRA",
            "401k",
            "estate",
            "gift",
        ]

        # Extract terms that appear in the question
        found_terms = []
        for term in tax_terms:
            if term.lower() in question.lower():
                found_terms.append(term)

        # If no tax terms found, use main words from the question
        if not found_terms:
            # Simple approach - just use words longer than 4 characters
            found_terms = [
                word
                for word in question.split()
                if len(word) > 4
                and word.lower()
                not in ["what", "where", "when", "which", "there", "their", "about"]
            ]

        return found_terms

    def _extract_citation(self, heading: str) -> str:
        """Extract a formatted citation from a section heading."""
        # Extract section numbers like §123(a)(4)
        section_match = re.search(r"§(\d+)(?:\(([^)]+)\))?", heading)
        if section_match:
            section = section_match.group(1)
            subsection = section_match.group(2) if section_match.group(2) else ""

            # Extract heading text
            heading_text = re.sub(r"#{1,4}\s+§\d+(?:\([^)]+\))?", "", heading).strip()

            return f"26 USC §{section}{f'({subsection})' if subsection else ''} [{heading_text}]"

        # If no section number found, use the heading text without markdown
        clean_heading = re.sub(r"#{1,4}\s+", "", heading).strip()
        return f"US Tax Code [{clean_heading}]"

    def _generate_response(self, question: str, relevant_sections: List[Dict[str, str]]) -> str:
        """Generate a response using LLM with references to tax code sections."""
        if not relevant_sections:
            return "I couldn't find specific information about that in the tax code. Please try rephrasing your question or ask something more specific about tax regulations."

        # Prepare context from relevant sections
        context = "\n\n".join(
            [
                f"Section: {section['heading']}\n{section['content'][:300]}..."
                for section in relevant_sections
            ]
        )

        # Prepare prompt for the LLM
        prompt = f"""
        You are a tax expert assistant. Answer the following tax question using ONLY the provided sections of the US Tax Code.
        If the answer is not clear from these sections, admit that you don't have enough information.
        Always cite your sources using the citation format at the end of each relevant section.

        Question: {question}

        Relevant Tax Code Sections:
        {context}

        Answer the question concisely and accurately, citing the specific sections of the tax code that support your answer.
        """

        try:
            # Call Ollama API
            response = ollama.chat(
                model=self.model_name, messages=[{"role": "user", "content": prompt}]
            )

            answer = response["message"]["content"]

            # Ensure there's at least one citation
            if not any(section["citation"] for section in relevant_sections):
                citation = relevant_sections[0]["citation"] if relevant_sections else "US Tax Code"
                if "Source:" not in answer:
                    answer += f"\n\nSource: {citation}"

            return answer

        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I'm having trouble processing your question right now. Please try again later."


if __name__ == "__main__":
    # Simple CLI for testing
    agent = TaxAgent()
    print("Welcome to Tax Agent! Ask me any tax-related questions (type 'exit' to quit).")

    while True:
        question = input("> ")
        if question.lower() in ["exit", "quit", "bye"]:
            break
        response = agent.query(question)
        print("\n" + response + "\n")
