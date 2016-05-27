"""Written by Rex Garland. 5/26/16"""
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock

from spp import SPP
from scipy import signal
from filters import *

class ProjectGUI(BoxLayout):
	# a serial port profile instance for communicating with the Arduino
	spp = SPP('/dev/cu.AdafruitEZ-Link9dd8-SPP', 115200, timeout=1)

	# graphs for (1) raw data and (2) filtered data
	graph1 = ObjectProperty(None)
	graph2 = ObjectProperty(None)

	# "buffer" to keep track of data we've yet to filter
	buff = []
	# minimum buffer length for convolution
	buffsize = 300 # once the buffer is filled to this length, it will be kept at this length after every update

	h_lp_ecg, h_lp_icg, h_lp_ppg, h_60 = createFilters()

	def __init__(self, *args, **kwargs):
		super(ProjectGUI, self).__init__(*args, **kwargs)
		self.orientation = 'vertical'
		self.iter = 0
		self.filt_iter = self.buffsize
		self.plots = {}
		self.plots['raw'] = MeshLinePlot(color=[0, 0, 1, 1])
		self.plots['filtered'] = MeshLinePlot(color=[0, 1, 0, 1])
		self.num_points = 3e3 # number of points per screen
		self.scale = self.graph1.xmax/float(self.num_points)

	def create_plot(self):
		self.plots['raw'].points = []
		self.plots['filtered'].points = []
		self.graph1.add_plot(self.plots['raw'])
		self.graph2.add_plot(self.plots['filtered'])

	def update_plot(self, dt):
		if self.iter>self.num_points: # check if we've reached the end of the screen
			self.plots['raw'].points = []
			self.plots['filtered'].points = []
			self.iter = 0
			self.filt_iter = 0

		# retrieve new data
		new_data = self.spp.update_buffer(release = True)

		# update raw data plot
		self.plots['raw'].points = self.plots['raw'].points+zip([(self.iter+i)*self.scale for i in range(len(new_data))], new_data)
		self.iter += len(new_data)
		self.buff += new_data
		num_filtered = len(self.buff)-self.buffsize

		# update filtered data plot
		if num_filtered>0: # only draw filtered data if we've overfilled the buffer (prevent convolving too little data)
			# convolve new data with filter
			filtered = [np.dot(self.h_lp_icg,self.buff[-(i+1):-(i+1)-len(self.h_lp_icg):-1]) for i in range(num_filtered)][::-1]
			self.plots['filtered'].points = self.plots['filtered'].points+zip([(self.filt_iter+i)*self.scale for i in range(num_filtered)], filtered)
			self.filt_iter += num_filtered
			del self.buff[:num_filtered] # keep the buffer size limited to buffsize

class ProjectApp(App):
	def build(self):
		gui = ProjectGUI()
		gui.create_plot()
		Clock.schedule_interval(gui.update_plot, 1.0 / 60.0)
		return gui

if __name__ == '__main__':
	ProjectApp().run()