import sys
class Tee:
	# send output to both the console and a file
    def __init__(self, filename, mode="a"):
        self.terminal = sys.__stdout__
        self.log = open(filename, mode)
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()