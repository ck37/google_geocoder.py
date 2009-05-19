#!/usr/bin/python
# By Chris Kennedy, ck@ck37.com.
# geopy is a contrib module available at http://code.google.com/p/geopy/
# demjson is at http://deron.meranda.us/python/demjson/ (easy_install demjson)

import sys, time, datetime
from geopy import geocoders
import urllib, demjson, os.path
g = geocoders.Google(resource="maps")

input_file = 'your_input_file'

# List of fields from the input file to include in the geocoded output file.
target_fields = ["first_name", "middle_name", "last_name", "home_address1", "home_apt", "home_city", "home_state", "home_zip"]

# Field names to use for constructing the full address for Google.
address_field_name = "home_address1"
city_field_name = "home_city"
state_field_name = "home_state"
zip_field_name = "home_zip"

# Display current status every X lines.
display_status_interval = 100

# Misc settings.
output_file_name_suffix = "-geocoded"
file_extension = '.txt'
max_consecutive_fails = 5
sleep_time = 0.1
hide_output_stream = "/dev/null"
field_separator = "\t"
line_terminator = "\n"

input = open(input_file + file_extension, 'r')
print "Opened", input_file + file_extension, "for input."

output_file = input_file + output_file_name_suffix + file_extension

new_file = os.path.isfile(output_file) == 0

if new_file == 0:
  # We have tried to geocode this file before so pickup where we left off.
  old_file = open(output_file, "r")
  existing_lines = 0
  for line in old_file:
    existing_lines += 1
  old_file.close()
  print "Found", existing_lines, "existing lines."
    
output = open(output_file, 'a')

header = input.readline().strip()
new_geocode_fields = ["geocoded", "clean_address", "lat", "lng"]
output_fields = target_fields[:]
output_fields.extend(new_geocode_fields);

header_line = field_separator.join(output_fields) + line_terminator
if new_file:
  output.write(header_line)
header_fields = header.split(field_separator)
target_indices = []
code_counts = {}
index_list = {}

for key in target_fields:
  if key in header_fields:
    target_indices.append(header_fields.index(key)) 
    index_list[key] = header_fields.index(key)
  else:
    print "Error: could not locate key \"" + key + "\" in header fields."
input_count = 0
output_count = 0
row = 0

hide_output = open(hide_output_stream, "w")
show_output = sys.stdout

good = 0
bad = 0

consecutive_fails = 0
for line in input:
  input_count += 1
  if new_file == 0 and input_count < existing_lines:
    # Skip this line until we get to a new line.
    continue
  fields = [f.replace("\r", "").replace("\n", "") for f in line.split(field_separator)]
  data_fields = [fields[index] for index in target_indices]

  address1 = data_fields[target_fields.index(address_field_name)]
  city = data_fields[target_fields.index(city_field_name)]
  state = data_fields[target_fields.index(state_field_name)]
  zip = data_fields[target_fields.index(zip_field_name)]

  raw_address = address1 + ", " + city + ", " + state + " " + zip
  clean_address = ''
  lat = 0.0
  lng = 0.0
  try:
    sys.stdout = hide_output
    clean_address, (lat, lng) = g.geocode(raw_address)
    geocoded = 1
    consecutive_fails = 0
    good += 1
    sys.stdout = show_output
  except ValueError:
    bad += 1
    consecutive_fails += 1
    sys.stdout = show_output
    # Failed to geocode address.
    # print "Bad %d: %s" % (input_count, raw_address)
    geocoded = 0

  # Wait a bit so we don't overload the Google Maps API.
  time.sleep(sleep_time)

  if consecutive_fails > max_consecutive_fails:
    print "FAIL:", consecutive_fails, "fails in a row; stopping on line", str(input_count) + "."
    input.close()
    output.close()
    sys.exit()

  try: 
    # TODO: need to fix this quick unicode hack.
    extra_data = [str(geocoded), clean_address.replace(u'\xe9', 'e'), str(lat), str(lng)]
  except UnicodeEncodeError:
    extra_data = ["0", "", "0", "0"]
    
  data_fields.extend(extra_data)
  try: 
    output_line = field_separator.join(data_fields) + line_terminator
    output.write(output_line)
    output_count += 1
  except UnicodeDecodeError:
    # TODO: need to fix this quick unicode hack.
    print "Weird Unicode error! Record:", str(input_count), ", Address:", raw_address + "."
  except UnicodeEncodeError:
    # TODO: need to fix this quick unicode hack.
    print "Weird Unicode error! Record:", str(input_count) + ", Address:", raw_address + "."

  if input_count % display_status_interval == 0:
    print "Count:", str(input_count) + ", Good:", str(good) + ", Bad:", str(bad) + "."

  row += 1

print "Final input:", str(input_count) + ", Final output:", output_count + "."
print "Good:", str(good) + ", Bad:", str(bad) + "."
input.close()
output.close()
