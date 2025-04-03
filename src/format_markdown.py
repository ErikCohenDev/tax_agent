"""
Module for formatting markdown documents using LLMs.
Handles chunking, processing, and reassembly of large files.
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import ollama


def setup_logging(log_dir="logs"):
    """Set up logging configuration"""
    os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                f"{log_dir}/formatting_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            ),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def split_by_paragraphs(text, max_chunk_size=5000):
    """Split text at paragraph boundaries, respecting max chunk size."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 > max_chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n"
            current_chunk += para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def format_markdown(
    input_file,
    output_file,
    model="llama3.1:8b",
    max_chunk_size=5000,
    resume=False,
    clean=False,
):
    """Format a markdown file using Ollama LLM."""
    logger = logging.getLogger(__name__)

    start_time = time.time()
    logger.info(f"Starting markdown formatting process with model: {model}")

    logger.info(f"Reading input file: {input_file}")
    with open(input_file, "r", encoding="utf-8") as file:
        content = file.read()
    logger.info(f"Read {len(content)} characters from input file")

    # Create necessary directories
    intermediate_dir = "data/output"
    output_dir = os.path.dirname(output_file)
    os.makedirs(intermediate_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    # Split content into logical chunks
    chunks = split_by_paragraphs(content, max_chunk_size)
    logger.info("Split content into {len(chunks)} chunks")
    formatted_chunks = []

    # Determine starting point for processing
    start_chunk = 0
    if resume:
        # Find highest chunk number
        existing_chunks = [
            f
            for f in os.listdir(intermediate_dir)
            if f.startswith("formatted_") and f.endswith(".md")
        ]
        if existing_chunks:
            indices = [int(f.split("_")[1].split(".")[0]) for f in existing_chunks]
            if indices:
                start_chunk = max(indices) + 1
                # Load previously processed chunks
                for i in range(start_chunk):
                    chunk_file = f"{intermediate_dir}/formatted_{i}.md"
                    if os.path.exists(chunk_file):
                        with open(chunk_file, "r", encoding="utf-8") as f:
                            formatted_chunks.append(f.read())

        logger.info(f"Resuming from chunk {start_chunk}")

    # Process chunks
    total_chunks = len(chunks)
    for i in range(start_chunk, total_chunks):
        chunk_start_time = time.time()
        logger.info(f"Processing chunk {i+1}/{total_chunks} ({(i+1)/total_chunks*100:.1f}%)")

        current_chunk = chunks[i]
        previous_chunk = chunks[i - 1] if i > 0 else ""
        next_chunk = chunks[i + 1] if i < len(chunks) - 1 else ""

        # Check if current chunk is already formatted
        chunk_file = f"{intermediate_dir}/formatted_{i}.md"
        if os.path.exists(chunk_file):
            with open(chunk_file, "r", encoding="utf-8") as file:
                formatted_chunk = file.read()
            logger.info(f"Found existing formatting for chunk {i+1}")
        else:
            formatted_chunk = ""
            logger.info(f"No existing formatting found for chunk {i+1}")

        # Create prompt for the LLM
        prompt = f"""
        Format the following text as proper markdown.
        ----
        Here are previously formatings choose the best one:
        current formatting of chunk {i}: {formatted_chunk}

        ----
        Previous chunk {i-1}: {previous_chunk}
        Current chunk {i}: {current_chunk}
        Next chunk {i+1}: {next_chunk}
        Only return the current chunk formatted as proper markdown, the previous and next chunks are provided to give you context.
        """

        # Try to format with LLM
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending chunk {i+1} to LLM (size: {len(current_chunk)} chars)")
                response = ollama.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                )
                # Extract the actual content from the response
                formatted_text = response["message"]["content"]
                formatted_chunks.append(formatted_text)

                # Save intermediate result
                with open(chunk_file, "w", encoding="utf-8") as f:
                    f.write(formatted_text)

                # Calculate statistics
                chunk_duration = time.time() - chunk_start_time
                avg_time_per_chunk = (
                    (time.time() - start_time) / (i - start_chunk + 1)
                    if i > start_chunk
                    else chunk_duration
                )
                est_remaining = avg_time_per_chunk * (total_chunks - (i + 1))

                logger.info(
                    f"Chunk {i+1} completed in {chunk_duration:.1f}s | Est. remaining: {est_remaining/60:.1f} minutes"
                )
                break  # Exit retry loop on success

            except Exception as e:
                logger.error(
                    f"Attempt {attempt+1}/{max_retries} failed for chunk {i+1}: {str(e)}",
                    exc_info=True,
                )
                if attempt == max_retries - 1:
                    logger.warning(
                        f"All attempts failed for chunk {i+1}, continuing with next chunk"
                    )
                    # Add placeholder to maintain chunk order
                    formatted_chunks.append(f"[ERROR: Failed to process chunk {i+1}]")
                else:
                    logger.info("Retrying in 5 seconds...")
                    time.sleep(5)

        # Save checkpoint periodically
        if (i + 1) % 10 == 0 or i == total_chunks - 1:
            checkpoint_path = f"{output_file}.checkpoint"
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(formatted_chunks))
            logger.info(f"Saved checkpoint to {checkpoint_path}")

    # Combine all formatted chunks into final document
    logger.info("Combining formatted chunks into final document")
    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write("\n\n".join(formatted_chunks))

    # Clean up intermediate files if requested
    if clean:
        logger.info("Cleaning up intermediate files")
        for i in range(total_chunks):
            try:
                os.remove(f"{intermediate_dir}/formatted_{i}.md")
            except Exception as e:
                logger.error(
                    f"Error removing intermediate file {intermediate_dir}/formatted_{i}.md: {str(e)}"
                )
        try:
            os.remove(f"{output_file}.checkpoint")
        except Exception as e:
            logger.error(f"Error removing checkpoint file {output_file}.checkpoint: {str(e)}")

    total_duration = time.time() - start_time
    logger.info(f"Processing complete! Total time: {total_duration/60:.1f} minutes")
    logger.info(f"Output saved to {os.path.abspath(output_file)}")

    return os.path.abspath(output_file)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Format markdown using Ollama LLM")
    parser.add_argument("--input", default="data/usc26.md", help="Input markdown file")
    parser.add_argument(
        "--output", default="data/output/usc26_formatted.md", help="Output file path"
    )
    parser.add_argument("--model", default="llama3.1:8b", help="Ollama model to use")
    parser.add_argument(
        "--chunk-size", type=int, default=5000, help="Maximum chunk size in characters"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Clean intermediate files after processing"
    )
    parser.add_argument("--resume", action="store_true", help="Resume from last processed chunk")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_logging()
    try:
        format_markdown(
            args.input,
            args.output,
            args.model,
            args.chunk_size,
            args.resume,
            args.clean,
        )
    except KeyboardInterrupt:
        logging.warning("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}", exc_info=True)
