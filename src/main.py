"""
Main application for Tax Agent - processes tax queries and provides information.
"""

import os
import argparse
import logging
import sys

# Import agent and document processing modules
from agent import TaxAgent
from xml_to_markdown import convert_xml_to_markdown
from format_markdown import format_markdown, setup_logging


def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = ["data", "data/output", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


def process_tax_code(args):
    """Process tax code documents if needed."""
    logger = logging.getLogger("main")

    if not os.path.exists(args.output) or args.reprocess:
        logger.info("Processing tax code documents...")

        if not os.path.exists(args.intermediate) or args.reprocess:
            if os.path.exists(args.xml):
                logger.info("Converting XML to Markdown...")
                convert_xml_to_markdown(args.xml, args.intermediate)
            else:
                logger.error(f"XML file not found: {args.xml}")
                sys.exit(1)

        logger.info("Formatting Markdown with LLM...")
        format_markdown(
            args.intermediate,
            args.output,
            args.model,
            args.chunk_size,
            args.resume,
            args.clean,
        )
    else:
        logger.info(f"Using existing tax code document: {args.output}")


def interactive_mode(agent):
    """Run interactive mode for tax questions."""
    print(
        "\nWelcome to Tax Agent! Ask me any tax-related questions (type 'exit' to quit)."
    )

    while True:
        try:
            question = input("\n> ")
            if question.lower() in ["exit", "quit", "bye"]:
                print("Goodbye!")
                break

            response = agent.query(question)
            print("\n" + response)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")
            continue


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Tax Agent - AI tax assistant")

    # Document processing arguments
    parser.add_argument(
        "--xml", default="data/usc26.xml", help="Input tax code XML file"
    )
    parser.add_argument(
        "--intermediate", default="data/usc26.md", help="Intermediate markdown file"
    )
    parser.add_argument(
        "--output",
        default="data/output/usc26_formatted.md",
        help="Final output file path",
    )
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model to use")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=5000,
        help="Maximum chunk size for LLM processing",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean intermediate files after processing"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last processed formatting chunk",
    )
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="Force reprocessing of tax code documents",
    )

    # Query mode arguments
    parser.add_argument("--query", help="Run a single query in non-interactive mode")

    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()
    setup_directories()
    logger = setup_logging()

    try:
        # Process tax code documents if needed
        process_tax_code(args)

        # Initialize tax agent
        agent = TaxAgent(tax_code_path=args.output, model_name=args.model)

        # Handle query mode
        if args.query:
            response = agent.query(args.query)
            print(response)
        else:
            # Interactive mode
            interactive_mode(agent)

    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
