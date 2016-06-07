"""
Written by Rex Garland <rgarland@stanford.edu> on June 6th, 2016.
Can be accessed at https://github.com/rexgarland/bioshield

The bioshield GUI for live-plotting data sent over Bluetooth from the Arduino.

USAGE:
>>> kivy project.py
"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock

from spp import SPP
from scipy import signal
from filters import *

import copy

SERIAL_FILE = '/dev/cu.AdafruitEZ-Link9dd8-SPP'

class ProjectGUI(BoxLayout):
	# channels = ['ecg', 'icg_cardiac', 'icg_respiration', 'ppg']
	channels = ['ecg']
	graph1 = ObjectProperty(None)
	graph2 = ObjectProperty(None)

	# a serial port profile instance for communicating with the Arduino
	spp = SPP(channels, SERIAL_FILE, 115200, timeout=1)

	h_lp_ecg, h_lp_icg, h_lp_ppg, h_60, h_hp = createFilters()

	f = h_lp_icg # the filter selected for display

	# "buffer" to keep track of data we've yet to filter
	buff = {channel: [] for channel in channels}
	# minimum buffer length for convolution
	buffsize = 300 # once the buffer is filled to this length, it will be kept at this length after every update

	plot_filter = False # change to show the filtered signal in the second plot

	def __init__(self, *args, **kwargs):
		super(ProjectGUI, self).__init__(*args, **kwargs)
		self.orientation = 'vertical'
		self.iter = 0
		self.filt_iter = self.buffsize
		self.plots = {}
		self.plots['ecg'] = MeshLinePlot(color=[0, 1, 0, 1])
		if self.plot_filter:
			self.plots['ecg_filtered'] = MeshLinePlot(color=[0, 1, 0, 1])
		self.num_points = 5e3 # number of points per screen
		self.scale = self.graph1.xmax/float(self.num_points)

	def create_plots(self):
		self.plots['ecg'].points = []
		self.graph1.add_plot(self.plots['ecg'])
		if self.plot_filter:
			self.plots['ecg_filtered'].points = []
			self.graph2.add_plot(self.plots['ecg_filtered'])

	def update_plot(self, dt):
		if self.iter>self.num_points: # check if we've reached the end of the screen
			self.plots['ecg'].points = []
			if self.plot_filter:
				self.plots['ecg_filtered'].points = []
			self.iter = 0
			self.filt_iter = 0

		# retrieve new data
		self.spp.update_buffer()
		new_data = copy.deepcopy(self.spp.data)
		self.spp.release_data()

		# update raw data plot
		self.plots['ecg'].points = self.plots['ecg'].points+zip([(self.iter+i)*self.scale for i in range(len(new_data['ecg']))], new_data['ecg'])
		self.buff['ecg'] += new_data['ecg']
		
		self.iter += len(new_data['ecg'])

		# FIR filter shown on second plot
		if self.plot_filter:
			num_filtered = len(self.buff['ecg'])-self.buffsize
			# update filtered data plot
			if num_filtered>0: # only draw filtered data if we've overfilled the buffer (prevent convolving too little data)
				# convolve new data with filter
				filtered = [np.dot(self.f,self.buff['ecg'][-(i+1):-(i+1)-len(self.f):-1]) for i in range(num_filtered)][::-1]
				self.plots['ecg_filtered'].points = self.plots['ecg_filtered'].points+zip([(self.filt_iter+i)*self.scale for i in range(num_filtered)], filtered)
				self.filt_iter += num_filtered
				del self.buff['ecg'][:num_filtered] # keep the buffer size limited to buffsize

class ProjectApp(App):
	def build(self):
		gui = ProjectGUI()
		gui.create_plots()
		Clock.schedule_interval(gui.update_plot, 1.0 / 60.0)
		return gui

if __name__ == '__main__':
	ProjectApp().run()