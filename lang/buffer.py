import io

from util import check_type


class BufferedMatchStream:
    """
    Buffers a TextIOBase stream in a way that allows tokenization according to a regular expression.
    """

    def __init__(self, source):
        """
        Buffers a TextIOBase object.
        :param source: The TextIOBase oject that is to be buffered.
        """
        super().__init__()
        self._source = check_type(source, io.TextIOBase)
        self._buffer = io.StringIO('')
        self._buffer_offset = 0
        self._buffer_length = 0

    def match_prefix(self, pattern, chunk_size=1024):
        """
        Consumes the longest possible prefix of the buffered stream that is valid according to the given regular
        expression pattern.
        :param pattern: A compiled regular expresssion
        :param chunk_size: The number of characters that should be consumed from the input stream at once. This number
                           must be so large that if a chunk of this size does not have a prefix matching the pattern,
                           there cannot be any continuation of that chunk that would lead to the existence of such a
                           prefix.
        :exception EOFError: If not enough input remains in the source stream.
        :return: A pair (k, s), where k is the name of the regular expression group that matched a prefix
                 and s is the text of the prefix. If no prefix of the remaining source input matches the given pattern,
                 (None, "") is returned.
        """

        if self._buffer_length - self._buffer_offset == 0 and self._source is None:
            raise EOFError("No input left!")

        while True:

            self._buffer.seek(0)
            m = pattern.match(self._buffer.getvalue(), pos=self._buffer_offset)

            if m is not None and (m.end() < self._buffer_length or self._source is None):
                # Valid token ends before the end of the buffer. Must be a complete token.
                # Mark the range of m as consumed:
                t = m.group(0)
                self._buffer_offset += len(t)
                return m.lastgroup, t
            else:
                # Either there is no prefix of the buffer that matches the pattern, or the match ends at the end of
                # the buffer. In both cases it might be possible to continue the buffer, such that a new, valid match
                # happens. So we want to try to continue the buffer.

                if m is None:
                    # No valid match found so far, so we would need to continue the buffer to find one.
                    if self._buffer_length - self._buffer_offset >= chunk_size:
                        # We assume that the chunk size is sufficiently large, so in this case there is no hope.
                        return None, ""
                    if self._source is None:
                        # We would need to consume more input, but there is none left!
                        if self._buffer_length - self._buffer_offset == 0:
                            # We're exactly at the end, i.e. we properly matched *all* the input and are done.
                            raise EOFError("No input left!")
                        else:
                            # There is some remaining input that cannot be matched anymore.
                            return None, ""

                    # Otherwise we want to try and continue the buffer.
                else:
                    # We already have a match, but maybe continuing the buffer would continue the match?
                    pass

                # Before we extend the buffer, we discard all the stuff we've already read:
                if self._buffer_offset > 0:
                    self._buffer = io.StringIO(self._buffer.getvalue()[self._buffer_offset:])
                    self._buffer_length -= self._buffer_offset
                    self._buffer_offset = 0

                # Now extend the buffer:
                chunk = self._source.read(chunk_size)
                if len(chunk) < chunk_size:
                    self._source = None
                self._buffer.seek(self._buffer_length)
                self._buffer.write(chunk)
                self._buffer_length += len(chunk)