# LeCroy_Wavesurfer.py class, to perform the communication between the Wrapper and the device
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2009
# Pieter de Groot <pieterdegroot@gmail.com>, 2009
# Timothy Lucas <t.w.lucas@gmail.com>, 2011 (Waverunner 44XS driver adapted for Wavesurfer 104MXs-A)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from instrument import Instrument
import visa
import types
import logging
import socket
import numpy as np #added later..!
import struct
from numpy import linspace

class LeCroy_Wavesurfer(Instrument):
    '''
    This is the python driver for the LeCroy Wavesurfer 104MXs-A
    Digital Oscilloscope

    Usage:
    Initialize with
    <name> = instruments.create('name', 'LeCroy_Wavesurfer', address='<VICP address>')
    <VICP address> = VICP::<ip-address>
    '''

    def __init__(self, name, address):
        '''
        Initializes the LeCroy Wavesurfer 104MXs-A.

        Input:
            name (string)    : name of the instrument
            address (string) : VICP address

        Output:
            None
        '''
        Instrument.__init__(self, name, tags=['physical'])
        logging.debug(__name__ + ' : Initializing instrument')
        
        self._address = address
        self._visainstrument = visa.instrument(self._address)
#        self._values = {}
        self._visainstrument.clear()
        self._input_channels = ['C1', 'C2', 'C3', 'C4']
        #self._visainstrument.delay = 20e-3

        # Add parameters
##        self.add_parameter('timesteps', type=types.FloatType,
##                           flags = Instrument.FLAG_GETSET)
#        self.add_parameter('enhanced_resolution', type=types.FloatType,
#                             flags=Instrument.FLAG_GETSET, minval=0, maxval=3)


        for ch_in in self._input_channels:
#            self.add_parameter('enhanced_resolution_bits_'+ch_in,
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                minval=0, maxval=3,
#                get_func=self.do_get_enhanced_resolution,
#                channel=ch_in)
            self.add_parameter(ch_in+'_vdiv',
                flags=Instrument.FLAG_GET,
                type=types.FloatType,
                get_func=self.do_get_vdiv,
                channel=ch_in,
                units='V')
#            self.add_parameter(ch_in+'_tdiv',
#                flags=Instrument.FLAG_GET,
#                type=types.FloatType,
#                get_func=self.do_get_tdiv,
#                channel=ch_in,
#                units='s')
            self.add_parameter(ch_in+'_vertical_offset',
                flags=Instrument.FLAG_GET,
                type=types.FloatType,
                get_func=self.do_get_voffset,
                channel=ch_in,
                units='V'
                )        
            self.add_parameter(ch_in+'_trace_on_display',
                flags=Instrument.FLAG_GET,
                type=types.BooleanType,
                get_func=self.do_get_trace_on_display,
                channel=ch_in,
                )
            self.add_parameter(ch_in+'_coupling',
                flags=Instrument.FLAG_GET,
                type=types.StringType,
                get_func=self.do_get_coupling,
                channel=ch_in,
                )
	    self.add_parameter(ch_in+'_eres_bits',
	        flags=Instrument.FLAG_GET,
	        type=types.FloatType,
		get_func=self.do_get_eres_bits,
		channel=ch_in,
		)
	    self.add_parameter(ch_in+'_eres_bandwidth',
	        flags=Instrument.FLAG_GET,
		type=types.FloatType,
		get_func=self.do_get_eres_bandwidth,
		channel=ch_in,
		)
        self.add_parameter('tdiv',
            flags=Instrument.FLAG_GET,
            type=types.FloatType,
            units='s')
        self.add_parameter('memsize',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            units='S')
        self.add_parameter('samplerate',
            flags=Instrument.FLAG_GET,
            type=types.IntType,
            units='S/s')
	self.add_parameter('trigger_source',
	    flags=Instrument.FLAG_GET,
	    type=types.StringType,
	    )
	self.add_parameter('trigger_type',
	    flags=Instrument.FLAG_GET,
	    type=types.StringType,
	    )
        
	self.add_function('arm_acquisition')
	self.add_function('get_all')
	self.add_function('stop_acquisition')
        self.get_all()


        # Make Load/Delete Waveform functions for each channel


    # Functions

    def get_all(self):
        logging.debug(__name__ + ' : Get all.')
        for ch_in in self._input_channels:
#            logging.info(__name__ + ' : Get '+ch_in)
            self.get(ch_in+'_vdiv')
#            self.get(ch_in+'_tdiv')
            self.get(ch_in+'_vertical_offset')
            self.get(ch_in+'_trace_on_display')
            self.get(ch_in+'_coupling')
	    self.get(ch_in+'_eres_bits')
	    self.get(ch_in+'_eres_bandwidth')
        self.get('tdiv')
        self.get('memsize')
        self.get('samplerate')
	self.get_trigger_source()
	self.get_trigger_type()
#            self.get_enhanced_resolution(ch_in)

#    def do_get_enhanced_resolution(self, channel):
#        '''
#        Get the number of enhanced resolution bits.
#        Input:
#            Channel name {C1, C2, C3, C4}
#        Output:
#            {0, 0.5, 1, 1.5, 2, 2.5, 3}
#        '''
#        logging.info(__name__ + ' : Get number of ERES bits.')
#        if channel in self._input_channels:
#            value = self._visainstrument.ask('ERES '+channel+'?')
#            return value
#        else:
#            raise ValueError('Channel has to be C1, C2, C3, or C4')

    def do_get_vdiv(self, channel):
        '''
        Get the volts per div.
        '''
        logging.debug(__name__ + ' : Get volts per div %s.' %channel)
        response = self._visainstrument.ask(channel+':VDIV?')
        return float(response.lstrip(channel+':VDIV').rstrip('V'))  

    def do_get_tdiv(self):
        '''
        Get the volts per div.
        '''
        logging.debug(__name__ + ' : Get time per division.')
        response = self._visainstrument.ask('TDIV?')
        return float(response.lstrip('TDIV').rstrip('S'))  
    
    def do_get_memsize(self):
        '''
        Get the memory size.
        '''
        response = self._visainstrument.ask('MSIZ?')
        return int(float(response.lstrip('MSIZ').rstrip('SAMPLE')))

    def do_get_samplerate(self):
        '''
        Get the sample rate.
        '''
        return int(self.get_memsize()/(self.get_tdiv()*10))

    def do_get_voffset(self, channel):
        response = self._visainstrument.ask(channel+':OFFSET?')
        return float(response.lstrip(channel+':OFFSET').rstrip('V'))

    def do_get_trace_on_display(self, channel):
        response = self._visainstrument.ask(channel+':TRACE?')
        if response.lstrip(channel+':TRA ') == 'ON':
            return True
        else:
            return False

    def do_get_coupling(self, channel):
        response = self._visainstrument.ask(channel+':CPL?')
        return response.lstrip(channel+':CPL ')

    def set_trigger_normal(self):
        '''
        Change the trigger mode to Normal.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger to normal')
        self._visainstrument.write('TRMD NORMAL')
      

    def set_trigger_auto(self):
        '''
        Change the trigger mode to Auto.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + ' : Set trigger to auto')
        self._visainstrument.write('TRMD AUTO')
       

    def auto_setup(self):
        '''
        Adjust vertical, timebase and trigger parameters automatically

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Auto setup of vertical, timebase and trigger')
        self._visainstrument.write('ASET')
        
        
    def screen_dump(self, file, type='JPEG', background='BLACK', dir='C:\\', area='FULLSCREEN'):
        '''
        Initiate a screen dump

        Input:
            file(str) : destination filename, auto incremented
            type(str) : image type (PSD, BMP, BMPCOMP, JPEG (default), PNG, TIFF)
            background(str) : background color (BLACK (default), WHITE)
            dir(str) : destination directory (E:\\ is the default shared folder)
            area(str) : hardcopy area (GRIDAREAONLY, DSOWINDOW, FULLSCREEN)

        Output:
            None
        '''
        logging.info(__name__ + ' : Take a screenshot with filename %s, type %s and save on harddisk %s' % (file, type, dir))
        self._visainstrument.write('HCSU DEV, %s, BCKG, %s, DEST, FILE, DIR, %s, FILE, %s, AREA, %s; SCDP' % (type, background, dir, file, area))
        
    def set_timesteps(self, time):
        '''
        Set timesteps used per scale unit to the scope

        Input:
            Timesteps (eg. 1 ms = 1E-6)

        Output:
            none
        '''
        logging.info(__name__ + ' : Acquiring timesteps from instrument')
        self._visainstrument.write('TDIV %s' % time)
        

    def get_timesteps(self):
        '''
        Set timesteps used per scale unit to the scope

        Input:
            None

        Output:
            Timesteps (eg. 1 ms = 1E-6)
        '''
        logging.info(__name__ + ' : Getting timebase from the instrument')
        timebase = self._visainstrument.ask_for_values('TDIV?', format = double )
        return timebase
        

    def get_voltage_scale(self, channel):
        '''
        Gets the voltage scale from the instrument from a specified channel

        Input:
            Channel

        Output:
            Voltage (eg. 1 ms = 1E-6)
        '''
        logging.info(__name__ + ' : Getting timebase from the instrument')
        voltage = self._visainstrument.ask('C%s:VDIV?' % channel)
        #voltage = voltage.remove(channel)
        return voltage
        

    def set_voltage_scale(self, voltage, channel):
        '''
        Set the voltage scale from the instrument from a specified channel

        Input:
            Voltage (eg. 1 ms = 1E-6), Channel

        Output:
            None
        '''
        logging.info(__name__ + ' : Getting timebase from the instrument')
        self._visainstrument.write('C%s:VDIV %s' % (channel, voltage))

    def do_get_eres_bits(self, channel):
	'''
	Get the number of ERES bits for a channel.
	Since I haven't figured out a direct command, we'll just extract it from a measured waveform.
	'''
	old_memsize = self.get_memsize()
	self.set_memsize(500)
	self.arm_acquisition()
        self._visainstrument.write('COMM_FORMAT DEF9,WORD,BIN')
        rawdata = self._visainstrument.ask(channel+':WAVEFORM?')

	self.set_memsize(old_memsize)
        offset = 21
        nominal_bits = struct.unpack('h',rawdata[172+offset:174+offset])
        eres_bits = nominal_bits[0] - 8
	if eres_bits == 8:
	    eres_bits = 0
	return eres_bits

    def do_get_eres_bandwidth(self, channel):
	'''
	Calculate the bandwidth of a channel following the enhanced resolution option.
	'''
	bits = self.do_get_eres_bits(channel)
	Nyquist = self.get_samplerate()/2
	if bits == 0:
	    return Nyquist
	bw_table = {0.5:0.5, 1.0:0.241, 1.5:0.121, 2.0:0.058, 3.0:0.016}
	return bw_table[bits]*Nyquist

    def reset(self):
        '''
        Resets the instrument

        Input:
            None

        Output:
            None
        '''
        logging.info(__name__ + ' : Resetting Instrument')
        self._visainstrument.clear()

    def setup_storage(self, channel='C1', destination='HDD', mode='OFF', filetype='MATLAB'):
        '''
        Sets up the waveform storage

        Input:
            Channel = C1, C2, C3 or C4 (C1 default)
            Destination = M1, M2, M3, M4, or HDD (what memory you want to save it to)
            Mode = Off, Fill or Wrap (Off default)
            Filetype = ASCII, BINARY, EXCEL, MATCAD or MATLAB (MATLAB)

        Output:
            None
        '''
        logging.info(__name__ + ' : Setting up waveform storage')
        self._visainstrument.write('STST %s, %s, AUTO, %s, FORMAT, %s' % (channel, destination, mode, filetype))

    def set_memsize(self, memsize):
        '''
        Starts measuring data, saves the data and sends it to the computer

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 5MA, 10MA, 25MA)
            

        Output:
            None
        '''
        logging.debug(__name__ + ' : Setting memory size')
        self._visainstrument.write('MSIZ %s' % memsize)

    def measure_waveform(self):
        '''
        Starts measuring data, saves the data to the scope

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 5MA, 10MA, 25MA)
            

        Output:
            None
        '''
        logging.debug(__name__ + ' : Measuring waveform')
        #self._visainstrument.write('MSIZ %s' % memsize)
        self._visainstrument.write('ARM')
        self._visainstrument.write('TRMD SINGLE')
        #self._visainstrument.write('STO')

    def store_waveform(self):
        '''
        Starts measuring data, saves the data to the scope

        Input:
            Time to measure, Maximum measurement size (Inputs possible = 50
            0, 1000, 2500, 5000, 10K, 25K, 50K, 100K, 250K, 500K, 1MA, 2.5MA, 5MA, 10MA, 25MA)
            

        Output:
            None
        '''
        logging.info(__name__ + ' : Measuring waveform')
        self._visainstrument.write('STO')

    def get_waveform_memory(self, channel, xdata=True):
        '''
        Reads out the data directly from the memory. By doing this it also changes the format to 'word', which is    a 16-bit read-out, instead of other possible options as 8-bit for example.
        Output:
        Ydata = numpy array with measured values
        Xdata = numpy array with x axis values
        '''
        # Need a check to figure out whether the trace is on the display.

        self._visainstrument.write('COMM_FORMAT DEF9,WORD,BIN')
        rawdata = self._visainstrument.ask(channel+':WAVEFORM?')
        #Channel can be C1, C2, C3 or C4
        data_array_start = 348
        offset = 21
        floating = 4

        Yoffset = struct.unpack('f',rawdata[160+offset:164+offset])

        Ygain = struct.unpack('f',rawdata[156+offset:156+floating+offset])

        Xgain = struct.unpack('f',rawdata[176+offset:176+floating+offset])
        nominal_bits = struct.unpack('h',rawdata[172+offset:174+offset])
        eres_bits = nominal_bits[0] - 8
        logging.debug('Number of enhanced resolution bits of channel %s is %.1f.' %(channel, eres_bits))
        
        
        datapoints = len(rawdata[data_array_start+offset:])/2.0

        if int(datapoints) == datapoints:
            lastnumber = len(rawdata)
        else:
            lastnumber = len(rawdata)-1           
        
        logging.debug('Number of datapoints according to LeCroy %s is %.1f.' %(channel, datapoints))

        data1 = struct.unpack(str(int(datapoints))+'h',rawdata[data_array_start+offset:lastnumber])

        YVperDIV = {'(0,)': 1e-6, '(1,)': 2e-6, '(2,)': 5e-6, '(3,)': 10e-6, '(4,)': 20e-6, '(5,)': 50e-6, '(6,)': 100e-6, '(7,)': 200e-6, '(8,)': 500e-6, '(9,)': 1e-3, '(10,)': 2e-3, '(11,)': 5e-3, '(12,)': 10e-3, '(13,)': 20e-3, '(14,)': 50e-3, '(15,)': 100e-3, '(16,)': 200e-3, '(17,)': 500e-3, '(18,)': 1, '(19,)': 2, '(20,)': 5, '(21,)': 10, '(22,)': 20, '(23,)': 50, '(24,)': 100, '(25,)': 200, '(26,)': 500, '(27,)': 1e3}

        #YVperDIV is given in V/div.

        YVperDIVgain = YVperDIV[str(struct.unpack('h',rawdata[332+offset:334+offset]))]

        XTIMEperDIV = {'(0,)': 1e-12, '(1,)': 2e-12, '(2,)': 5e-12, '(3,)': 10e-12, '(4,)': 20e-12, '(5,)': 50e-12, '(6,)': 100e-12, '(7,)': 200e-12, '(8,)': 500e-12, '(9,)': 1e-9, '(10,)': 2e-9, '(11,)': 5e-9, '(12,)': 10e-9, '(13,)': 20e-9, '(14,)': 50e-9, '(15,)': 100e-9, '(16,)': 200e-9, '(17,)': 500e-9, '(18,)': 1e-6, '(19,)': 2e-6, '(20,)': 5e-6, '(21,)': 10e-6, '(22,)': 20e-6, '(23,)': 50e-6, '(24,)': 100e-6, '(25,)': 200e-6, '(26,)': 500e-6, '(27,)': 1e-3, '(28,)': 2e-3, '(29,)': 5e-3, '(30,)': 10e-3, '(31,)': 20e-3, '(32,)': 50e-3, '(33,)': 100e-3, '(34,)': 200e-3, '(35,)': 500e-3, '(36,)': 1, '(37,)': 2, '(38,)': 5, '(39,)': 10, '(40,)': 20, '(41,)': 50, '(42,)': 100, '(43,)': 200, '(44,)': 500, '(45,)': 1e3, '(46,)': 2e3, '(47,)': 5e3, '(100,)': 0}

        #XTIMEperDIV is given in seconds/div. WATCH OUT: EXTERNAL timing per div is not implemented in the program. The output on the X-axis will be equal to zero when external is chosen!

        XTIMEperDIVgain = XTIMEperDIV[str(struct.unpack('h',rawdata[324+offset:326+offset]))]

        Ydata = Ygain[0]*np.array(data1)-Yoffset

        Xdata = Xgain[0]*np.linspace(0,datapoints-1,datapoints, endpoint=True)

        if xdata: 
            return Xdata, Ydata
        else:
            return Ydata

    def do_get_trigger_source(self):
	'''
	Get the source for the trigger.
	'''
	logging.debug(__name__ + ' Getting the source for the trigger.')
        response = self._visainstrument.ask('TRSE?') # TRig_Select
	if response.startswith('TRSE'):
	    return response.lstrip('TRSE').split(',')[2]
        else:
	    raise Warning('Unexpected response to TRSE?: %s' % response)

    def do_get_trigger_type(self):
	'''
	Get the type for the trigger.
	'''
	logging.debug(__name__ + ' Getting the type for the trigger.')
        response = self._visainstrument.ask('TRSE?') # TRig_Select
	if response.startswith('TRSE'):
	    return response.lstrip('TRSE').split(',')[0]
        else:
	    raise Warning('Unexpected response to TRSE?: %s' % response)

    def arm_acquisition(self):
	'''
	Send the ARM_ACQUISITION command. This armes the scope and forces a single acquisition.
	'''
        self._visainstrument.write('ARM_ACQUISITION')

    def stop_acquisition(self):
	'''
	Stop the acquisition.
	'''
	self._visainstrument.write('STOP')

# Next thing doesn't work yet, because in the transfer to the instrument visa throws away the \' needed to specify what file to get... Do not know how to solve this...
# Also, remember that you need qt lab to wait until we are sure that the entire waveform for the specified time is 
##    def receive_file(self, destination_filename, channel='1', filetype='MATLAB'):
##        '''
##        Receives the measured data from the scope, saves the file, then deletes the file from the scope
##
##        Input:
##            Filename (is generic, so should not be such a problem)
##            Channel from which measurement was just taken
##            filetype which was specified in setup_storage (in capitals!)
##            The name of the file to which is should be saved
##
##        Output:
##            The measurement in a prespecified filetype
##        '''
##        logging.info(__name__ + ' : Receiving & Deleting data from scope')
##        if filetype == 'MATLAB':
##            extension = '.dat'
##        elif filetype == 'ASCII':
##            extension = '.txt'
##        elif filetype == 'BINARY':
##            extension = '.trc'
##        elif filetype == 'EXCEL':
##            extension = '.csv'
##        elif filetype == 'MATCAD':
##            extension = '.prn'
##        
##        FILE = destination_filename+extension
##        filepath = 'D:\\xtalk\\C%sxtalk_chndir200000' %channel
##        filepath = filepath+extension
##        print 'TRFL DISK, HDD, FILE,  \' %s \' ' % filepath
##        data = self._visainstrument.ask('TRFL DISK, HDD, FILE,\'%s\'' % filepath)
##        FILE.write(data)
##        FILE.close()
##        self._visainstrument.write('DELF, DISK, HDD, FILE,\'%s\'' %filepath)
        