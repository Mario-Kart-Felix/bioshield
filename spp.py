"""
Written by Rex Garland <rgarland@stanford.edu> on June 6th, 2016.

A module for communicating with the Arduino via the Bluetooth Serial Port Profile (SPP).

See the last few lines for usage.
"""
import serial, sys
from find_ports import serial_ports
from Queue import Queue
import time

count = 0

class SPP(serial.Serial):
	"""The Bluetooth Serial Port Profile (SPP) class."""
	buff = []
	
	read_first_0 = False

	def __init__(self, channels, *args, **kwargs):
		"""Create a serial instance and read until the spp header is passed."""
		super(SPP, self).__init__(*args, **kwargs)
		self.data = {}
		self.channels = channels
		for channel in channels:
			self.data[channel] = []
		# self.num_channels = num_channels
		self.packet_len = 2*len(self.channels)+1
		# read until the header is past
		read = 0
		start = time.time()
		while read<50:
			if (time.time()-start)>3:
				print "Did not read serial data from Bluetooth for 3 seconds... closing."
				self.close()
				exit(0)
			# read past the spp header data (about 50 bytes) and check for the data_begin byte
			if self.inWaiting()>0:
				self.read(1)
				read += 1

	def update_buffer(self, verbose = False):
		"""Read available data from the spp. Save the data into the buffer."""
		global count
		# read all available data into a buffer
		self.buff += [ord(d) for d in self.read(self.inWaiting())]
		if not self.read_first_0:
			if 0 in self.buff:
				# delete up to buff
				del self.buff[:self.buff.index(0)]
				self.read_first_0 = True
		else:
			# split data into packets of combined channel data points (ignoring the first 0 in each)
			num_packets = len(self.buff)//self.packet_len
			packets = [self.buff[i*self.packet_len+1:(i+1)*self.packet_len] for i in range(num_packets)]
			del self.buff[:num_packets*self.packet_len]
			for packet in packets:
				count += 1
				if count>100:
					if verbose:
						print packet
					count = 0
				i = 0
				for channel in self.channels:
					d1, d2 = packet[i], packet[i+1]
					i += 2
					d1 = d1&ord('\x7f') # remove identifying 1 bit at the beginning of 16 bits
					value = (d1<<8|d2)*5./2**10 # convert 10-bit data across 2 bytes to a voltage on [0,5)
					# value = 5-value # invert
					self.data[channel].append(value)

	def release_data(self, num_points = -1):
		"""Return the data from the buffer and delete the buffer."""
		if num_points == -1:
			self.release_data(len(self.data[self.channels[0]]))
		for channel in self.channels:
			del self.data[channel][:num_points]

	def get_data(self, dt = 1):
		"""Read from the spp for |dt| seconds."""
		start = time.time()
		while (time.time()-start)<dt:
			self.update_buffer()

if __name__=='__main__':
	# for testing purposes
	spp = SPP(['ecg'], '/dev/cu.AdafruitEZ-Link9dd8-SPP', 115200, timeout=1)
	spp.get_data(1)
	import matplotlib.pyplot as plt
	plt.plot(spp.data['ecg']); plt.show()
	spp.close()