import OSC
import socket

class OSCCommunicator(object):

    def __init__(self, client_ip, server_ip=None,
                 server_port=9000, client_port=8000,
                 send_OSC=True):
        '''
        Inputs:

            server_ip - A string holding this machine's ip address.

            client_ip - A string holding the ip address of the machine where
                we will send OSC messages.

            server_port - An integer specifying the port number that we will
                use on this machine for the server.

            client_port - An integer specifying the port number of the
                machine that will receive our sent OSC messages.
        '''

        if server_ip is None:
            #server_ip = self._find_own_ip(client_ip)
            server_ip = '10.35.145.217' # just for testing
        self.server = OSC.OSCServer((server_ip, server_port))
        self.server.timeout = 0
        #self.server.addMsgHandler('/1/toggle1', self._print_msg)
        self.server.addMsgHandler('/1/toggle1', self._toggle_send_OSC)
        self.client = OSC.OSCClient()
        self.client.connect((client_ip, client_port))
        self.send_OSC = send_OSC

    def _find_own_ip(self, client_ip):
        '''
        Find this machine's own IP address.

        This code is taken from:
        http://stackoverflow.com/questions/7334349/python-get-local-ip-address-used-to-send-ip-data-to-a-specific-remote-ip-addres
        '''

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((client_ip, 9))
            own_ip = s.getsockname()[0]
        except socket.error:
            own_ip = None
            raise
        finally:
            del s
        return own_ip

    def send_message(self, address, *values):
        message = OSC.OSCMessage(address)
        for v in values:
            message.append(v)
        self.client.send(message)

    def _print_msg(self, address, tags, data, client_address):
        print('address: %s' % address)
        print('tags: %s' % tags)
        print('data: %s' % data)
        print('client_address: %s' % (client_address,))

    def _toggle_send_OSC(self, address, tags, data, client_address):
        self.send_OSC = bool(data[0])
