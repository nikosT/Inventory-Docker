"""
ORFEUS Data Center WSGI Response Plot API

Returns ObsPy plot of response for network, station. The 
location and channel codes are optional.

API Usage: /network/station/(location)/(channel)

Authors:
Vincent van Heiden (heiden@knmi.nl)
Mathijs Koymans (koymans@knmi.nl)

Copyright: ORFEUS Data Center, 2017
last modified: 2017-07-04
"""

import io
import json

import matplotlib; matplotlib.use('Agg')
#from matplotlib.backends.backend_agg import FigureCanvas
import numpy as np

from obspy import read, read_inventory, UTCDateTime
from bottle import run, response, hook, route, request, default_app, HTTPResponse, static_file
#np.set_printoptions(threshold='nan')

import sys

with open("./config.json") as configuration:
  CONFIG = json.load(configuration)

CONTENT_HEADERS = {
  "Access-Control-Allow-Origin": "*",
  "Content-Type": "image/png"
}

# Add hook before request to strip trailing slashes
@hook("before_request")
def strip_path():
  request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip("/")


@route('/test/<filename>')
def server_static(filename):
    return static_file(filename, root="/Users/vincentvanderheiden/Programming/Python/bottle_new")

@route("/")
def send_nothing():

    return HTTPResponse(status=204)


"""
Response routes
"""

@route("/response/<network>")
def send_nothing(network):

    return HTTPResponse(status=204)

@route("/response/<network>/<station>")
def display_station(network, station):

    return show_inventory(create_query_array("response", network, station, None, None))

@route("/response/<network>/<station>/<location>")
def display_location(network, station, location):

    return show_inventory(create_query_array("response", network, station, location, None))

# Define routes to up to a station level
@route("/response/<network>/<station>/<location>/<channel>")
def display_location(network, station, location, channel):

    return show_inventory(create_query_array("response", network, station, location, channel))

"""
Waveform routes
"""

@route("/waveform/<network>")
def send_nothing(network):

    return HTTPResponse(status=400)

@route("/waveform/<network>/<station>")
def display_station(network, station):

    return HTTPResponse(status=400)


@route("/waveform/<network>/<station>/<location>")
def send_nothing(network, station, location):

  return HTTPResponse(status=400)

# Define routes to up to a station level
@route("/waveform/<network>/<station>/<location>/<channel>")
def display_location(network, station, location, channel):

    return show_waveform(create_query_array("waveform", network, station, location, channel))


def create_query_array(which, network, station, location, channel):
  """
  Create an array from the passed parameters
  and skip values that are None
  """

  if not network.isalnum():
    return HTTPResponse("Network code must be alphanumerical", status=400)

  if not station.isalnum():
    return HTTPResponse("Station code must be alphanumerical", status=400)

  query_array = []

  if which == "response":
    query_array.append("level=response")
  if network is not None:
    query_array.append("network=%s" % network)
  if station is not None:
    query_array.append("station=%s" % station)
  if location is not None:
    query_array.append("location=%s" % location)
  if channel is not None:
    query_array.append("channel=%s" % channel)

  return query_array

def show_waveform(query_array):
    """
    Call FDSNWS-Station for the stream and read using
    ObsPy. Save the frame in memory and forward to user
    """
    # Propagate error HTTPResponse
    if isinstance(query_array, HTTPResponse):
      return query_array

    #request.query.start="2019-01-01"
    #request.query.end="2019-01-02"

    # Limit requested data to a timespan of one day
    if (UTCDateTime(request.query.end).timestamp - UTCDateTime(request.query.start).timestamp) > 86400:
      return HTTPResponse(status=413)

    # Go over all supported keys
    for key in ["start", "end"]:

        value = getattr(request.query, key)
        if value == "" :
            return HTTPResponse("%s is required" % key, status=400)

        query_array.append(key + "=" + value)
    
    # Try getting the stream
    # If the request fails send a 204 NO CONTENT reply
    try:
      stream = read(CONFIG["FDSN_DATASELECT_URL"] + "?" + "&".join(query_array))
      
      # apply instrument deconvolution
      deconvolution(stream, query_array)

      trace_counter = 0

      waveform_trace  = {
          "name": stream[0].stats.network + '.' + stream[0].stats.station  + '.' + stream[0].stats.location + '.' + stream[0].stats.channel,
          "data": [],
      }
      for trace in stream:
        trace_counter = trace_counter + 1
        dt = trace.stats.delta*1e3 # timesteps in milliseconds
        t = trace.stats.starttime.timestamp*1000 # starttime in milliseconds

        n = -1
        waveform_trace_data = []
        waveform = []
        time_array = []

        # create waveform data and associated timestamp, and push to array
        k = None
        limit = dt
        for value in trace.data:
          n = n + 1
          t = t + dt
          value = np.asscalar(value)
          time_array.append(t)
          waveform.append(value)

        # downsample to 1 sample per second
        waveform = waveform[1::int(trace.stats.sampling_rate)]
        time_array = time_array[1::int(trace.stats.sampling_rate)]

        for t,value in zip(time_array, waveform):
          waveform_trace_data = [t,value]
          waveform_trace["data"].append(waveform_trace_data)
        if trace_counter > 0:
          null = [t, None]
          waveform_trace["data"].append(null)
    except Exception as e:
      print e
      return HTTPResponse(status=204)

    # Filter stream
    minfr = request.query.freqmin
    maxfr = request.query.freqmax
    try:
        if minfr != "" and maxfr != "":
            stream = stream.filter("bandpass", freqmin=float(minfr), freqmax=float(maxfr))
        if minfr != "":
            stream = stream.filter("highpass", freq=float(minfr))
        if maxfr != "":
            stream = stream.filter("lowpass", freq=float(maxfr))
    except Exception as e:
        return HTTPResponse(str(e), status=400)

    if request.query.units == "rawdata":
      abbrev=""
    elif request.query.units == "displacement":
      abbrev=" [m]"
    elif request.query.units == "acceleration":
      abbrev=" [m/s2]"
    else:   
      abbrev=" [m/s]"

    return HTTPResponse(
      {"payload": [waveform_trace],
       "unit": [request.query.units.title() + abbrev],},
      headers=CONTENT_HEADERS,
      status=200
    )

def deconvolution(stream, query_array):
    # Read inventory used for deconvolution
    if request.query.units != "rawdata":
        try:
            inv = read_inventory(CONFIG["FDSN_STATION_URL"] + "?" + "&".join(query_array)+ "&level=response")
        except Exception:
            return HTTPResponse(status=204)
        
        if request.query.units == "displacement":
            outp="DISP"
        elif request.query.units == "acceleration":
            outp="ACC"
        else:
            outp="VEL"

        # Instrument response deconvolution
        for trace in stream:
            trace.remove_response(
              inventory=inv, 
              output=outp
            )

def show_inventory(query_array):

    """
    Call FDSNWS-Station for the inventory and read using
    ObsPy. Save the frame in memory and forward to user
    """

    # Propogate error HTTPResponse
    if isinstance(query_array, HTTPResponse):
      return query_array

    # Go over all supported keys
    for key in ["start", "end"]:

        value = getattr(request.query, key)

        if value != "":
            query_array.append(key + "=" + value)

    # Set the requested units
    if request.query.units == "acceleration":
      units = "ACC"
    elif request.query.units == "displacement":
      units = "DISP"
    else:
      units = "VEL"
    
    # Try getting the inventory
    # If the request fails send a 204 NO CONTENT reply
    try:
      min_freq = 0.001
      inventory = read_inventory(CONFIG["FDSN_STATION_URL"] + "?" + "&".join(query_array))
      # request response data from server
      station = inventory[0][0]
      
      response_data = [] 
      
      # loop through channels, determine sampling frequncies and nyquist value 
      for cha in station.channels:
        for stage in cha.response.response_stages[::-1]:
          if (stage.decimation_input_sample_rate is not None and stage.decimation_factor is not None):
            sampling_rate = (stage.decimation_input_sample_rate /stage.decimation_factor)
            break
        t_samp = 1.0 / sampling_rate
        nyquist = sampling_rate / 2.0 
        nfft = sampling_rate / min_freq
        response, freq = cha.response.get_evalresp_response(t_samp=t_samp, nfft=nfft, output=units)
     
        
        # skip zero value and space data point even in log10space 
        freq_new = []
        response_new = []
        n = None
        limit = 0.01
        for x, y in zip(freq, response):
          if x > 0:
            if n is None:
              freq_new.append(x)
              response_new.append(y)
              n = np.log10(x)
         
            if (np.log10(x) - n) > limit:
              freq_new.append(x)
              response_new.append(y)
              n = np.log10(x)
       
        # create amplitude array
        amplitude = list(np.abs(response_new))
        amplitude_x_y = [] 
        channel_amplitude  = {
          "name": inventory.networks[0].code + '.' + station.code  + '.' + cha.location_code + '.' + cha.code,
          "data": [],
          "typo": "amplitude",
          "nyquist": nyquist,
        }
        for x,y in zip(freq_new, amplitude):
          if x > nyquist:
            break
          amplitude_x_y = [x,y]
          channel_amplitude["data"].append(amplitude_x_y)
        response_data.append(channel_amplitude)
        
        # create phase array
        phase = list(np.angle(response_new))
        phase_x_y = []
        channel_phase  = {
          "name": inventory.networks[0].code + '.' + station.code  + '.' + cha.location_code + '.' + cha.code,
          "data": [],
          "typo": "phase",
          "nyquist": nyquist,
        }
        for x,y in zip(freq_new, phase):
          if x > nyquist:
            break
          phase_x_y = [x,y]
          channel_phase["data"].append(phase_x_y)
        response_data.append(channel_phase)

    except Exception as e:
      print e
      return HTTPResponse(status=204)

    return HTTPResponse(
      {"payload": response_data},
      headers=CONTENT_HEADERS,
      status=200
    )

# Run default Bottle application used with WSGI
run( host='0.0.0.0', port=8080, debug=True)
