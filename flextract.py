import math

from pykml.factory import KML_ElementMaker as KML

from lxml import etree
import utm
from os import path

kml_file = 'Palms vux1lr 120-60m_3Dpath.kml'

coordinates = []

# extract all coordinates from the kml
with open(kml_file) as f:
    root = etree.parse(f).getroot()

    for elem in root.getiterator():
        if 'LineString' in elem.tag:
            for child in elem.getiterator():
                if 'coordinates' in child.tag:
                    coordinates += child.text.split(' ')

# convert coordinates from lat lon to utm
utm_coordinates = []

for coord in coordinates:
    parts = coord.split(',')
    utm_coordinates += [utm.from_latlon(float(parts[1]), float(parts[0]))]


# now find flight lines

def get_len(utm_a, utm_b):
    return math.sqrt(math.pow(utm_b[0] - utm_a[0], 2) + math.pow(utm_b[1] - utm_a[1], 2))


def get_bearing(utm_a, utm_b):
    return math.atan2(utm_b[0] - utm_a[0], utm_b[1] - utm_a[1])


# radians per meter
angle_threshold_rad_per_meter = math.radians(1.0)  # degrees to radians
length_threshold_meters = 20

flight_lines = []
current_fl = []
current_fl_length = 0

for i in range(0, len(utm_coordinates)):
    if i + 2 >= len(utm_coordinates):
        break
    point_a = utm_coordinates[i + 0]
    point_b = utm_coordinates[i + 1]
    point_c = utm_coordinates[i + 2]

    length_ab = get_len(point_a, point_b)
    length_bc = get_len(point_b, point_c)

    bearing_ab = get_bearing(point_a, point_b)
    bearing_bc = get_bearing(point_b, point_c)

    bearing_delta = math.fabs(math.fabs(bearing_ab) - math.fabs(bearing_bc))

    radians_per_meter = bearing_delta / length_bc

    if radians_per_meter > angle_threshold_rad_per_meter:
        current_fl += [i + 0]
        current_fl += [i + 1]
        current_fl_length += length_ab

        if current_fl_length > length_threshold_meters:
            flight_lines += [current_fl[:]]

        current_fl = []
        current_fl_length = 0
    else:
        # not a severe angle
        current_fl += [i + 0]
        current_fl_length += length_ab


print(len(flight_lines))
for fl in flight_lines:
    print(fl)


# create output kml
folder_fl = KML.Folder(KML.name('extracted flightlines'))
for i in range(len(flight_lines)):
    ls = ''
    for coord_index in flight_lines[i]:
        ls += coordinates[coord_index] + ' '

    pm = KML.Placemark(KML.name('%d' % (i+1)), KML.LineString(KML.altitudeMode('absolute'), KML.coordinates(ls)))
    folder_fl.append(pm)

output_kml = KML.kml(folder_fl)
print(etree.tostring(output_kml, pretty_print=True))

with open('out.kml', 'wb') as f:
    f.write(etree.tostring(output_kml, pretty_print=True))
