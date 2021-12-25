from unittest.mock import Mock, patch
import pytest
import socket

from src.traceroute import Traceroute


@pytest.fixture()
def traceroute_fixt() -> Traceroute:
    return Traceroute('')


def test_send_echo_callSendtoOneTime():
    with patch('socket.socket'):
        traceroute = Traceroute('')
        traceroute._send_echo()
        traceroute._socket.sendto.assert_called_once()


def test_send_echo_intcementSeq():
    with patch('socket.socket'):
        traceroute = Traceroute('')
        seq = traceroute._curr_seq
        traceroute._send_echo()

    assert seq == traceroute._curr_seq - 1


def test_send_echo_sendToDestination():
    with patch('socket.socket'),\
            patch('src.traceroute.Traceroute._get_ping_icmp_packet') as icmp_packet,\
            patch('socket.gethostbyname') as resolve:
        resolve.return_value = 'destination'
        icmp_packet.return_value = b'ret'
        traceroute = Traceroute('destination')
        traceroute._send_echo()
        traceroute._socket.sendto.assert_called_with(b'ret', ('destination', 0))