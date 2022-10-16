import sys
import socket
from typing import Optional

# How many bytes is the word length?
WORD_LEN_SIZE = 2

def usage():
    print("usage: wordclient.py server port", file=sys.stderr)

packet_buffer = b''

ServerHungUp = type("ServerHungUp", (BaseException,), {})

def receive_bytes_from(s: socket.SocketType, num_bytes: int) -> Optional[bytes]:
    """
    Get a minimum number of bytes from a socket.

    Args:
        s (socket): Socket to receive data from.
        num_bytes (int): Number of bytes to receive from s.
    
    Raises:
        ServerHungUp: If the socket closes or sends 0 bytes.

    Returns:
        bytes of length >= num_bytes
    """
    total_bytes_received = b''
    while len(total_bytes_received) < num_bytes:
        received_bytes = s.recv(5)
        if received_bytes:
            total_bytes_received += received_bytes
        else:
            raise ServerHungUp
    return total_bytes_received

def get_next_word_packet(s: socket.SocketType) -> Optional[bytes]:
    """
    Return the next word packet from the stream.

    The word packet consists of the encoded word length followed by the
    UTF-8-encoded word.

    Returns None if there are no more words, i.e. the server has hung
    up.
    """

    # yuck
    global packet_buffer

    # using an exception to break out of this instead of nested or repeated conditionals 
    try:
        # get the length of the word
        if len(packet_buffer) < WORD_LEN_SIZE:
            packet_buffer += receive_bytes_from(s, WORD_LEN_SIZE - len(packet_buffer))
        
        length = int.from_bytes(packet_buffer[:WORD_LEN_SIZE], "big")
        packet_buffer = packet_buffer[WORD_LEN_SIZE:]

        # get the actual word
        if len(packet_buffer) < length:
            packet_buffer += receive_bytes_from(s, length - len(packet_buffer))
        
        word_packet = length.to_bytes(2, "big") + packet_buffer[:length]
        packet_buffer = packet_buffer[length:]

        return word_packet

    except ServerHungUp:
        return None


def extract_word(word_packet: bytes) -> str:
    """
    Extract a word from a word packet.

    word_packet: a word packet consisting of the encoded word length
    followed by the UTF-8 word.

    Returns the word decoded as a string.
    """

    return word_packet[WORD_LEN_SIZE:].decode()

# Do not modify:

def main(argv):
    try:
        host = argv[1]
        port = int(argv[2])
    except:
        usage()
        return 1

    s = socket.socket()
    s.connect((host, port))

    print("Getting words:")

    while True:
        word_packet = get_next_word_packet(s)

        if word_packet is None:
            break

        word = extract_word(word_packet)

        print(f"    {word}")

    s.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))
