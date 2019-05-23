from math import sin, cos, exp, pi		
import render


y = lambda x,z: cos(x) + sin(z)		# define "functional" cost function
y_str = '-y + cos(x) + sin(z)'		# define graphable function in form of f(x,y,z) = 0
color = [.5,.5,.5]					# color of the rendered surface

fps = 60					# output video fps
seconds = 4					# output video length
videoformat = "webm"		# format: avi, webm, gif, mp4, ... etc



	# generate example "point structure"
	# this will be snapshots taken from your algorithm
	# as well as the final result
	# some manipulation may be needed to put into the form of 
	#	[	keyframes,
	#		keyframes,
	#		...			]
	# with keyframes being a list of point coordinates:
	#	[ [x1, y1, z1], [x2, y2, z2], ..., [xn, yn, zn]	]

points = []
tframes = fps*seconds		# total frames: fps * animation length

for pt in range(10):		# generate 10 points
	frames = []				# initialize frame data for this point
	for frame in range(int(fps*seconds)):	# generate point data for this frame

		position = [	(frame / tframes) * 10*cos(2*pi*pt/10),
						0,
						(frame / tframes) * 10*sin(2*pi*pt/10)]	# give it a known x & z value
		position[1] = y(position[0], position[2])				# calculate its y value

		frames.append(position)				# add it to the list of frames

	points.append(frames)				# add the animation for one point to the list of all points

							# render the video with all points, on the given surface with a color
							# at a given fps, in the given format:
render.render(points, y_str, color, fps, videoformat)

