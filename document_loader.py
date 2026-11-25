import os
import re
import zlib
from typing import List, Dict, Any

class DocumentLoader:
    """Loads and chunks course documents (slides, syllabi, notes) with metadata."""

    @staticmethod
    def load_file(file_path: str) -> List[Dict[str, Any]]:
        filename = os.path.basename(file_path)
        ext = os.path.splitext(filename)[1].lower()

        if ext in [".txt", ".md", ".text"]:
            return DocumentLoader._load_text_file(file_path, filename)
        elif ext == ".pdf":
            return DocumentLoader._load_pdf_file(file_path, filename)
        else:
            return DocumentLoader._load_text_file(file_path, filename)

    @staticmethod
    def _load_text_file(file_path: str, filename: str) -> List[Dict[str, Any]]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        return DocumentLoader.split_into_slides(content, filename)

    @staticmethod
    def _load_pdf_file(file_path: str, filename: str) -> List[Dict[str, Any]]:
        # Try pypdf / pypdf2 first if available
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            chunks = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    first_line = text.strip().split("\n")[0][:60]
                    chunks.append({
                        "text": text.strip(),
                        "slide_num": i + 1,
                        "title": first_line,
                        "source": filename
                    })
            if chunks:
                return chunks
        except ImportError:
            pass
        except Exception as e:
            print(f"pypdf extraction failed, falling back to pure-python parser: {e}")

        # Lightweight Pure-Python PDF text stream extractor
        return DocumentLoader._extract_pdf_pure_python(file_path, filename)

    @staticmethod
    def _extract_pdf_pure_python(file_path: str, filename: str) -> List[Dict[str, Any]]:
        """Fallback extractor using standard zlib and regex for uncompressed/FlateDecode streams."""
        with open(file_path, "rb") as f:
            data = f.read()

        pages_text = []
        # Find stream objects
        stream_matches = re.finditer(b"stream[\r\n]+(.*?)[\r\n]+endstream", data, re.DOTALL)
        accumulated_text = []

        for match in stream_matches:
            raw_stream = match.group(1)
            decompressed = None
            try:
                decompressed = zlib.decompress(raw_stream)
            except Exception:
                decompressed = raw_stream

            try:
                text_stream = decompressed.decode("latin1", errors="ignore")
                # Look for BT ... ET text blocks
                bt_matches = re.findall(r"BT(.*?)ET", text_stream, re.DOTALL)
                for block in bt_matches:
                    # Extract literal strings in parentheses (Text)Tj or [(Text)]TJ
                    strings = re.findall(r"\((.*?)\)\s*Tj", block)
                    if strings:
                        accumulated_text.append(" ".join(strings))
                    tj_array = re.findall(r"\[(.*?)\]\s*TJ", block)
                    for arr in tj_array:
                        sub_strings = re.findall(r"\((.*?)\)", arr)
                        if sub_strings:
                            accumulated_text.append(" ".join(sub_strings))
            except Exception:
                continue

        full_extracted = "\n".join(accumulated_text)
        if not full_extracted.strip():
            # If nothing found, search for visible ASCII strings
            ascii_strings = re.findall(r"[A-Za-z0-9 ,.\-:;?!\n]{5,}", data.decode("latin1", errors="ignore"))
            full_extracted = "\n".join(ascii_strings[:500])

        return DocumentLoader.split_into_slides(full_extracted, filename)

    @staticmethod
    def split_into_slides(content: str, filename: str) -> List[Dict[str, Any]]:
        """Splits raw content into structured slide units."""
        # Check for explicit slide markers: e.g. "--- Slide 1 ---" or "Slide 1:" or form feeds
        slide_pattern = re.compile(
            r"(?:^|\n)(?:[-=]{3,}\s*(?:Slide|Page)\s*(\d+)[:\s-]*([^\n]*)|(?:Slide|Page)\s+(\d+)[:\s-]*([^\n]*))",
            re.IGNORECASE
        )

        matches = list(slide_pattern.finditer(content))
        chunks = []

        if matches:
            for idx, m in enumerate(matches):
                slide_num = m.group(1) or m.group(3)
                slide_num = int(slide_num) if slide_num and slide_num.isdigit() else idx + 1
                header_title = (m.group(2) or m.group(4) or f"Slide {slide_num}").strip()

                start_idx = m.end()
                end_idx = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
                slide_body = content[start_idx:end_idx].strip()

                if not header_title and slide_body:
                    first_line = slide_body.split("\n")[0][:60].strip()
                    header_title = first_line or f"Slide {slide_num}"

                full_text = f"{header_title}\n{slide_body}".strip()
                chunks.append({
                    "text": full_text,
                    "slide_num": slide_num,
                    "title": header_title,
                    "source": filename
                })
        else:
            # Fallback: split on form-feed \x0c or double newlines into ~400 word chunks
            raw_sections = [s.strip() for s in content.split("\x0c") if s.strip()]
            if len(raw_sections) <= 1:
                paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
                current_chunk = []
                current_len = 0
                slide_counter = 1

                for p in paragraphs:
                    current_chunk.append(p)
                    current_len += len(p.split())
                    if current_len >= 180:
                        chunk_text = "\n\n".join(current_chunk)
                        title = current_chunk[0].split("\n")[0][:60]
                        chunks.append({
                            "text": chunk_text,
                            "slide_num": slide_counter,
                            "title": title or f"Section {slide_counter}",
                            "source": filename
                        })
                        slide_counter += 1
                        current_chunk = []
                        current_len = 0

                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    title = current_chunk[0].split("\n")[0][:60]
                    chunks.append({
                        "text": chunk_text,
                        "slide_num": slide_counter,
                        "title": title or f"Section {slide_counter}",
                        "source": filename
                    })
            else:
                for i, sec in enumerate(raw_sections):
                    first_line = sec.split("\n")[0][:60].strip()
                    chunks.append({
                        "text": sec,
                        "slide_num": i + 1,
                        "title": first_line or f"Slide {i + 1}",
                        "source": filename
                    })

        # Ensure we return at least one chunk if content wasn't empty
        if not chunks and content.strip():
            chunks.append({
                "text": content.strip(),
                "slide_num": 1,
                "title": "Course Overview",
                "source": filename
            })

        return chunks
