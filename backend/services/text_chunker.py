def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []

    if not text:
        return chunks

    words = text.split()
    current_words = []
    current_size = 0

    for word in words:
        extra_space = 1 if current_words else 0

        if current_words and current_size + len(word) + extra_space > chunk_size:
            chunks.append(" ".join(current_words))

            overlap_words = []
            overlap_size = 0

            for previous_word in reversed(current_words):
                previous_size = len(previous_word) + (1 if overlap_words else 0)

                if overlap_words and overlap_size + previous_size > overlap:
                    break

                overlap_words.insert(0, previous_word)
                overlap_size += previous_size

            current_words = overlap_words
            current_size = len(" ".join(current_words))

        current_words.append(word)
        current_size += len(word) + extra_space

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks
