from telnetsrv.threaded import TelnetHandler, command
import socket,threading
import SocketServer
 
class MyTelnetHandler(TelnetHandler):
    WELCOME = "Welcome to my server."
    WELCOME=WELCOME.encode('gb2312')
    PROMPT="TELNET_Server>"
    authNeedUser=True
    authNeedPass=True
   
    def session_start(self):      
        print self.client_address
       
    @command(['echo', 'copy', 'repeat'])
    def command_echo(self, params):
        '''
        Echo text back to the console.
       
        '''
        self.writeresponse( ' '.join(params) )
   
    def authCallback(self, username, password):
        print 'auth begin'
        #print username
        #print password
        #return
        auth_info={}
        auth_info['test']='888888'
        if auth_info.get(username) is None:
            self.writeline('Wrong Username')
            raise RuntimeError('Wrong Username')
        if auth_info[username]<>password:
            self.writeline('Wrong password!')
            raise RuntimeError('Wrong password!')

class TelnetServer(SocketServer.ThreadingTCPServer):
        allow_reuse_address = False
if __name__ == '__main__':
    print "server running..."
    server = TelnetServer(("0.0.0.0", 8027), MyTelnetHandler)
    server.serve_forever()