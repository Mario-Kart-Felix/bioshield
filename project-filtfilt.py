from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.garden.graph import Graph, MeshLinePlot
from kivy.clock import Clock
import time

from spp import SPP
from scipy import signal
from filters import *

class ProjectGUI(BoxLayout):
	spp = SPP('/dev/cu.AdafruitEZ-Link9dd8-SPP', 115200, timeout=1)
	graph1 = ObjectProperty(None)
	graph2 = ObjectProperty(None)

	buff = []
	buffsize = 300

	h_lp_ecg, h_lp_icg, h_lp_ppg, h_60 = createFilters()

	def __init__(self, *args, **kwargs):
		super(ProjectGUI, self).__init__(*args, **kwargs)
		self.orientation = 'vertical'
		self.iter = 0
		self.filt_iter = 0
		self.plots = []
		self.plots.append(MeshLinePlot(color=[0, 0, 1, 1]))
		self.plots.append(MeshLinePlot(color=[0, 1, 0, 1]))

	def create_plot(self):
		self.plots[0].points = []
		self.plots[1].points = []
		self.graph1.add_plot(self.plots[0])
		self.graph2.add_plot(self.plots[1])
		# self.start = time.time()

	def update_plot(self, dt):
		m = 30
		if self.iter>100*m:
			self.plots[0].points = []
			self.plots[1].points = []
			self.iter = 0
			self.filt_iter = 0
			self.buff = []
			# print time.time()-self.start
			# self.start = time.time()
			# for i in range(len(self.plots)):
			# 	for _ in range(30):
			# 		self.plots[i].points.pop()
		added = self.spp.update_buffer(release = True)
		n = len(added)
		self.plots[0].points = self.plots[0].points+zip([(self.iter+i)/float(m) for i in range(n)], added)
		self.iter += n

		num_filtered = 0
		for i in added:
			if len(self.buff)==self.buffsize:
				del self.buff[0]
				num_filtered += 1
			self.buff.append(i)
		if len(self.buff) == self.buffsize and num_filtered:
			filt = signal.filtfilt(self.h_lp_icg,1,self.buff[::-1])[:num_filtered]
			filt_n = len(filt)
			self.plots[1].points = self.plots[1].points+zip([(self.buffsize+self.filt_iter+i)/float(m) for i in range(filt_n)], filt)
			self.filt_iter += filt_n
		


class ProjectApp(App):
	def build(self):
		gui = ProjectGUI()
		gui.create_plot()
		Clock.schedule_interval(gui.update_plot, 1.0 / 60.0)
		return gui

if __name__ == '__main__':
	ProjectApp().run()