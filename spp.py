import serial, sys
from find_ports import serial_ports
from Queue import Queue
import time

count = 0

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
	buff = {}
	keys = ['ecg', 'icg_cardiac', 'icg_respiration', 'ppg']
	for key in keys:
		buff[key] = Queue(maxsize = 100000)

	def __init__(self, *args, **kwargs):
		super(SPP, self).__init__(*args, **kwargs)
		read = 0
		start = time.time()
		while read<50 or datum!=0:
			if (time.time()-start)>3:
				print "Did not read serial data from Bluetooth for 3 seconds... closing."
				exit(0)
			# read past the spp header data (about 20 bytes) and check for the data_begin byte
			if self.inWaiting()>0:
				datum = ord(self.read(1))
				read += 1

	def update_buffer(self, release = False, verbose = False):
		global count
		num_packets = self.inWaiting()//9 # a packet is a group of 4 data points (2 bytes each) and a data_begin byte
		if num_packets>0:
			data = [ord(d) for d in self.read(num_packets*9)]
			for i in range(num_packets):
				packet = data[i*9:(i+1)*9]
				count += 1
				if count > 100:
					print packet
					count = 0
				for j in range(4):
					d1, d2 = packet[j*2], packet[j*2+1]
					d1 = d1&ord('\x7f')
					value = (d1<<8|d2)*5./2**10 # convert 10-bit data across 2 bytes to a voltage on [0,5)
					key = self.keys[j]
					if self.buff[key].full():
						self.buff[key].get_nowait()
					self.buff[key].put_nowait(value)
		if release:
			return self.release_data()

	def release_data(self):
		length = {key: self.buff[key].qsize() for key in self.buff}
		data = {}
		for key in self.buff:
			data[key] = []
			for _ in range(length[key]):
				data[key].append( self.buff[key].get_nowait() )
		return data

	def get_data(self, dt = 1):
		start = time.time()
		while (time.time()-start)<dt:
			self.update_buffer()

	def print_data(self):
		length = {key: self.buff[key].qsize() for key in self.buff}
		for key in self.buff:
			sys.stdout.write( key+': ' )
			for _ in range(length[key]):
				sys.stdout.write( str(self.buff[key].get_nowait()) + ' ')

if __name__=='__main__':
	spp = SPP('/dev/cu.AdafruitEZ-Link9dd8-SPP', 115200, timeout=1)
	spp.get_data(1)
	# spp.print_data()
	# spp.plot_data()
	spp.close()