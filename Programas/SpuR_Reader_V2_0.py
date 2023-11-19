#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: SpuR _Reader - (V2.0)
# Author: Frate, M.
# Description: SpuR - (v2.0) - An Spectral Signature Writer System in Chipless Tags
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import filter
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import iio
import SpuR_Reader_V2_0_python_mod as python_mod  # embedded python module
import sip
import time
import threading



class SpuR_Reader_V2_0(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "SpuR _Reader - (V2.0)", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("SpuR _Reader - (V2.0)")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "SpuR_Reader_V2_0")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.fun_prob = fun_prob = 0
        self.samp_rate = samp_rate = 50000000
        self.frequency = frequency = python_mod.sweeper(fun_prob)
        self.freqc = freqc = python_mod.sweeper(fun_prob)
        self.amplitude = amplitude = fun_prob

        ##################################################
        # Blocks
        ##################################################

        self.probSign = blocks.probe_signal_f()
        self.qtgui_time_sink = qtgui.time_sink_f(
            2048, #size
            samp_rate, #samp_rate
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_time_sink.set_update_time(0.001)
        self.qtgui_time_sink.set_y_axis(0, 1)

        self.qtgui_time_sink.set_y_label('(mV)', "")

        self.qtgui_time_sink.enable_tags(True)
        self.qtgui_time_sink.set_trigger_mode(qtgui.TRIG_MODE_TAG, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "packet_len")
        self.qtgui_time_sink.enable_autoscale(False)
        self.qtgui_time_sink.enable_grid(True)
        self.qtgui_time_sink.enable_axis_labels(True)
        self.qtgui_time_sink.enable_control_panel(True)
        self.qtgui_time_sink.enable_stem_plot(False)


        labels = ['Real', 'Im', 'Power (mW)', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['red', 'blue', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 2, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink.set_line_label(i, labels[i])
            self.qtgui_time_sink.set_line_width(i, widths[i])
            self.qtgui_time_sink.set_line_color(i, colors[i])
            self.qtgui_time_sink.set_line_style(i, styles[i])
            self.qtgui_time_sink.set_line_marker(i, markers[i])
            self.qtgui_time_sink.set_line_alpha(i, alphas[i])

        self._qtgui_time_sink_win = sip.wrapinstance(self.qtgui_time_sink.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_time_sink_win)
        self.moving_average = blocks.moving_average_ff(100000, 0.00001, 10000, 1)
        self.iio_pluto_source = iio.fmcomms2_source_fc32('ip:192.168.2.1' if 'ip:192.168.2.1' else iio.get_pluto_uri(), [True, True], 1000)
        self.iio_pluto_source.set_len_tag_key('packet_len')
        self.iio_pluto_source.set_frequency(freqc)
        self.iio_pluto_source.set_samplerate(samp_rate)
        self.iio_pluto_source.set_gain_mode(0, 'manual')
        self.iio_pluto_source.set_gain(0, 0)
        self.iio_pluto_source.set_quadrature(False)
        self.iio_pluto_source.set_rfdc(False)
        self.iio_pluto_source.set_bbdc(False)
        self.iio_pluto_source.set_filter_params('Auto', '', 0, 0)
        self.iio_pluto_sink = iio.fmcomms2_sink_fc32('ip:192.168.2.1' if 'ip:192.168.2.1' else iio.get_pluto_uri(), [True, True], 1000, True)
        self.iio_pluto_sink.set_len_tag_key('')
        self.iio_pluto_sink.set_bandwidth(1000000)
        self.iio_pluto_sink.set_frequency(freqc)
        self.iio_pluto_sink.set_samplerate(samp_rate)
        self.iio_pluto_sink.set_attenuation(0, 0)
        self.iio_pluto_sink.set_filter_params('Auto', '', 0, 0)
        self.hilbert = filter.hilbert_fc(500, window.WIN_RECTANGULAR, 6.76)
        def _fun_prob_probe():
          while True:

            val = self.probSign.level()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_fun_prob,val))
              except AttributeError:
                self.set_fun_prob(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (100e6))
        _fun_prob_thread = threading.Thread(target=_fun_prob_probe)
        _fun_prob_thread.daemon = True
        _fun_prob_thread.start()
        self._frequency_tool_bar = Qt.QToolBar(self)

        if None:
            self._frequency_formatter = None
        else:
            self._frequency_formatter = lambda x: eng_notation.num_to_str(x)

        self._frequency_tool_bar.addWidget(Qt.QLabel("Frequency"))
        self._frequency_label = Qt.QLabel(str(self._frequency_formatter(self.frequency)))
        self._frequency_tool_bar.addWidget(self._frequency_label)
        self.top_grid_layout.addWidget(self._frequency_tool_bar, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.complex_to_mag = blocks.complex_to_mag(1)
        self.analog_sig_source = analog.sig_source_f(samp_rate, analog.GR_CONST_WAVE, 0.00001, 10, 0, 0)
        self._amplitude_tool_bar = Qt.QToolBar(self)

        if None:
            self._amplitude_formatter = None
        else:
            self._amplitude_formatter = lambda x: repr(x)

        self._amplitude_tool_bar.addWidget(Qt.QLabel("Amplitude"))
        self._amplitude_label = Qt.QLabel(str(self._amplitude_formatter(self.amplitude)))
        self._amplitude_tool_bar.addWidget(self._amplitude_label)
        self.top_grid_layout.addWidget(self._amplitude_tool_bar, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_sig_source, 0), (self.hilbert, 0))
        self.connect((self.complex_to_mag, 0), (self.moving_average, 0))
        self.connect((self.hilbert, 0), (self.iio_pluto_sink, 0))
        self.connect((self.iio_pluto_source, 0), (self.complex_to_mag, 0))
        self.connect((self.moving_average, 0), (self.probSign, 0))
        self.connect((self.moving_average, 0), (self.qtgui_time_sink, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "SpuR_Reader_V2_0")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_fun_prob(self):
        return self.fun_prob

    def set_fun_prob(self, fun_prob):
        self.fun_prob = fun_prob
        self.set_amplitude(self.fun_prob)
        self.set_freqc(python_mod.sweeper(self.fun_prob))
        self.set_frequency(python_mod.sweeper(self.fun_prob))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_sig_source.set_sampling_freq(self.samp_rate)
        self.iio_pluto_sink.set_samplerate(self.samp_rate)
        self.iio_pluto_source.set_samplerate(self.samp_rate)
        self.qtgui_time_sink.set_samp_rate(self.samp_rate)

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
        Qt.QMetaObject.invokeMethod(self._frequency_label, "setText", Qt.Q_ARG("QString", str(self._frequency_formatter(self.frequency))))

    def get_freqc(self):
        return self.freqc

    def set_freqc(self, freqc):
        self.freqc = freqc
        self.iio_pluto_sink.set_frequency(self.freqc)
        self.iio_pluto_source.set_frequency(self.freqc)

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
        Qt.QMetaObject.invokeMethod(self._amplitude_label, "setText", Qt.Q_ARG("QString", str(self._amplitude_formatter(self.amplitude))))




def main(top_block_cls=SpuR_Reader_V2_0, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
