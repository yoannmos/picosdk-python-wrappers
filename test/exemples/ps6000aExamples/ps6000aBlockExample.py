#
# Copyright (C) 2020 Pico Technology Ltd. See LICENSE file for terms.
#
# PS6000 A BLOCK MODE EXAMPLE
# This example opens a 6000a driver device, sets up two channels and a trigger then collects a block of data.
# This data is then plotted as mV against time in ns.

import ctypes
import numpy as np
from picosdk.ps6000a import ps6000a as ps
from picosdk.PicoDeviceEnums import picoEnum as enums
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

# Create chandle and status ready for use
chandle = ctypes.c_int16()
status = {}

# Open 6000 A series PicoScope
# returns handle to chandle for use in future API functions
resolution = enums.PICO_DEVICE_RESOLUTION["PICO_DR_8BIT"]
status["openunit"] = ps.ps6000aOpenUnit(ctypes.byref(chandle), None, resolution)
assert_pico_ok(status["openunit"])

# Set channel A on
# handle = chandle
channelA = enums.PICO_CHANNEL["PICO_CHANNEL_A"]
coupling = enums.PICO_COUPLING["PICO_DC"]
channelRange = 7
# analogueOffset = 0 V
bandwidth = enums.PICO_BANDWIDTH_LIMITER["PICO_BW_FULL"]
status["setChannelA"] = ps.ps6000aSetChannelOn(chandle, channelA, coupling, channelRange, 0, bandwidth)
assert_pico_ok(status["setChannelA"])

# set channel B-H off
for x in range (1, 7, 1):
    channel = x
    status["setChannel",x] = ps.ps6000aSetChannelOff(chandle,channel)
    assert_pico_ok(status["setChannel",x])

# Set simple trigger on channel A, 1 V rising with 1 s autotrigger
# handle = chandle
# enable = 1
source = channelA
# threshold = 1000 mV
direction = enums.PICO_THRESHOLD_DIRECTION["PICO_RISING"]
# delay = 0 s
# autoTriggerMicroSeconds = 1000000 us
status["setSimpleTrigger"] = ps.ps6000aSetSimpleTrigger(chandle, 1, source, 1000, direction, 0, 1000000)
assert_pico_ok(status["setSimpleTrigger"])

# Get fastest available timebase
# handle = chandle
enabledChannelFlags = enums.PICO_CHANNEL_FLAGS["PICO_CHANNEL_A_FLAGS"]
timebase = ctypes.c_uint32(0)
timeInterval = ctypes.c_double(0)
# resolution = resolution
status["getMinimumTimebaseStateless"] = ps.ps6000aGetMinimumTimebaseStateless(chandle, enabledChannelFlags, ctypes.byref(timebase), ctypes.byref(timeInterval), resolution)
print("timebase = ", timebase.value)
print("sample interval =", timeInterval.value, "s")

# Set number of samples to be collected
noOfPreTriggerSamples = 500000
noOfPostTriggerSamples = 1000000
nSamples = noOfPostTriggerSamples + noOfPreTriggerSamples

# Create buffers
bufferAMax = (ctypes.c_int16 * nSamples)()
bufferAMin = (ctypes.c_int16 * nSamples)() # used for downsampling which isn't in the scope of this example

# Set data buffers
# handle = chandle
# channel = channelA
# bufferMax = bufferAMax
# bufferMin = bufferAMin
# nSamples = nSamples
dataType = enums.PICO_DATA_TYPE["PICO_INT16_T"]
waveform = 0
downSampleMode = enums.PICO_RATIO_MODE["PICO_RATIO_MODE_RAW"]
clear = enums.PICO_ACTION["PICO_CLEAR_ALL"]
add = enums.PICO_ACTION["PICO_ADD"]
action = clear|add # PICO_ACTION["PICO_CLEAR_WAVEFORM_CLEAR_ALL"] | PICO_ACTION["PICO_ADD"]  
status["setDataBuffers"] = ps.ps6000aSetDataBuffers(chandle, channelA, ctypes.byref(bufferAMax), ctypes.byref(bufferAMin), nSamples, dataType, waveform, downSampleMode, action)
assert_pico_ok(status["setDataBuffers"])

# Run block capture
# handle = chandle
# timebase = timebase
timeIndisposedMs = ctypes.c_double(0)
# segmentIndex = 0
# lpReady = None   Using IsReady rather than a callback
# pParameter = None
status["runBlock"] = ps.ps6000aRunBlock(chandle, noOfPreTriggerSamples, noOfPostTriggerSamples, timebase, ctypes.byref(timeIndisposedMs), 0, None, None)
assert_pico_ok(status["runBlock"])

# Check for data collection to finish using ps6000aIsReady
ready = ctypes.c_int16(0)
check = ctypes.c_int16(0)
while ready.value == check.value:
    status["isReady"] = ps.ps6000aIsReady(chandle, ctypes.byref(ready))
    
# Get data from scope
# handle = chandle
# startIndex = 0
noOfSamples = ctypes.c_uint64(nSamples)
# downSampleRatio = 1
# segmentIndex = 0
overflow = ctypes.c_int16(0)
status["getValues"] = ps.ps6000aGetValues(chandle, 0, ctypes.byref(noOfSamples), 1, downSampleMode, 0, ctypes.byref(overflow))
assert_pico_ok(status["getValues"])

# get max ADC value
# handle = chandle
minADC = ctypes.c_int16()
maxADC = ctypes.c_int16()
status["getAdcLimits"] = ps.ps6000aGetAdcLimits(chandle, resolution, ctypes.byref(minADC), ctypes.byref(maxADC))
assert_pico_ok(status["getAdcLimits"])

# convert ADC counts data to mV
adc2mVChAMax =  adc2mV(bufferAMax, channelRange, maxADC)

# Create time data
time = np.linspace(0, (nSamples -1) * timeInterval.value * 1000000000, nSamples)

# plot data from channel A and B
plt.plot(time, adc2mVChAMax[:])
plt.xlabel('Time (ns)')
plt.ylabel('Voltage (mV)')
plt.show()

# Close the scope
status["closeunit"] = ps.ps6000aCloseUnit(chandle)
assert_pico_ok(status["closeunit"])

print(status)