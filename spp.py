import serial, sys
from find_ports import serial_ports
from Queue import Queue
import time

def ask_for_int(value, condition = lambda value: True):
	try:
		answer = int(raw_input("Enter {}: ".format(value)))
		assert condition(answer)
		return answer
	except KeyboardInterrupt:
		exit(0)
	except:
		print "Invalid {}.".format(value)
		return ask_for_int(value)

def connect_spp():
	ports = serial_ports()
	print "Available ports:"
	if not ports:
		print "(None)"
		return None
	for i in range(len(ports)):
		print "{}) {}".format(i+1, ports[i])
	i = ask_for_int('number', lambda i: i<=len(ports) and i>0)
	port = ports[i-1]
	baud_rate = ask_for_int('baud_rate', lambda r: 0<r and r<=115200)
	timeout = ask_for_int('timeout (in seconds)')
	spp = SPP(port, baud_rate, timeout=timeout)
	return spp

class SPP(serial.Serial):
	"""The Bluetooth Serial Port Profile (SPP) class."""
	byte_buff = Queue(maxsize = 2)
	data_buff = Queue(maxsize = 100000)
	data_started = False

	# def __init__(self, *args, **kwargs):
	# 	super(SPP, self).__init__(*args, **kwargs)

	def update_buffer(self, release = False, verbose = False):
		num_bytes = self.inWaiting()
		if num_bytes > 0:
			data = self.read(num_bytes)
			for datum in list(data):
				if not self.data_started:
					if ord(datum)==62:
						self.data_started = True
					continue
				if self.byte_buff.full():
					l1, l2 = self.byte_buff.get_nowait(), self.byte_buff.get_nowait()
					value = (l1<<8|l2)*5/2.**10
					if self.data_buff.full():
						self.data_buff.get_nowait()
					self.data_buff.put_nowait(value)
					continue
				self.byte_buff.put_nowait(ord(datum))
				if verbose:
					print ord(datum)
		if release:
			return self.release_data()

	def release_data(self):
		length = self.data_buff.qsize()
		data = []
		for _ in range(length):
			data.append( self.data_buff.get_nowait() )
		return data

	def get_data(self, dt = 1):
		start = time.time()
		while (time.time()-start)<dt:
			self.update_buffer()

	def print_data(self):
		length = self.data_buff.qsize()
		for _ in range(length):
			sys.stdout.write( str(self.data_buff.get_nowait()) + ' ')

if __name__=='__main__':
	spp = SPP('/dev/cu.AdafruitEZ-Link9dd8-SPP', 115200, timeout=1)
	spp.get_data(1)
	spp.print_data()
	spp.close()